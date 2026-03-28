MORNING_DIGEST_PROMPT = """
Generate a morning digest for {name}.

Current mode: {mode}
Timezone: {timezone}
Today's date: {date}

Their active tasks:
{tasks}

Recent thread context:
{recent_context}

Rules:
- Open with what happened overnight that matters.
- Surface the top 3 things they need to act on today, in order.
- End with one sentence of encouragement tied to their actual situation.
- Under 150 words. No bullet points. Short punchy sentences.
- End with "put the phone down and go do the real thing."
"""
