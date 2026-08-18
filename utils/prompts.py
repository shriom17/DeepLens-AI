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


DOCUMENT_ANALYSIS_PROMPT = """
You are an expert document analyst.

Analyze the document and return ONLY valid JSON with this exact schema:
{{
	"ExecutiveSummary": "string, max 5 sentences",
	"KeyPoints": ["max 7 concise bullets"],
	"ImportantInformation": {{
		"Dates": ["important dates only"],
		"Names": ["important people/organizations only"],
		"Numbers": ["important numbers, amounts, IDs, percentages"],
		"Deadlines": ["explicit deadlines only"]
	}},
	"ActionItems": ["only required actions; no suggestions"],
	"DocumentType": "short label",
	"ResearchDetails": {{
		"ResearchProblem": "string",
		"Methodology": "string",
		"KeyFindings": ["list"],
		"Limitations": ["list"],
		"FutureWork": ["list"]
	}}
}}

Rules:
- Keep output concise and user-friendly.
- Do not repeat or copy long passages from the source.
- Paraphrase information; do not dump the original text.
- If information is not present, return empty string or empty list.
- Include ResearchDetails only when the document is a research paper; otherwise keep empty values.
- Return JSON only, no markdown, no code fences.

Document:
{notice}
"""