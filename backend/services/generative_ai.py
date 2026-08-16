import os

from dotenv import load_dotenv
from openai import AzureOpenAI

from utils.prompts import (
    SUMMARY_PROMPT,
    ACTION_PROMPT,
    QUESTION_PROMPT
)


load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-10-21"
)

deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")


def generate_response(prompt):

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

    return response.choices[0].message.content


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