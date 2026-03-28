BRAIN_DUMP_PROMPT = """
The user has dumped everything on their mind:

{dump_text}

Extract and rank up to 6 tasks by importance × urgency.
For each output EXACTLY this format (one per line):
TASK: [clear actionable title] | CAT: [work/health/home/money/family/admin/personal] | WHY: [one sentence reason for this rank] | URGENT: [true/false]

Then in 2 sentences explain the overall priority logic.
Be warm, direct, and specific. No fluff.
"""
