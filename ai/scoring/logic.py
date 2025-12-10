import json
import logging
from typing import Dict, Any
from ai.llm.adapter import run

logger = logging.getLogger("ai.scoring")

# Prompt Template
QUALITY_SCORE_PROMPT = """
You are a Real Estate Analysis AI. Evaluate the quality of this real estate project based on the provided features.

Input Data:
{features}

Task:
1. Assign a quality score from 0 to 100.
2. Identify primary risks (missing approvals, delays, lack of amenities).
3. Identify strengths (location, reputable builder, progress).
4. Provide a SHORT explanation (max 2 sentences).

Output JSON Format ONLY:
{{
    "score": <number 0-100>,
    "confidence": <number 0.0-1.0>,
    "risks": ["risk1", "risk2"],
    "strengths": ["strength1", "strength2"],
    "explanation": "text summary"
}}
"""

def score_project_quality(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runs the scoring logic against the LLM.
    """
    
    # Prepare prompt
    prompt = QUALITY_SCORE_PROMPT.format(features=json.dumps(features, indent=2))
    
    # Call Adapter
    # Start with lower temperature for deterministic results
    result = run(prompt, system="You are a JSON-only response bot.", temperature=0.2)
    
    if result.get("error"):
        logger.error(f"Scoring failed: {result['error']}")
        return {
            "score": 0,
            "confidence": 0,
            "explanation": f"Scoring unavailable: {result['error']}",
            "metadata": {"error": result['error']}
        }
        
    text = result["text"]
    
    # Simple JSON extraction (robustness improvement possible)
    try:
        # cleanup markdown code blocks if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
            
        data = json.loads(text.strip())
        
        # Validate schema basics
        return {
            "score": data.get("score", 0),
            "confidence": data.get("confidence", 0.0),
            "explanation": data.get("explanation", "No explanation provided."),
            "risks": data.get("risks", []),
            "strengths": data.get("strengths", []),
            "metadata": {
                "tokens_used": result["tokens_used"],
                "latency_ms": result["latency_ms"]
            }
        }
        
    except json.JSONDecodeError:
        logger.error(f"Failed to parse LLM response: {text}")
        return {
            "score": 0,
            "confidence": 0,
            "explanation": "Failed to parse AI response.",
            "metadata": {"raw_text": text}
        }
