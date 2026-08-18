from backend.services.ai_provider import generate_response as _provider_generate_response

from utils.prompts import (
    SUMMARY_PROMPT,
    ACTION_PROMPT,
    QUESTION_PROMPT
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