import os

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from backend.services.generative_ai import generate_summary, generate_actions


load_dotenv()


def _get_provider() -> str:
    return (os.getenv("AI_PROVIDER") or "azure").strip().lower()


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


def _to_action_items(actions_text: str):
    lines = [
        line.strip("-* \t")
        for line in actions_text.split("\n")
        if line.strip()
    ]
    return lines if lines else actions_text


def _build_gemini_notice_data(content: str, title: str) -> dict:
    summary = generate_summary(content)
    actions = generate_actions(content)

    notice_data = {
        "Title": title,
        "AISummary": summary,
        "Content": content[:12000]
    }

    if actions:
        notice_data["ActionItems"] = _to_action_items(actions)

    return notice_data


def _process_with_azure(file_bytes: bytes) -> dict:
    from backend.services.azure_content import analyze_notice

    result = analyze_notice(file_bytes)
    fields = result.contents[0].fields
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