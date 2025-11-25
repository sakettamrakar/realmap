"""Print a concise summary for a single project."""
from __future__ import annotations

import argparse
import sys
from textwrap import indent

from cg_rera_extractor.analysis.projects import get_project_summary


def _format_score_line(label: str, value: int | None) -> str:
    return f"{label}: {value if value is not None else 'n/a'}"


def _format_project_section(summary) -> str:
    parts = [
        f"Project: {summary.project['project_name']}",
        f"Registration: {summary.project['rera_registration_number']} ({summary.project['state_code']})",
        f"Status: {summary.project.get('status') or 'Unknown'}",
        f"District / Tehsil: {summary.project.get('district') or '-'} / {summary.project.get('tehsil') or '-'}",
        f"Address: {summary.project.get('full_address') or 'n/a'}",
    ]

    lat = summary.project.get("latitude")
    lon = summary.project.get("longitude")
    if lat is not None and lon is not None:
        parts.append(f"Coordinates: {lat:.6f}, {lon:.6f}")

    return "\n".join(parts)


def _format_scores(summary) -> str:
    if not summary.scores:
        return "Scores: n/a"

    score_lines = [
        "Scores:",
        indent(
            "\n".join(
                [
                    _format_score_line("Overall", summary.scores.overall_score),
                    _format_score_line("Amenity", summary.scores.amenity_score),
                    _format_score_line("Location", summary.scores.location_score),
                    _format_score_line(
                        "Connectivity", summary.scores.connectivity_score
                    ),
                    _format_score_line("Daily Needs", summary.scores.daily_needs_score),
                    _format_score_line(
                        "Social Infra", summary.scores.social_infra_score
                    ),
                    f"Version: {summary.scores.score_version or 'n/a'}",
                ]
            ),
            "  ",
        ),
    ]

    return "\n".join(score_lines)


def _format_amenities(title: str, amenities) -> str:
    if not amenities:
        return f"{title}: none recorded"

    lines = [title]
    for item in amenities:
        label = item.amenity_type.replace("_", " ").title()
        details: str | None = None
        if item.onsite_details:
            details = ", ".join(f"{k}: {v}" for k, v in item.onsite_details.items())

        description = f"{label}"
        if item.radius_km is not None:
            description += f" within {item.radius_km:.2f} km"
        if item.nearby_count is not None:
            description += f" (count: {item.nearby_count})"
        if item.nearest_km is not None:
            description += f", nearest {item.nearest_km:.2f} km"
        if item.onsite_available:
            description += " [onsite]"
        if details:
            description += f" | {details}"

        lines.append(f"- {description}")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--project-id", type=int, help="Database ID for the project")
    group.add_argument(
        "--reg", dest="registration", help="RERA registration number (with state)"
    )
    args = parser.parse_args()

    project_key = args.project_id if args.project_id is not None else args.registration

    try:
        summary = get_project_summary(project_key)
    except ValueError as exc:  # pragma: no cover - CLI feedback only
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    sections = [
        _format_project_section(summary),
        "",
        _format_scores(summary),
        "",
        _format_amenities("Onsite amenities", summary.onsite_amenities),
        "",
        _format_amenities("Location context", summary.location_context),
    ]

    print("\n".join(sections))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
