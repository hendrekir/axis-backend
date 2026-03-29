# AXIS — Session 6 Build Plan
## The orchestration backbone + intelligence layer
### Updated: Session 5 complete · March 2026

---

## CONTEXT FILES TO LOAD AT SESSION START
```
AXIS_CLAUDE.md
AXIS_VISION_v1.md
AXIS_BUILD_FRAMEWORK_v1.md
AXIS_INTELLIGENCE_v1.md   ← NEW — AI models, data sources, signal filtering
AXIS_SESSION_6_PLAN.md    ← this file
```

---

## WHERE WE ARE

**Live:**
- Gmail OAuth + dispatch + morning digest running
- All 6 web screens deployed
- Stripe paywall working ($9/mo)
- Mode switcher live
- 6 memory tables in Neon (user_model, interactions, relationship_graph, patterns, sent_emails_cache, collective_patterns)

**Not built:**
- Gmail SEND
- Google Calendar OAuth
- Skills framework
- Multi-model routing (Perplexity, Grok, Gemini, GPT-5)
- Signal filtering system
- YouTube/Reddit/News/Spotify integrations
- Apprentice visibility
- iOS app

---

## SESSION 6 BUILD ORDER

### Phase A — Database (do first, 20 min)
Add 4 new tables to models.py:

```sql
CREATE TABLE skills (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  name TEXT NOT NULL,
  description TEXT,
  is_builtin BOOLEAN DEFAULT FALSE,
  is_active BOOLEAN DEFAULT TRUE,
  data_sources JSONB DEFAULT '[]',
  reasoning_model TEXT DEFAULT 'claude',
  trigger_type TEXT DEFAULT 'dispatch',
  trigger_config JSONB DEFAULT '{}',
  output_routing TEXT DEFAULT 'thread',
  system_prompt TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE skill_executions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  skill_id UUID REFERENCES skills(id),
  user_id UUID REFERENCES users(id),
  input_context JSONB,
  output_result TEXT,
  model_used TEXT,
  surface_delivered TEXT,
  user_action TEXT,
  execution_time_ms INTEGER,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE api_connections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  service TEXT NOT NULL,
  access_token TEXT,
  refresh_token TEXT,
  token_expiry TIMESTAMP,
  is_connected BOOLEAN DEFAULT FALSE,
  scopes JSONB DEFAULT '[]',
  metadata JSONB DEFAULT '{}',
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, service)
);

CREATE TABLE model_routes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  task_type TEXT NOT NULL,
  model TEXT NOT NULL,
  reasoning TEXT,
  cost_per_1m_input FLOAT,
  is_active BOOLEAN DEFAULT TRUE
);
```

### Phase B — Model router (30 min)
Create `services/model_router.py`:

```python
import os
import aiohttp
from services.claude_service import generate

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
GROK_API_KEY = os.getenv("GROK_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GPT_API_KEY = os.getenv("OPENAI_API_KEY")

async def route_to_model(model: str, system: str, user_msg: str, **kwargs) -> str:
    if model == "perplexity":
        return await call_perplexity(system, user_msg)
    elif model == "grok":
        return await call_grok(system, user_msg)
    elif model == "gemini_flash":
        return await call_gemini_flash(system, user_msg)
    elif model == "gemini_pro":
        return await call_gemini_pro(system, user_msg)
    elif model == "gpt5":
        return await call_gpt5(system, user_msg)
    else:
        return await generate(system_prompt=system, user_message=user_msg)

async def call_perplexity(system: str, user_msg: str) -> str:
    async with aiohttp.ClientSession() as session:
        resp = await session.post(
            "https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {PERPLEXITY_API_KEY}"},
            json={
                "model": "llama-3.1-sonar-large-128k-online",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_msg}
                ]
            }
        )
        data = await resp.json()
        return data["choices"][0]["message"]["content"]

async def call_grok(system: str, user_msg: str) -> str:
    async with aiohttp.ClientSession() as session:
        resp = await session.post(
            "https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROK_API_KEY}"},
            json={
                "model": "grok-4.1-fast",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_msg}
                ]
            }
        )
        data = await resp.json()
        return data["choices"][0]["message"]["content"]

async def call_gemini_flash(system: str, user_msg: str) -> str:
    async with aiohttp.ClientSession() as session:
        resp = await session.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent?key={GEMINI_API_KEY}",
            json={
                "contents": [{"parts": [{"text": f"{system}\n\n{user_msg}"}]}]
            }
        )
        data = await resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
```

Railway env vars to add:
```
PERPLEXITY_API_KEY=pplx-...
GROK_API_KEY=xai-...
GEMINI_API_KEY=AIza...
OPENAI_API_KEY=sk-...  (optional, for GPT-5)
```

### Phase C — Triage service (30 min)
Create `services/triage_service.py`:

The cheap pre-filter. Gemini Flash-Lite ($0.01/1M tokens) classifies every item before any expensive model sees it.

```python
async def triage_items(items: list, user_profile: dict) -> dict:
    """
    Classify all incoming items as spam/noise/relevant/urgent.
    Returns dict with keys: urgent, relevant, noise.
    Only urgent and relevant pass to expensive models.
    """
    prompt = f"""
    User profile: {user_profile}
    
    For each item below, classify as:
    - urgent (score 7-10): needs action today
    - relevant (score 4-6): interesting but not urgent
    - noise (score 1-3): not relevant to this user
    
    Items: {items}
    
    Return JSON: [{{"id": "...", "score": 8, "class": "urgent", "reason": "..."}}]
    """
    result = await call_gemini_flash("You are a relevance classifier.", prompt)
    return parse_triage_result(result)
```

### Phase D — Signal filter (20 min)
Create `services/signal_filter.py`:

Apply the 5 noise filters after triage:
1. Relevance check against user model
2. Urgency scoring
3. Context check (calendar + location)
4. Deduplication (24hr window)
5. Apprentice filter (dismissed topics)

### Phase E — Gmail SEND (45 min)
This is the highest-value feature. Close the action loop.

1. Add `gmail.send` scope to OAuth flow in `routes/gmail.py`
2. Create `services/gmail_send.py`:

```python
async def send_email_draft(user, to: str, subject: str, body: str, thread_id: str = None):
    """Send email via Gmail API using stored credentials."""
    service = build_gmail_service(user.gmail_access_token)
    
    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject
    
    if thread_id:
        message['References'] = thread_id
    
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    
    service.users().messages().send(
        userId='me',
        body={'raw': raw, 'threadId': thread_id}
    ).execute()
```

3. Add POST /gmail/send endpoint
4. Update dispatch prompt to set `action_type: "send_email"` for high-intent emails
5. Add [Send] button to thread messages in React

### Phase F — Google Calendar OAuth (45 min)
1. Add Calendar OAuth scopes to Google Cloud project
2. Create `routes/calendar.py` — OAuth flow
3. Create `services/calendar_service.py` — fetch events
4. Add `calendar_connected` column to users table
5. Build meeting prep cron — fires 30 min before each event

### Phase G — Skills framework (1 hr)
1. Seed built-in skills for new users (email, calendar, finance, research, entertainment)
2. Create `routes/skills.py` — CRUD + manual trigger
3. Update dispatch to loop through active skills instead of monolithic prompt
4. Skills specify: data_sources + reasoning_model + output_routing

### Phase H — Perplexity + Grok integrations (30 min)
1. Add `services/perplexity_service.py` — research skill powered by Perplexity
2. Add `services/grok_service.py` — entertainment/social skill powered by Grok
3. Seed Research Skill and Entertainment Skill using these services

### Phase I — YouTube + Reddit + News (45 min)
1. `services/youtube_service.py` — YouTube Data API v3, Gemini processes video
2. `services/reddit_service.py` — Reddit API, community post fetching
3. `services/news_service.py` — Google News + RSS aggregation
4. Add these as data sources available to skills

---

## START COMMAND

```bash
cd ~/forge/axis-backend
claude
```

First message:
```
Read all 5 AXIS context files from the repo root.

Session 6 goal: build the orchestration backbone.

Start with Phase A — add 4 new tables to models.py:
skills, skill_executions, api_connections, model_routes

SQL schemas are in AXIS_SESSION_6_PLAN.md Section "Phase A".
Show me the SQLAlchemy ORM models before running the migration.
```

---

## SUCCESS CRITERIA FOR SESSION 6

End of session, these should all work:
- [ ] `POST /skills` creates a custom skill
- [ ] `GET /skills` returns user's active skills
- [ ] `POST /cron/dispatch` routes tasks through skills engine
- [ ] Gmail OAuth has send scope, `/gmail/send` endpoint works
- [ ] Google Calendar OAuth connected, events fetchable
- [ ] Model router correctly sends to Claude/Perplexity/Grok based on task_type
- [ ] Triage service classifies items before expensive model calls
- [ ] Research skill uses Perplexity
- [ ] Entertainment skill uses Grok

---

*Update success criteria as each item is completed.*
*Next session: Session 7 = entertainment layer (Spotify + Reddit + YouTube + News + Grok).*

**END OF AXIS SESSION 6 PLAN**
