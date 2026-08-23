import os

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from backend.services.generative_ai import generate_document_analysis


load_dotenv()


def _get_provider() -> str:
    configured = (os.getenv("AI_PROVIDER") or "").strip().lower()
    if configured:
        return configured

    # Auto-detect provider when AI_PROVIDER is not explicitly set.
    # This avoids silently defaulting to Azure in deployments where only Gemini
    # secrets were configured.
    gemini_configured = bool(
        (os.getenv("GEMINI_API_KEY") or "").strip()
        and (os.getenv("GEMINI_MODEL") or "").strip()
        and (os.getenv("GEMINI_FALLBACK_MODEL") or "").strip()
    )
    if gemini_configured:
        return "gemini"

    azure_configured = bool(
        (os.getenv("ENDPOINT") or "").strip()
        and (os.getenv("ANALYZER") or "").strip()
    )
    if azure_configured:
        return "azure"

    return "azure"


def _is_pdf(file_bytes: bytes) -> bool:
    return bool(file_bytes) and file_bytes[:4] == b"%PDF"


def _extract_pdf_text(file_bytes: bytes) -> str:
    try:
        import fitz  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "PyMuPDF is required for Gemini PDF extraction. Install 'pymupdf'."
        ) from exc

    try:
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            pages = [page.get_text("text") for page in doc]

        text = "\n".join(part.strip() for part in pages if part and part.strip())
        if not text:
            raise ValueError("No extractable text found in PDF.")

        return text
    except Exception as exc:
        raise RuntimeError(f"Failed to extract PDF text locally: {exc}") from exc


def _extract_web_text(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else "Web Document"

    text = soup.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    cleaned = "\n".join(lines)

    if not cleaned:
        raise ValueError("No extractable webpage text found.")

    return title, cleaned


def _build_gemini_notice_data(content: str, title: str) -> dict:
    analysis = generate_document_analysis(content)

    important = analysis.get("ImportantInformation") or {}
    research = analysis.get("ResearchDetails") or {}

    notice_data = {
        "Title": title,
        "ExecutiveSummary": analysis.get("ExecutiveSummary", ""),
        "KeyPoints": analysis.get("KeyPoints", []),
        "ImportantDates": important.get("Dates", []),
        "ImportantNames": important.get("Names", []),
        "ImportantNumbers": important.get("Numbers", []),
        "Deadlines": important.get("Deadlines", []),
        "ActionItems": analysis.get("ActionItems", []),
        "DocumentType": analysis.get("DocumentType", "Unknown")
    }

    research_problem = research.get("ResearchProblem")
    methodology = research.get("Methodology")
    key_findings = research.get("KeyFindings") or []
    limitations = research.get("Limitations") or []
    future_work = research.get("FutureWork") or []

    if research_problem:
        notice_data["ResearchProblem"] = research_problem
    if methodology:
        notice_data["Methodology"] = methodology
    if key_findings:
        notice_data["KeyFindings"] = key_findings
    if limitations:
        notice_data["Limitations"] = limitations
    if future_work:
        notice_data["FutureWork"] = future_work

    # Remove empty fields to keep the response concise and user-friendly.
    cleaned = {}
    for key, value in notice_data.items():
        if isinstance(value, list) and not value:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        cleaned[key] = value

    return cleaned


def _process_with_azure(file_bytes: bytes) -> dict:
    from backend.services.azure_content import analyze_notice

    result = analyze_notice(file_bytes)

    contents = getattr(result, "contents", None) or []
    if not contents:
        raise RuntimeError(
            "Azure Content Understanding returned no contents in the analysis result. "
            "Check ENDPOINT/ANALYZER and that the uploaded file is supported."
        )

    fields = getattr(contents[0], "fields", None) or {}
    if not fields:
        raise RuntimeError(
            "Azure analyzer returned 0 extracted fields. "
            "This usually means ANALYZER is pointing at the wrong analyzer, the analyzer schema doesn't match, "
            "or the analyzer isn't trained/published for this document type."
        )
    notice_data = {}

    for field_name, field_value in fields.items():

        if hasattr(field_value, "value_string"):
            notice_data[field_name] = field_value.value_string

        elif hasattr(field_value, "value_array"):
            notice_data[field_name] = [
                item.value_string
                for item in field_value.value_array
            ]

        else:
            notice_data[field_name] = str(field_value)

    if not notice_data:
        raise RuntimeError(
            "Azure analysis completed but produced an empty notice payload. "
            "Verify your analyzer field mappings."
        )

    return notice_data


def _process_with_gemini_file(file_bytes: bytes) -> dict:
    if not _is_pdf(file_bytes):
        raise ValueError(
            "Gemini file analysis currently supports PDF uploads only."
        )

    content = _extract_pdf_text(file_bytes)
    return _build_gemini_notice_data(content, title="Uploaded PDF")


def _fetch_url_content(url: str):
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    content_type = (response.headers.get("content-type") or "").lower()
    return response, content_type


def _process_with_gemini_url(url: str) -> dict:
    response, content_type = _fetch_url_content(url)

    if "application/pdf" in content_type or url.lower().endswith(".pdf"):
        content = _extract_pdf_text(response.content)
        return _build_gemini_notice_data(content, title="Web PDF")

    if "text/html" in content_type or "application/xhtml+xml" in content_type:
        title, content = _extract_web_text(response.text)
        return _build_gemini_notice_data(content, title=title)

    if content_type.startswith("text/"):
        content = response.text.strip()
        if not content:
            raise ValueError("URL returned empty text content.")
        return _build_gemini_notice_data(content, title="Text Document")

    raise ValueError(f"Unsupported URL content type for Gemini mode: {content_type}")


def process_notice(file_bytes):

    provider = _get_provider()

    if provider == "azure":
        return _process_with_azure(file_bytes)

    if provider == "gemini":
        return _process_with_gemini_file(file_bytes)

    raise ValueError(
        f"Unsupported AI_PROVIDER value: {provider}. Supported values: azure, gemini."
    )


def process_notice_url(url: str):

    if not url or not (url.startswith("http://") or url.startswith("https://")):
        raise ValueError("URL must start with http:// or https://")

    provider = _get_provider()

    if provider == "azure":
        response, _ = _fetch_url_content(url)
        return _process_with_azure(response.content)

    if provider == "gemini":
        return _process_with_gemini_url(url)

    raise ValueError(
        f"Unsupported AI_PROVIDER value: {provider}. Supported values: azure, gemini."
    )