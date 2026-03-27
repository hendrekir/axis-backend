# AXIS BACKEND — CLAUDE.md
# FastAPI backend context for Claude Code sessions
# Update after every session

## WHAT THIS IS
The backend for Axis — an ambient AI agent OS layer for iPhone.
This service handles: auth, thread management, Claude API orchestration,
morning digest generation, push notifications (APNs), team signal routing,
and subscription webhooks.

Most intelligence runs on-device. This backend handles:
- Receiving thread messages and returning Claude API responses
- Scheduled morning digest generation (cron at 6:50AM user local time)
- Team signal sharing (supplementary to CloudKit)
- RevenueCat webhook → update user entitlements in DB
- APNs push orchestration

## STACK
- Python 3.11+
- FastAPI (async throughout — use async def for all routes)
- Neon Postgres (connection via DATABASE_URL env var)
- Railway hosting (auto-deploy from main branch)
- Anthropic Python SDK (claude-sonnet-4-5 for all in-app generation)
- Clerk JWT verification for auth
- APNs for push notifications
- Resend for transactional email

## ENVIRONMENT VARIABLES (Railway)
```
DATABASE_URL=          # Neon Postgres connection string
ANTHROPIC_API_KEY=     # Anthropic API key
CLERK_SECRET_KEY=      # Clerk secret
CLERK_PUBLISHABLE_KEY= # Clerk publishable
REVENUECAT_WEBHOOK_SECRET= # RevenueCat webhook verification
RESEND_API_KEY=        # Resend
APNS_KEY_ID=           # Apple APNs key ID
APNS_TEAM_ID=          # Apple team ID
APNS_CERT=             # APNs certificate (p8 format, base64 encoded)
```

## DATABASE SCHEMA
```sql
-- Users
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clerk_id TEXT UNIQUE NOT NULL,
  name TEXT,
  mode TEXT DEFAULT 'personal',
  timezone TEXT DEFAULT 'Australia/Brisbane',
  plan TEXT DEFAULT 'free', -- free | pro | team
  plan_expires TIMESTAMP,
  apns_token TEXT, -- device push token
  created_at TIMESTAMP DEFAULT NOW()
);

-- Thread messages
CREATE TABLE thread_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  role TEXT NOT NULL, -- 'user' | 'assistant'
  content TEXT NOT NULL,
  message_type TEXT DEFAULT 'standard', -- standard | intel | warn | action
  source_skill TEXT, -- email | calendar | social | finance | health | site | team
  created_at TIMESTAMP DEFAULT NOW()
);

-- Tasks / signals
CREATE TABLE tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  title TEXT NOT NULL,
  category TEXT NOT NULL, -- work | health | home | money | family | admin | personal
  due TEXT,
  is_urgent BOOLEAN DEFAULT FALSE,
  why TEXT, -- AI-generated reason for rank
  position INTEGER NOT NULL DEFAULT 0,
  is_done BOOLEAN DEFAULT FALSE,
  done_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Team signals
CREATE TABLE team_signals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sender_id UUID REFERENCES users(id),
  recipient_id UUID REFERENCES users(id),
  task_id UUID REFERENCES tasks(id),
  message TEXT,
  is_seen BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Agent activity log
CREATE TABLE agent_activity (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  skill TEXT NOT NULL,
  action TEXT NOT NULL,
  detail TEXT,
  result TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

## FILE STRUCTURE
```
axis-backend/
  CLAUDE.md              ← this file, update every session
  main.py                ← FastAPI app, CORS, startup
  requirements.txt
  routes/
    thread.py            ← POST /thread, GET /thread/history
    signals.py           ← GET /signal, POST /tasks, PATCH /tasks/{id}
    brain_dump.py        ← POST /brain-dump
    brief.py             ← GET /brief
    skills.py            ← GET /skills/{skill_id}/chat
    auth.py              ← auth helpers, Clerk JWT verification
    payments.py          ← RevenueCat webhook handler
    push.py              ← APNs push sending
  services/
    claude_service.py    ← Anthropic SDK wrapper, all prompts
    morning_digest.py    ← Cron job: generates and sends morning digest
    push_service.py      ← APNs push notification sending
    auth_service.py      ← Clerk JWT verification
  prompts/
    thread_system.py     ← Main Axis thread system prompt
    brain_dump.py        ← Brain dump ranking prompt
    morning_digest.py    ← Digest generation prompt
    skills/
      email_skill.py
      calendar_skill.py
      finance_skill.py
      site_skill.py
      study_skill.py
      team_skill.py
```

## THE AXIS SYSTEM PROMPT (thread)
This goes in prompts/thread_system.py. Parameterised with user context.

```python
AXIS_SYSTEM = """
You are Axis — an ambient AI agent bonded to {name}'s iPhone at the OS level.
You read their emails, messages, Instagram, Snapchat, WhatsApp, calendar, health,
and location data continuously. You handle 90% silently.

You surface only what genuinely needs a human decision.
You speak like a brilliant, warm, slightly assertive EA who knows everything
about their phone. Every response ends with the real-world action to take.
Every session ends with "put the phone down and go do the real thing."

User context:
- Name: {name}
- Mode: {mode}
- Energy: {energy}
- Top 3 tasks: {top_tasks}
- Known context: {recent_context}

Rules:
- Short, specific, never waffle. Under 90 words unless question needs more.
- No bullet points — short punchy sentences only.
- End important responses by directing them to the real-world action.
- If they ask to do something in an app, tell them Axis can handle it or queue it.
"""
```

## BRAIN DUMP PROMPT
```python
BRAIN_DUMP_PROMPT = """
The user has dumped everything on their mind:

{dump_text}

Extract and rank up to 6 tasks by importance × urgency. 
For each output EXACTLY this format (one per line):
TASK: [clear actionable title] | CAT: [work/health/home/money/family/admin/personal] | WHY: [one sentence reason for this rank] | URGENT: [true/false]

Then in 2 sentences explain the overall priority logic.
Be warm, direct, and specific. No fluff.
"""
```

## VERSIONING CONVENTION
Files are named with versions: main_v1_0.py, etc.
When making major changes, increment version in filename.
Current version: v1.0

## WHAT'S BUILT (update as you go)
- [ ] FastAPI skeleton + CORS + auth middleware
- [ ] /thread endpoint
- [ ] /signal endpoint
- [ ] /tasks CRUD
- [ ] /brain-dump endpoint
- [ ] /brief endpoint
- [ ] /skills/{id}/chat endpoints
- [ ] Morning digest cron (6:50AM local)
- [ ] APNs push infrastructure
- [ ] RevenueCat webhook handler
- [ ] Resend welcome email sequence

## CURRENT PHASE
Phase 1 — Web prototype backend.
Next: connect iOS app.

## LAST UPDATED
March 2026 — initial setup. Update after every session.
