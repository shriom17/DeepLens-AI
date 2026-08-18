import json
import re

from backend.services.ai_provider import generate_response as _provider_generate_response

from utils.prompts import (
    SUMMARY_PROMPT,
    ACTION_PROMPT,
    QUESTION_PROMPT,
    DOCUMENT_ANALYSIS_PROMPT
)


def generate_response(prompt):
    return _provider_generate_response(prompt)


def generate_summary(notice):

    prompt = SUMMARY_PROMPT.format(notice=notice)

    return generate_response(prompt)


def generate_actions(notice):

    prompt = ACTION_PROMPT.format(notice=notice)

    return generate_response(prompt)


def answer_question(notice, question):

    prompt = QUESTION_PROMPT.format(
        notice=notice,
        question=question
    )

    return generate_response(prompt)


def _extract_json_object(text: str):
    if not text:
        return None

    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?", "", candidate).strip()
        if candidate.endswith("```"):
            candidate = candidate[:-3].strip()

    try:
        return json.loads(candidate)
    except Exception:
        pass

    start = candidate.find("{")
    end = candidate.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    try:
        return json.loads(candidate[start:end + 1])
    except Exception:
        return None


def _normalize_list(value, limit: int | None = None):
    if isinstance(value, list):
        items = [str(v).strip() for v in value if str(v).strip()]
    elif isinstance(value, str) and value.strip():
        parts = [line.strip("-* \t") for line in value.split("\n") if line.strip()]
        items = [part for part in parts if part]
    else:
        items = []

    if limit is not None:
        return items[:limit]
    return items


def generate_document_analysis(notice: str):
    prompt = DOCUMENT_ANALYSIS_PROMPT.format(notice=(notice or "")[:16000])
    response = generate_response(prompt)
    parsed = _extract_json_object(response)

    if not isinstance(parsed, dict):
        return {
            "ExecutiveSummary": (response or "").strip(),
            "KeyPoints": [],
            "ImportantInformation": {
                "Dates": [],
                "Names": [],
                "Numbers": [],
                "Deadlines": []
            },
            "ActionItems": [],
            "DocumentType": "Unknown",
            "ResearchDetails": {
                "ResearchProblem": "",
                "Methodology": "",
                "KeyFindings": [],
                "Limitations": [],
                "FutureWork": []
            }
        }

    important = parsed.get("ImportantInformation") or {}
    research = parsed.get("ResearchDetails") or {}

    return {
        "ExecutiveSummary": str(parsed.get("ExecutiveSummary") or "").strip(),
        "KeyPoints": _normalize_list(parsed.get("KeyPoints"), limit=7),
        "ImportantInformation": {
            "Dates": _normalize_list(important.get("Dates")),
            "Names": _normalize_list(important.get("Names")),
            "Numbers": _normalize_list(important.get("Numbers")),
            "Deadlines": _normalize_list(important.get("Deadlines"))
        },
        "ActionItems": _normalize_list(parsed.get("ActionItems")),
        "DocumentType": str(parsed.get("DocumentType") or "Unknown").strip(),
        "ResearchDetails": {
            "ResearchProblem": str(research.get("ResearchProblem") or "").strip(),
            "Methodology": str(research.get("Methodology") or "").strip(),
            "KeyFindings": _normalize_list(research.get("KeyFindings")),
            "Limitations": _normalize_list(research.get("Limitations")),
            "FutureWork": _normalize_list(research.get("FutureWork"))
        }
    }