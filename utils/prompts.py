SUMMARY_PROMPT = """
You are an AI assistant that explains official notices.

Summarize the notice in simple English.

Focus on:
- What the notice is about
- Who needs to take action
- Important dates
- Important instructions

Do not invent information.

Notice:
{notice}
"""


ACTION_PROMPT = """
You are an AI assistant.

Extract the actions that a student needs to take from this notice.

Return a simple checklist.

Do not add information that is not present in the notice.

Notice:
{notice}
"""


QUESTION_PROMPT = """
Answer the user's question using only the information provided
in the notice.

If the answer is not present in the notice, say:
"I could not find this information in the notice."

Notice:
{notice}

Question:
{question}
"""