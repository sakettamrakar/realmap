#!/usr/bin/env python3
"""
Data Quality Audit Script
=========================
Executes comprehensive data quality and model sanity checks on N=100 sample projects.

Tasks:
1. Select 100 recent diverse projects by district/status
2. Compute null percentages per required field, data type mismatches, normalization issues
3. Run AI microservice scoring on all projects
4. Generate: data_quality_report.json, model_sanity.csv, data_model_audit.md

Usage:
    python scripts/data_quality_audit.py --sample-size 100 --null-threshold 0.2 --confidence-threshold 0.4
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import func, text, select
from sqlalchemy.orm import Session

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cg_rera_extractor.db import get_engine, get_session_local, Project, ProjectScores
from ai.features.builder import build_feature_pack
from ai.scoring.logic import score_project_quality

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Required fields for a complete project record
REQUIRED_FIELDS = {
    "core": [
        "state_code",
        "rera_registration_number",
        "project_name",
        "status",
        "district",
    ],
    "location": [
        "tehsil",
        "village_or_locality",
        "full_address",
        "latitude",
        "longitude",
    ],
    "dates": [
        "approved_date",
        "proposed_end_date",
    ],
    "quality": [
        "geocoding_status",
        "geo_precision",
    ],
}

# Fields that should have specific data types
TYPE_VALIDATIONS = {
    "latitude": {"type": "numeric", "min": -90, "max": 90},
    "longitude": {"type": "numeric", "min": -180, "max": 180},
    "status": {"type": "enum", "values": ["Ongoing", "Completed", "Lapsed", "Revoked", "New", "Under Review"]},
    "approved_date": {"type": "date"},
    "proposed_end_date": {"type": "date"},
    "data_quality_score": {"type": "int", "min": 0, "max": 100},
}

# Normalization patterns (expected formats)
NORMALIZATION_RULES = {
    "district": {"should_be": "Title Case", "pattern": r"^[A-Z][a-z]+(\s[A-Z][a-z]+)*$"},
    "state_code": {"should_be": "Uppercase 2-char", "pattern": r"^[A-Z]{2}$"},
    "pincode": {"should_be": "6 digits", "pattern": r"^\d{6}$"},
}


# ============================================================================
# DATA SAMPLING
# ============================================================================

def sample_diverse_projects(session: Session, n: int = 100) -> list[Project]:
    """
    Select N recent projects with diversity across districts and statuses.
    Uses stratified sampling to ensure representation.
    """
    logger.info(f"Sampling {n} diverse projects...")
    
    # Get distribution of districts and statuses
    district_counts = session.execute(
        select(Project.district, func.count(Project.id))
        .group_by(Project.district)
        .order_by(func.count(Project.id).desc())
    ).all()
    
    status_counts = session.execute(
        select(Project.status, func.count(Project.id))
        .group_by(Project.status)
        .order_by(func.count(Project.id).desc())
    ).all()
    
    logger.info(f"Found {len(district_counts)} districts, {len(status_counts)} statuses")
    
    # Calculate proportional samples per district (at least 1 per district)
    total_projects = sum(count for _, count in district_counts)
    samples_per_district = {}
    remaining = n
    
    for district, count in district_counts:
        if remaining <= 0:
            break
        # Proportional allocation with minimum of 1
        allocation = max(1, int((count / total_projects) * n))
        allocation = min(allocation, remaining, count)
        samples_per_district[district] = allocation
        remaining -= allocation
    
    # Fetch projects per district with diverse status
    projects = []
    for district, target_count in samples_per_district.items():
        district_projects = session.execute(
            select(Project)
            .where(Project.district == district)
            .order_by(Project.approved_date.desc().nullslast(), Project.id.desc())
            .limit(target_count)
        ).scalars().all()
        projects.extend(district_projects)
    
    # If we don't have enough, fill with recent projects
    if len(projects) < n:
        existing_ids = {p.id for p in projects}
        additional = session.execute(
            select(Project)
            .where(~Project.id.in_(existing_ids))
            .order_by(Project.id.desc())
            .limit(n - len(projects))
        ).scalars().all()
        projects.extend(additional)
    
    logger.info(f"Sampled {len(projects)} projects")
    return projects[:n]


# ============================================================================
# DATA QUALITY ANALYSIS
# ============================================================================

def analyze_null_percentages(projects: list[Project]) -> dict[str, dict[str, float]]:
    """Compute null percentage per required field category."""
    results = {}
    n = len(projects)
    
    for category, fields in REQUIRED_FIELDS.items():
        category_results = {}
        for field in fields:
            null_count = sum(1 for p in projects if getattr(p, field, None) is None)
            category_results[field] = round(null_count / n * 100, 2) if n > 0 else 0
        results[category] = category_results
    
    return results


def analyze_type_mismatches(projects: list[Project]) -> dict[str, list[dict]]:
    """Check for data type mismatches and out-of-range values."""
    mismatches = defaultdict(list)
    
    for p in projects:
        # Latitude validation
        if p.latitude is not None:
            lat = float(p.latitude) if isinstance(p.latitude, Decimal) else p.latitude
            if not (-90 <= lat <= 90):
                mismatches["latitude"].append({
                    "project_id": p.id,
                    "value": str(lat),
                    "issue": "out_of_range"
                })
        
        # Longitude validation
        if p.longitude is not None:
            lon = float(p.longitude) if isinstance(p.longitude, Decimal) else p.longitude
            if not (-180 <= lon <= 180):
                mismatches["longitude"].append({
                    "project_id": p.id,
                    "value": str(lon),
                    "issue": "out_of_range"
                })
        
        # Status validation
        if p.status and p.status not in TYPE_VALIDATIONS["status"]["values"]:
            # Check for similar values (case insensitive)
            if p.status.title() not in TYPE_VALIDATIONS["status"]["values"]:
                mismatches["status"].append({
                    "project_id": p.id,
                    "value": p.status,
                    "issue": "invalid_enum"
                })
        
        # Date validation (ensure dates are not in the past for proposed_end_date of ongoing projects)
        if p.status and "ongoing" in p.status.lower() and p.proposed_end_date:
            if p.proposed_end_date < datetime.now().date():
                mismatches["proposed_end_date"].append({
                    "project_id": p.id,
                    "value": str(p.proposed_end_date),
                    "issue": "ongoing_project_past_due"
                })
    
    return dict(mismatches)


def analyze_normalization_issues(projects: list[Project]) -> dict[str, list[dict]]:
    """Check for normalization issues in text fields."""
    import re
    issues = defaultdict(list)
    
    for p in projects:
        # District normalization (should be Title Case)
        if p.district:
            if p.district != p.district.title():
                issues["district_case"].append({
                    "project_id": p.id,
                    "value": p.district,
                    "expected": p.district.title()
                })
        
        # State code (should be uppercase)
        if p.state_code:
            if p.state_code != p.state_code.upper():
                issues["state_code_case"].append({
                    "project_id": p.id,
                    "value": p.state_code,
                    "expected": p.state_code.upper()
                })
            if len(p.state_code) != 2:
                issues["state_code_length"].append({
                    "project_id": p.id,
                    "value": p.state_code,
                    "issue": f"length={len(p.state_code)}, expected=2"
                })
        
        # Pincode validation (6 digits)
        if p.pincode:
            if not re.match(r"^\d{6}$", p.pincode.strip()):
                issues["pincode_format"].append({
                    "project_id": p.id,
                    "value": p.pincode,
                    "issue": "invalid_format"
                })
        
        # Address completeness
        if p.full_address and len(p.full_address.strip()) < 10:
            issues["address_too_short"].append({
                "project_id": p.id,
                "value": p.full_address,
                "issue": "suspiciously_short"
            })
    
    return dict(issues)


# ============================================================================
# AI MODEL EXECUTION
# ============================================================================

def run_ai_scoring(projects: list[Project], session: Session) -> list[dict[str, Any]]:
    """
    Run AI scoring on all sampled projects and capture outputs.
    Returns list of dicts with project inputs and model outputs.
    """
    results = []
    
    logger.info(f"Running AI scoring on {len(projects)} projects...")
    
    for i, project in enumerate(projects):
        if (i + 1) % 10 == 0:
            logger.info(f"  Processing {i + 1}/{len(projects)}...")
        
        try:
            # Build feature pack
            feature_pack = build_feature_pack(project.id, session)
            
            if feature_pack is None:
                results.append({
                    "project_id": project.id,
                    "project_name": project.project_name,
                    "district": project.district,
                    "status": project.status,
                    "score_value": None,
                    "confidence": None,
                    "explanation": "Feature pack build failed - project not found",
                    "tokens_used": 0,
                    "model_name": "N/A",
                    "model_version": "N/A",
                    "error": "feature_pack_failed"
                })
                continue
            
            # Run scoring
            score_result = score_project_quality(feature_pack.features)
            
            results.append({
                "project_id": project.id,
                "project_name": project.project_name,
                "district": project.district,
                "status": project.status,
                "lat": float(project.latitude) if project.latitude else None,
                "lon": float(project.longitude) if project.longitude else None,
                "has_amenities": len(feature_pack.features.get("amenities", {}).get("onsite", [])) > 0,
                "has_promoters": len(feature_pack.features.get("promoters", [])) > 0,
                "score_value": score_result.get("score", 0),
                "confidence": score_result.get("confidence", 0),
                "explanation": score_result.get("explanation", ""),
                "risks": score_result.get("risks", []),
                "strengths": score_result.get("strengths", []),
                "tokens_used": score_result.get("metadata", {}).get("tokens_used", 0),
                "model_name": "llama-cpp",
                "model_version": "1.0",
                "error": score_result.get("metadata", {}).get("error")
            })
            
        except Exception as e:
            logger.error(f"Error scoring project {project.id}: {e}")
            results.append({
                "project_id": project.id,
                "project_name": project.project_name,
                "district": project.district,
                "status": project.status,
                "score_value": None,
                "confidence": None,
                "explanation": f"Scoring error: {str(e)}",
                "tokens_used": 0,
                "model_name": "N/A",
                "model_version": "N/A",
                "error": str(e)
            })
    
    return results


# ============================================================================
# STATISTICS COMPUTATION
# ============================================================================

def compute_summary_stats(scoring_results: list[dict]) -> dict[str, Any]:
    """Compute summary statistics from scoring results."""
    scores = [r["score_value"] for r in scoring_results if r["score_value"] is not None]
    confidences = [r["confidence"] for r in scoring_results if r["confidence"] is not None]
    
    # Score histogram bins (0-20, 20-40, 40-60, 60-80, 80-100)
    histogram = {"0-20": 0, "20-40": 0, "40-60": 0, "60-80": 0, "80-100": 0}
    for s in scores:
        if s < 20:
            histogram["0-20"] += 1
        elif s < 40:
            histogram["20-40"] += 1
        elif s < 60:
            histogram["40-60"] += 1
        elif s < 80:
            histogram["60-80"] += 1
        else:
            histogram["80-100"] += 1
    
    # Low confidence count
    low_confidence_threshold = 0.4
    low_confidence_count = sum(1 for c in confidences if c < low_confidence_threshold)
    low_confidence_rate = low_confidence_count / len(confidences) * 100 if confidences else 0
    
    # Empty explanations
    empty_explanations = sum(1 for r in scoring_results if not r.get("explanation") or r["explanation"].strip() == "")
    empty_explanation_rate = empty_explanations / len(scoring_results) * 100 if scoring_results else 0
    
    # Errors
    error_count = sum(1 for r in scoring_results if r.get("error"))
    error_rate = error_count / len(scoring_results) * 100 if scoring_results else 0
    
    return {
        "score_stats": {
            "count": len(scores),
            "mean": round(statistics.mean(scores), 2) if scores else 0,
            "std": round(statistics.stdev(scores), 2) if len(scores) > 1 else 0,
            "min": min(scores) if scores else 0,
            "max": max(scores) if scores else 0,
            "median": round(statistics.median(scores), 2) if scores else 0,
        },
        "confidence_stats": {
            "count": len(confidences),
            "mean": round(statistics.mean(confidences), 4) if confidences else 0,
            "std": round(statistics.stdev(confidences), 4) if len(confidences) > 1 else 0,
            "min": round(min(confidences), 4) if confidences else 0,
            "max": round(max(confidences), 4) if confidences else 0,
        },
        "histogram": histogram,
        "low_confidence": {
            "threshold": low_confidence_threshold,
            "count": low_confidence_count,
            "rate_percent": round(low_confidence_rate, 2),
        },
        "empty_explanations": {
            "count": empty_explanations,
            "rate_percent": round(empty_explanation_rate, 2),
        },
        "errors": {
            "count": error_count,
            "rate_percent": round(error_rate, 2),
        }
    }


# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_data_quality_report(
    null_analysis: dict,
    type_mismatches: dict,
    normalization_issues: dict,
    scoring_results: list[dict],
    summary_stats: dict,
    sample_size: int,
    null_threshold: float,
) -> dict:
    """Generate comprehensive data quality report."""
    
    # Identify failing fields (null % > threshold)
    failing_fields = {}
    for category, fields in null_analysis.items():
        for field, null_pct in fields.items():
            if null_pct > null_threshold * 100:
                failing_fields[field] = {
                    "category": category,
                    "null_percent": null_pct,
                    "threshold": null_threshold * 100,
                    "severity": "high" if null_pct > 50 else "medium"
                }
    
    # Count total issues
    total_type_issues = sum(len(v) for v in type_mismatches.values())
    total_norm_issues = sum(len(v) for v in normalization_issues.values())
    
    # Determine action required flag
    action_required = (
        summary_stats["low_confidence"]["rate_percent"] > 20 or
        summary_stats["empty_explanations"]["rate_percent"] > 20 or
        len(failing_fields) > 0
    )
    
    return {
        "generated_at": datetime.now().isoformat(),
        "sample_size": sample_size,
        "thresholds": {
            "null_threshold_percent": null_threshold * 100,
            "low_confidence_threshold": 0.4,
        },
        "action_required": action_required,
        "action_reasons": _get_action_reasons(summary_stats, failing_fields),
        "null_analysis": null_analysis,
        "failing_fields": failing_fields,
        "type_mismatches": {
            "summary": {k: len(v) for k, v in type_mismatches.items()},
            "total_count": total_type_issues,
            "details": type_mismatches,
        },
        "normalization_issues": {
            "summary": {k: len(v) for k, v in normalization_issues.items()},
            "total_count": total_norm_issues,
            "details": normalization_issues,
        },
        "model_stats": summary_stats,
        "failing_projects": [
            {
                "project_id": r["project_id"],
                "project_name": r["project_name"],
                "issue": "low_confidence" if r.get("confidence", 1) < 0.4 else "empty_explanation" if not r.get("explanation") else "error",
                "confidence": r.get("confidence"),
                "error": r.get("error"),
            }
            for r in scoring_results
            if r.get("confidence", 1) < 0.4 or not r.get("explanation") or r.get("error")
        ]
    }


def _get_action_reasons(summary_stats: dict, failing_fields: dict) -> list[str]:
    """Get list of reasons why action is required."""
    reasons = []
    
    if summary_stats["low_confidence"]["rate_percent"] > 20:
        reasons.append(f"Low confidence rate ({summary_stats['low_confidence']['rate_percent']:.1f}%) exceeds 20% threshold")
    
    if summary_stats["empty_explanations"]["rate_percent"] > 20:
        reasons.append(f"Empty explanation rate ({summary_stats['empty_explanations']['rate_percent']:.1f}%) exceeds 20% threshold")
    
    if failing_fields:
        reasons.append(f"{len(failing_fields)} required fields exceed null threshold: {', '.join(failing_fields.keys())}")
    
    return reasons


def generate_model_sanity_csv(scoring_results: list[dict], output_path: Path) -> None:
    """Generate CSV with project inputs and model outputs."""
    fieldnames = [
        "project_id", "project_name", "district", "status",
        "lat", "lon", "has_amenities", "has_promoters",
        "score_value", "confidence", "explanation",
        "risks", "strengths", "tokens_used", "model_name", "model_version", "error"
    ]
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for r in scoring_results:
            row = {k: r.get(k, "") for k in fieldnames}
            # Convert lists to strings
            row["risks"] = "; ".join(r.get("risks", []))
            row["strengths"] = "; ".join(r.get("strengths", []))
            writer.writerow(row)
    
    logger.info(f"Generated: {output_path}")


def generate_audit_markdown(
    data_quality_report: dict,
    scoring_results: list[dict],
    summary_stats: dict,
    null_threshold: float,
    confidence_threshold: float,
) -> str:
    """Generate markdown summary report."""
    
    action_status = "🚨 **ACTION REQUIRED**" if data_quality_report["action_required"] else "✅ **PASSED**"
    
    md = f"""# Data Model Audit Report

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Sample Size:** {data_quality_report['sample_size']} projects  
**Status:** {action_status}

---

## Executive Summary

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Null Rate (Required Fields) | {_calc_overall_null_rate(data_quality_report['null_analysis']):.1f}% | <{null_threshold*100:.0f}% | {"❌" if data_quality_report['failing_fields'] else "✅"} |
| Type Mismatch Count | {data_quality_report['type_mismatches']['total_count']} | 0 | {"⚠️" if data_quality_report['type_mismatches']['total_count'] > 0 else "✅"} |
| Normalization Issues | {data_quality_report['normalization_issues']['total_count']} | 0 | {"⚠️" if data_quality_report['normalization_issues']['total_count'] > 0 else "✅"} |
| Low Confidence Rate | {summary_stats['low_confidence']['rate_percent']:.1f}% | <20% | {"❌" if summary_stats['low_confidence']['rate_percent'] > 20 else "✅"} |
| Empty Explanations | {summary_stats['empty_explanations']['rate_percent']:.1f}% | <20% | {"❌" if summary_stats['empty_explanations']['rate_percent'] > 20 else "✅"} |
| Scoring Errors | {summary_stats['errors']['rate_percent']:.1f}% | <5% | {"❌" if summary_stats['errors']['rate_percent'] > 5 else "✅"} |

"""
    
    # Action Items
    if data_quality_report["action_required"]:
        md += """## ⚠️ Action Items

The following issues require immediate attention:

"""
        for reason in data_quality_report["action_reasons"]:
            md += f"- {reason}\n"
        md += "\n"
    
    # Null Analysis
    md += """## 1. Data Completeness (Null Analysis)

### Required Fields by Category

"""
    for category, fields in data_quality_report["null_analysis"].items():
        md += f"#### {category.title()}\n\n"
        md += "| Field | Null % | Status |\n"
        md += "|-------|--------|--------|\n"
        for field, pct in fields.items():
            status = "❌" if pct > null_threshold * 100 else "⚠️" if pct > 10 else "✅"
            md += f"| `{field}` | {pct:.1f}% | {status} |\n"
        md += "\n"
    
    # Failing Fields
    if data_quality_report["failing_fields"]:
        md += """### ❌ Fields Exceeding Null Threshold

"""
        for field, info in data_quality_report["failing_fields"].items():
            md += f"- **{field}** ({info['category']}): {info['null_percent']:.1f}% null (threshold: {info['threshold']:.0f}%)\n"
        md += "\n"
    
    # Type Mismatches
    md += """## 2. Data Type Validation

"""
    if data_quality_report["type_mismatches"]["total_count"] > 0:
        md += "| Field | Issue Count | Sample Issues |\n"
        md += "|-------|-------------|---------------|\n"
        for field, issues in data_quality_report["type_mismatches"]["details"].items():
            sample = issues[:3]
            sample_str = "; ".join([f"ID {i['project_id']}: {i['value']} ({i['issue']})" for i in sample])
            md += f"| `{field}` | {len(issues)} | {sample_str} |\n"
    else:
        md += "✅ No type mismatches detected.\n"
    md += "\n"
    
    # Normalization Issues
    md += """## 3. Normalization Issues

"""
    if data_quality_report["normalization_issues"]["total_count"] > 0:
        md += "| Issue Type | Count | Sample |\n"
        md += "|------------|-------|--------|\n"
        for issue_type, issues in data_quality_report["normalization_issues"]["details"].items():
            sample = issues[:2]
            sample_str = "; ".join([f"ID {i['project_id']}: '{i['value']}'" for i in sample])
            md += f"| {issue_type} | {len(issues)} | {sample_str} |\n"
    else:
        md += "✅ No normalization issues detected.\n"
    md += "\n"
    
    # AI Model Statistics
    md += f"""## 4. AI Model Sanity Check

### Score Distribution

| Bucket | Count | Percentage |
|--------|-------|------------|
"""
    total = sum(summary_stats["histogram"].values())
    for bucket, count in summary_stats["histogram"].items():
        pct = count / total * 100 if total > 0 else 0
        md += f"| {bucket} | {count} | {pct:.1f}% |\n"
    
    md += f"""
### Score Statistics

- **Mean:** {summary_stats['score_stats']['mean']}
- **Std Dev:** {summary_stats['score_stats']['std']}
- **Min:** {summary_stats['score_stats']['min']}
- **Max:** {summary_stats['score_stats']['max']}
- **Median:** {summary_stats['score_stats']['median']}

### Confidence Analysis

- **Mean Confidence:** {summary_stats['confidence_stats']['mean']:.4f}
- **Low Confidence Rate (<{confidence_threshold}):** {summary_stats['low_confidence']['rate_percent']:.1f}% ({summary_stats['low_confidence']['count']} projects)

### Model Issues

- **Empty Explanations:** {summary_stats['empty_explanations']['count']} ({summary_stats['empty_explanations']['rate_percent']:.1f}%)
- **Scoring Errors:** {summary_stats['errors']['count']} ({summary_stats['errors']['rate_percent']:.1f}%)

"""
    
    # Top Failing Projects
    failing = data_quality_report.get("failing_projects", [])[:10]
    if failing:
        md += """## 5. Failing Projects (Sample)

| Project ID | Name | Issue | Details |
|------------|------|-------|---------|
"""
        for p in failing:
            details = f"Confidence: {p['confidence']:.2f}" if p.get('confidence') is not None else p.get('error', 'N/A')
            md += f"| {p['project_id']} | {p['project_name'][:30]}... | {p['issue']} | {details} |\n"
    
    # Proposed Fixes
    md += """
## 6. Proposed Fixes

Based on the analysis, the following fixes are recommended:

### Data Quality Fixes

"""
    if data_quality_report["failing_fields"]:
        md += "1. **Address Null Fields:**\n"
        for field in data_quality_report["failing_fields"]:
            md += f"   - Implement data enrichment for `{field}`\n"
        md += "\n"
    
    if data_quality_report["normalization_issues"]["total_count"] > 0:
        md += "2. **Normalize Data:**\n"
        for issue_type in data_quality_report["normalization_issues"]["details"]:
            md += f"   - Fix {issue_type} inconsistencies\n"
        md += "\n"
    
    if data_quality_report["type_mismatches"]["total_count"] > 0:
        md += "3. **Fix Type Mismatches:**\n"
        for field in data_quality_report["type_mismatches"]["details"]:
            md += f"   - Validate and correct `{field}` values\n"
        md += "\n"
    
    md += """### Model Improvements

"""
    if summary_stats["low_confidence"]["rate_percent"] > 20:
        md += """1. **Low Confidence Issue:**
   - Review feature completeness for low-confidence projects
   - Consider adding more data signals to the feature pack
   - Tune LLM prompt for more confident responses

"""
    
    if summary_stats["empty_explanations"]["rate_percent"] > 5:
        md += """2. **Empty Explanations:**
   - Debug LLM response parsing
   - Add fallback explanation generation
   - Validate JSON schema compliance

"""
    
    if summary_stats["errors"]["rate_percent"] > 0:
        md += """3. **Scoring Errors:**
   - Review error logs for common failure patterns
   - Implement retry logic for transient failures
   - Add input validation before scoring

"""
    
    # Links to other reports
    md += """---

## Related Reports

- [`/reports/data_quality_report.json`](./data_quality_report.json) - Full JSON metrics
- [`/reports/model_sanity.csv`](./model_sanity.csv) - Per-project scoring results

---

*Generated by Data Quality Agent*
"""
    
    return md


def _calc_overall_null_rate(null_analysis: dict) -> float:
    """Calculate overall null rate across all required fields."""
    all_rates = []
    for fields in null_analysis.values():
        all_rates.extend(fields.values())
    return statistics.mean(all_rates) if all_rates else 0


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Data Quality Audit Script")
    parser.add_argument("--sample-size", type=int, default=100, help="Number of projects to sample")
    parser.add_argument("--null-threshold", type=float, default=0.2, help="Null percentage threshold (0-1)")
    parser.add_argument("--confidence-threshold", type=float, default=0.4, help="Low confidence threshold (0-1)")
    parser.add_argument("--skip-scoring", action="store_true", help="Skip AI scoring (for testing)")
    parser.add_argument("--output-dir", type=str, default="reports", help="Output directory for reports")
    args = parser.parse_args()
    
    # Setup
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    logger.info("=" * 60)
    logger.info("DATA QUALITY AUDIT STARTING")
    logger.info("=" * 60)
    logger.info(f"Sample Size: {args.sample_size}")
    logger.info(f"Null Threshold: {args.null_threshold * 100}%")
    logger.info(f"Confidence Threshold: {args.confidence_threshold}")
    logger.info(f"Output Directory: {output_dir}")
    
    # Connect to database
    engine = get_engine()
    SessionLocal = get_session_local(engine)
    
    with SessionLocal() as session:
        # 1. Sample diverse projects
        logger.info("\n[1/6] Sampling diverse projects...")
        projects = sample_diverse_projects(session, args.sample_size)
        
        if not projects:
            logger.error("No projects found in database!")
            return 1
        
        # 2. Analyze null percentages
        logger.info("\n[2/6] Analyzing null percentages...")
        null_analysis = analyze_null_percentages(projects)
        
        # 3. Check type mismatches
        logger.info("\n[3/6] Checking type mismatches...")
        type_mismatches = analyze_type_mismatches(projects)
        
        # 4. Check normalization issues
        logger.info("\n[4/6] Checking normalization issues...")
        normalization_issues = analyze_normalization_issues(projects)
        
        # 5. Run AI scoring
        if args.skip_scoring:
            logger.info("\n[5/6] Skipping AI scoring (--skip-scoring flag)")
            scoring_results = [
                {
                    "project_id": p.id,
                    "project_name": p.project_name,
                    "district": p.district,
                    "status": p.status,
                    "score_value": 0,
                    "confidence": 0,
                    "explanation": "Scoring skipped",
                    "tokens_used": 0,
                    "model_name": "N/A",
                    "model_version": "N/A",
                    "error": "skipped"
                }
                for p in projects
            ]
        else:
            logger.info("\n[5/6] Running AI scoring...")
            scoring_results = run_ai_scoring(projects, session)
        
        # 6. Compute summary statistics
        logger.info("\n[6/6] Computing summary statistics...")
        summary_stats = compute_summary_stats(scoring_results)
        
        # Generate reports
        logger.info("\n" + "=" * 60)
        logger.info("GENERATING REPORTS")
        logger.info("=" * 60)
        
        # Data quality report JSON
        data_quality_report = generate_data_quality_report(
            null_analysis=null_analysis,
            type_mismatches=type_mismatches,
            normalization_issues=normalization_issues,
            scoring_results=scoring_results,
            summary_stats=summary_stats,
            sample_size=len(projects),
            null_threshold=args.null_threshold,
        )
        
        json_path = output_dir / "data_quality_report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data_quality_report, f, indent=2, default=str)
        logger.info(f"Generated: {json_path}")
        
        # Model sanity CSV
        csv_path = output_dir / "model_sanity.csv"
        generate_model_sanity_csv(scoring_results, csv_path)
        
        # Audit markdown
        md_content = generate_audit_markdown(
            data_quality_report=data_quality_report,
            scoring_results=scoring_results,
            summary_stats=summary_stats,
            null_threshold=args.null_threshold,
            confidence_threshold=args.confidence_threshold,
        )
        
        md_path = output_dir / "data_model_audit.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        logger.info(f"Generated: {md_path}")
        
        # Summary output
        logger.info("\n" + "=" * 60)
        logger.info("AUDIT COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Projects Analyzed: {len(projects)}")
        logger.info(f"Type Mismatches: {data_quality_report['type_mismatches']['total_count']}")
        logger.info(f"Normalization Issues: {data_quality_report['normalization_issues']['total_count']}")
        logger.info(f"Low Confidence Rate: {summary_stats['low_confidence']['rate_percent']:.1f}%")
        logger.info(f"Empty Explanations: {summary_stats['empty_explanations']['rate_percent']:.1f}%")
        logger.info(f"Action Required: {'YES' if data_quality_report['action_required'] else 'NO'}")
        
        return 0 if not data_quality_report["action_required"] else 1


if __name__ == "__main__":
    sys.exit(main())
