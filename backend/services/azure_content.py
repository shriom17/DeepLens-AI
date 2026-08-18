import os

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.contentunderstanding import ContentUnderstandingClient
from azure.ai.contentunderstanding.models import AnalysisInput
from azure.identity import DefaultAzureCredential


load_dotenv()

api_version = "2025-11-01"


def _build_client_and_analyzer():

    endpoint = os.getenv("ENDPOINT")
    analyzer_id = os.getenv("ANALYZER")
    api_key = os.getenv("AZURE_CONTENT_KEY")

    if not endpoint:
        raise ValueError("Missing ENDPOINT in environment configuration.")

    if not endpoint.startswith("https://"):
        raise ValueError(
            "ENDPOINT must start with 'https://'. Azure services do not allow bearer token auth over non-TLS URLs."
        )

    if not analyzer_id:
        raise ValueError("Missing ANALYZER in environment configuration.")

    credential = AzureKeyCredential(api_key) if api_key else DefaultAzureCredential()

    client = ContentUnderstandingClient(
        endpoint=endpoint,
        credential=credential,
        api_version=api_version
    )

    return client, analyzer_id


def analyze_notice(file_bytes):

    if not file_bytes:
        raise ValueError("No file bytes provided for Azure analysis.")

    client, analyzer_id = _build_client_and_analyzer()

    poller = client.begin_analyze(
        analyzer_id=analyzer_id,
        inputs=[
            AnalysisInput(data=file_bytes)
        ],
    )

    result = poller.result()

    return result