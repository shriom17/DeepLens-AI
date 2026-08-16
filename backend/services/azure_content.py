import os

from dotenv import load_dotenv
from azure.ai.contentunderstanding import ContentUnderstandingClient
from azure.ai.contentunderstanding.models import AnalysisInput
from azure.identity import DefaultAzureCredential


load_dotenv()

endpoint = os.getenv("ENDPOINT")
analyzer_id = os.getenv("ANALYZER")

api_version = "2025-11-01"

credential = DefaultAzureCredential()

client = ContentUnderstandingClient(
    endpoint=endpoint,
    credential=credential,
    api_version=api_version
)


def analyze_notice(file_bytes):

    poller = client.begin_analyze(
        analyzer_id=analyzer_id,
        inputs=[
            AnalysisInput(data=file_bytes)
        ],
    )

    result = poller.result()

    return result