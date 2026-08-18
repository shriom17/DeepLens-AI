import os

from dotenv import load_dotenv
from openai import AzureOpenAI

try:
    import google.generativeai as legacy_genai
except ImportError:
    legacy_genai = None

try:
    from google import genai as modern_genai
except ImportError:
    modern_genai = None


load_dotenv()


def _get_provider() -> str:
    return (os.getenv("AI_PROVIDER") or "azure").strip().lower()


def _generate_with_azure(prompt: str) -> str:
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_KEY")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

    missing = []
    if not endpoint:
        missing.append("AZURE_OPENAI_ENDPOINT")
    if not api_key:
        missing.append("AZURE_OPENAI_KEY")
    if not deployment:
        missing.append("AZURE_OPENAI_DEPLOYMENT")

    if missing:
        raise ValueError(
            "Missing Azure OpenAI configuration: " + ", ".join(missing)
        )

    client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version="2024-10-21"
    )

    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Azure OpenAI returned an empty response.")

    return content


def _generate_with_gemini(prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL") or "gemini-3.6-flash"

    if not api_key:
        raise ValueError("Missing Gemini configuration: GEMINI_API_KEY")

    if legacy_genai is not None:
        legacy_genai.configure(api_key=api_key)
        model = legacy_genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        content = getattr(response, "text", None)
    elif modern_genai is not None:
        client = modern_genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        content = getattr(response, "text", None)
    else:
        raise ImportError(
            "Gemini SDK is not installed. Install google-generativeai or google-genai."
        )

    if not content:
        raise RuntimeError("Gemini returned an empty response.")

    return content


def generate_response(prompt: str) -> str:
    if not prompt:
        raise ValueError("Prompt cannot be empty.")

    provider = _get_provider()

    try:
        if provider == "azure":
            return _generate_with_azure(prompt)
        if provider == "gemini":
            return _generate_with_gemini(prompt)

        raise ValueError(
            "Unsupported AI_PROVIDER value: "
            f"{provider}. Supported values are: azure, gemini."
        )
    except Exception as exc:
        raise RuntimeError(
            f"AI generation failed for provider '{provider}': {exc}"
        ) from exc