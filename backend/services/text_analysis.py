import os

from dotenv import load_dotenv
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential


load_dotenv()

endpoint = os.getenv("LANGUAGE_ENDPOINT")
key = os.getenv("LANGUAGE_KEY")


client = TextAnalyticsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(key)
)


def analyze_text(text):

    documents = [text]

    # Key Phrase Extraction
    key_phrases_result = client.extract_key_phrases(
        documents=documents
    )

    # Named Entity Recognition
    entities_result = client.recognize_entities(
        documents=documents
    )

    key_phrases = []
    entities = []

    # Extract key phrases
    for result in key_phrases_result:

        if not result.is_error:

            key_phrases = result.key_phrases

    # Extract entities
    for result in entities_result:

        if not result.is_error:

            for entity in result.entities:

                entities.append({
                    "text": entity.text,
                    "category": entity.category,
                    "confidence": entity.confidence_score
                })

    return {
        "key_phrases": key_phrases,
        "entities": entities
    }