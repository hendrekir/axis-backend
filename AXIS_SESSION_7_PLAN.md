# AXIS — Session 7 Build Plan
## The complete intelligence layer
### Updated: March 2026

---

## CONTEXT: WHAT SESSION 7 BUILDS

Session 6 built the orchestration backbone — skills, multi-model routing, triage, signal filter.
Session 7 fills it with intelligence that makes Axis feel like Jarvis.

Three types of builds:
- PART A: High-leverage, build first (context notes, send button, smart notes, status, expert intel)
- PART B: Automation and monitoring (voice, PWA, follow-ups, weather, ambient watch, suggestions)
- PART C: Advanced execution (multi-turn tasks, planning, weekly email, Zapier, Stripe)

---

## PART A — Build first, highest leverage

### A1 — Context notes (30 min)

Add users.context_notes TEXT column. Inject into every Claude call. Settings UI.

Migration (add to startup block in main.py):
  ALTER TABLE users ADD COLUMN IF NOT EXISTS context_notes TEXT;

context_assembler.py: if user.context_notes add to context dict as "context_notes"
prompts/dispatch_v2.py: add {context_notes} field to system prompt
Settings.jsx: textarea "What Axis should always know" — onBlur calls PATCH /me

---

### A2 — [Send] + [Edit] buttons on email drafts (1 hour — frontend only)

Thread.jsx: detect message_type="email_draft", render Send + Edit + Dismiss buttons
Send button calls POST /gmail/send with draft content
Add sendEmailDraft(to, subject, body, threadId, token) to api.js
On send: show "Sent." confirmation, log to interactions as action_taken="sent"

---

### A3 — Smart notes table + thread commands (2 hours)

New table (add to startup migration):
  CREATE TABLE IF NOT EXISTS notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    content TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',
    source TEXT DEFAULT 'manual',
    context_snapshot JSONB DEFAULT '{}',
    related_email_ids TEXT[] DEFAULT '{}',
    related_task_ids UUID[] DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
  );

New file: routes/notes.py
  POST /notes         — save note, auto-extract tags via Claude
  GET  /notes         — list recent notes paginated
  GET  /notes/search?q= — semantic search via Claude
  GET  /notes/related?topic= — notes + emails + tasks about topic
  DELETE /notes/:id

New file: services/notes_service.py
  save_note(user_id, content, source, context_snapshot, db)
  search_notes(user_id, query, db) — Claude semantic match
  get_related(user_id, topic, db) — unified "what I know about X"

Update prompts/thread_system.py:
  "remember [anything]" → POST /notes → "Got it. I'll remember that."
  "what do I know about [X]" → GET /notes/related → synthesise and respond
  "what did I note about [X]" → GET /notes/search → respond with matches
  "read back my notes on [X]" → full readback

Register router in main.py

---

### A4 — Status command (1 hour)

Update thread_system.py to detect "what's the status of X" / "where are we with X"

New file: services/status_service.py
  get_status(user, topic, db):
    - Pull thread_messages, tasks, notes, sent_emails_cache, relationship_graph
    - If topic is person: last email, outstanding invoice, next meeting, relationship score
    - If topic is project: open tasks, last email, calendar events, notes, invoices
    - Claude synthesises into 3-5 bullet status report with specific facts + dates
    - Ends with: "Anything specific you want to action?"

---

### A5 — Expert intelligence command (2 hours)

Update prompts/research.py — add EXPERT_INTELLIGENCE_SYSTEM:
  Step 1: Factual briefing from trusted sources only
    Tier 1: Reuters, AP, BBC, AFP, official government, peer-reviewed, regulatory bodies
    Tier 2: Named experts with institution affiliation
    Never cite: social media, unverified blogs, anonymous sources
  Step 2: Personal relevance check
    Does this connect to user's clients/suppliers/industries/projects?
    If yes: state specifically with evidence
    If no: do not speculate, end briefing cleanly

New file: services/intelligence_service.py
  expert_briefing(topic, user, db):
    - Perplexity sonar-pro with source filter
    - Second Claude pass for personal relevance
  detect_personal_relevance(briefing, user_context):
    - Quick Claude call: direct connection exists?

Update thread_system.py: "what's happening with [X]" triggers expert_briefing

---

## PART B — Automation and monitoring

### B1 — Voice input on web (2 hours — frontend only)

MicButton component using window.SpeechRecognition (webkitSpeechRecognition fallback)
Add to Thread.jsx and BrainDump.jsx
Hold to record, release to transcribe, fills text input
Only renders if browser supports Web Speech API
lang defaults to 'en-AU'

---

### B2 — PWA manifest + service worker (1 hour — frontend only)

axis-web/public/manifest.json:
  name, short_name, display:"standalone", background_color, theme_color, icons array

index.html additions:
  <link rel="manifest" href="/manifest.json">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="Axis">
  <link rel="apple-touch-icon" href="/icon-192.png">

axis-web/public/sw.js — basic cache-first service worker
Register service worker in main.jsx

Need to create: icon-192.png and icon-512.png (Axis logo, dark background)

---

### B3 — Follow-up tracker (2 hours)

New table:
  CREATE TABLE IF NOT EXISTS followups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    email_id TEXT NOT NULL,
    to_email TEXT NOT NULL,
    subject TEXT,
    sent_at TIMESTAMP NOT NULL,
    follow_up_at TIMESTAMP NOT NULL,
    status TEXT DEFAULT 'pending',
    draft_followup TEXT,
    created_at TIMESTAMP DEFAULT NOW()
  );

Update routes/gmail.py POST /gmail/send:
  After successful send: call followup_service.register_followup()

New file: services/followup_service.py
  register_followup(user_id, email_id, to_email, subject, db) — saves with follow_up_at = sent_at + 3 days
  check_followups(db) — hourly cron, surfaces unresponded emails

Add to APScheduler: hourly job calling check_followups

---

### B4 — Weather + travel time in morning brief (1 hour)

New env vars needed:
  OPENWEATHER_API_KEY  (free at openweathermap.org)
  GOOGLE_MAPS_API_KEY  (enable Distance Matrix API in existing Google Cloud project)

New file: services/weather_service.py
  get_weather(lat, lon) — OpenWeather current conditions
  get_travel_time(origin_lat, origin_lon, dest_address) — Google Maps Distance Matrix

Update services/morning_digest.py:
  If next calendar event has a location:
    Get weather for that location
    Calculate travel time from user's home/office
    Add to digest: "Site visit 8AM. 14°C rain. Leave by 7:20 based on current traffic."

---

### B5 — Ambient monitoring — "watch this for me" (2 hours)

New table:
  CREATE TABLE IF NOT EXISTS watches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    topic TEXT NOT NULL,
    watch_type TEXT DEFAULT 'topic',
    sources TEXT[] DEFAULT '{}',
    threshold TEXT DEFAULT 'material',
    is_active BOOLEAN DEFAULT TRUE,
    last_checked TIMESTAMP,
    last_triggered TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
  );

New file: routes/watches.py
  POST /watches       — create watch
  GET  /watches       — list active watches
  DELETE /watches/:id — remove watch

New file: services/watch_service.py
  check_watches(db) — runs every 15 min alongside dispatch
  For topic/news watches: Perplexity sonar, compare to last check
  For person watches: check Gmail for new emails from that person
  If material change: thread message + push notification
  Update last_checked always, last_triggered only when something found

Update thread_system.py:
  "watch [topic] for me" → POST /watches → "I'll let you know if anything material changes."
  "stop watching [topic]" → DELETE watch
  "what are you watching" → GET /watches list

Wire into APScheduler 15-min job

---

### B6 — Risk + opportunity detection (1 hour)

New file: services/risk_service.py
  detect_risks(user, ctx, db):
    Check 1: Quotes/proposals sent 3+ days ago with no reply
    Check 2: High-importance contacts silent 14+ days
    Check 3: Calendar conflicts in next 48hrs
    Check 4: Invoices 7+ days overdue (if Stripe connected)
    Returns: list of risk items with urgency=8, surface="push"

Wire into dispatch_user() in dispatch.py:
  After fetching raw_items, append risk_service.detect_risks() output
  These bypass triage (already high-urgency) but go through signal filter

---

### B7 — Proactive skill suggestions (2 hours)

New table:
  CREATE TABLE IF NOT EXISTS skill_suggestions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    pattern_detected TEXT NOT NULL,
    suggested_skill_config JSONB NOT NULL,
    suggestion_text TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    dismissed_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
  );

New file: services/suggestion_service.py
  detect_patterns(user, db) — runs in Sunday apprentice cycle
    Detect: manual invoice chases, repeated searches, recurring tasks, frequent contacts
  surface_suggestions(user, suggestions, db)
    Saves SkillSuggestion + ThreadMessage with message_type="skill_suggestion"
  accept_suggestion(suggestion_id, user, db)
    Creates actual skill from suggested_skill_config

New route: POST /suggestions/:id/accept — creates skill from suggestion
New route: POST /suggestions/:id/dismiss — marks dismissed_until + 14 days

Thread.jsx: render message_type="skill_suggestion" with [Create Skill] [Not Now] buttons

Wire detect_patterns into Sunday 3AM apprentice cron

---

### B8 — Multi-turn task execution (3 hours)

Update prompts/thread_system.py:
  Add MULTI_TURN_EXECUTION section
  Intent detection: schedule_meeting | send_email | reschedule_event | create_task | research_report
  State tracking via thread history (no new tables needed)
  Gather info one question at a time
  Always confirm before executing
  Execute via existing APIs: gmail/send, calendar create_event, tasks

Update services/calendar_service.py:
  Add create_event(user, title, start_time, end_time, attendees, description, db)
  Called when multi-turn execution detects scheduling intent

New thread command handling in thread.py route:
  When Claude returns an execution command in JSON:
    {"execute": "create_calendar_event", "params": {...}}
  Route to appropriate service

---

### B9 — Planning + brainstorming skill (2 hours)

New file: prompts/brainstorm.py
  BRAINSTORM_SYSTEM:
    Phase 1 — Understand: ask focused clarifying questions, one at a time
    Phase 2 — Validate: Perplexity for real market/competition/pricing data
    Phase 3 — Structure: phased plan with specific next steps
    Phase 4 — Deliver: draft first concrete output
    Phase 5 — Save: offer to save as living skill

New skill type: "brainstorm" and "plan"
  trigger_type = "manual"
  output_routing = "thread"
  reasoning_model = "claude" (with Perplexity sub-calls)

Update thread_system.py:
  "help me brainstorm [X]" → triggers brainstorm session
  "help me plan [X]" → triggers plan session
  On completion: "Want me to save this as a project I'll keep updated?"

---

### B10 — Weekly retrospective email (1 hour)

New file: services/weekly_retrospective.py
  send_weekly_retrospective(user, db):
    Compute week stats from interactions table
    Pull user_model patterns
    Claude generates warm specific email (150-200 words)
    Send via Resend

RETROSPECTIVE_SYSTEM prompt:
  Specific facts not generalities
  What you handled / what's still open / one thing Axis learned / one suggestion

Add to APScheduler:
  scheduler.add_job(_scheduled_weekly_retrospective, "cron",
    day_of_week="sun", hour=8, minute=0, id="weekly_retrospective")

---

### B11 — Zapier/webhook skill output (1 hour)

Update services/output_router.py:
  If skill.output_routing == "webhook":
    POST to skill.trigger_config["webhook_url"] with {skill, output, urgency, timestamp}

New inbound webhook endpoint:
  POST /webhooks/skill-trigger — receives from Zapier, triggers named skill

Update skill model: output_routing options now include "webhook"

---

### B12 — Stripe finance intelligence (2 hours)

New file: routes/stripe_connect.py (user's own Stripe — separate from billing)
  GET /auth/stripe-connect — Stripe Connect OAuth
  GET /auth/stripe-connect/callback — stores in api_connections(service="stripe_connect")

New file: services/stripe_user_service.py
  get_overdue_invoices(user, db) — user's Stripe, filter by due_date < now
  get_invoice_chase_sequence(invoice, day) — voice-matched reminder at 7/14/30 days
  send_invoice_reminder(user, invoice, db) — draft + send via Gmail

Wire into dispatch: Finance Intelligence skill calls stripe_user_service

---

## PART C — New env vars (add to Railway)

  OPENWEATHER_API_KEY     — openweathermap.org free tier
  GOOGLE_MAPS_API_KEY     — enable Distance Matrix in Google Cloud console

All other services reuse existing credentials.

---

## START COMMAND FOR SESSION 7 CONTINUATION

  cd ~/forge/axis-backend && claude

First message:
  Read CLAUDE.md, AXIS_BUILD_FRAMEWORK_v2.md, AXIS_BUILD_CHECKLIST_v2.md, AXIS_SESSION_7_PLAN.md.

  Session 7 Part A — build in order:

  A1: Add context_notes column to users via ALTER TABLE in startup migration.
      Update context_assembler.py to inject context_notes into every Claude call.
      Add context notes textarea to Settings.jsx in axis-web.

  A2: Add Send + Edit + Dismiss buttons to Thread.jsx for message_type="email_draft".
      Call POST /gmail/send on Send. Show confirmation.

  A3: Create notes table. Create routes/notes.py and services/notes_service.py.
      Update thread_system.py for "remember X", "what do I know about X" commands.

  A4: Create services/status_service.py. Update thread_system.py for status queries.

  A5: Update prompts/research.py with EXPERT_INTELLIGENCE_SYSTEM.
      Create services/intelligence_service.py with expert_briefing().

  Show me models.py before writing anything. Build and verify each piece before moving on.

---

## SUCCESS CRITERIA

  [ ] context_notes saves and injects into every Claude call
  [ ] [Send] button on email drafts calls POST /gmail/send
  [ ] "remember this" saves to notes table
  [ ] "what do I know about X" returns synthesised answer
  [ ] "what's the status of X" returns specific current picture
  [ ] "what's happening with X" returns expert briefing with personal relevance
  [ ] voice mic button works in Thread (Chrome)
  [ ] PWA — axis-web adds to iPhone home screen
  [ ] weather + travel time appears in morning brief
  [ ] follow-up tracker populates + surfaces at 3 days
  [ ] "watch X for me" creates watch, checks every 15 min
  [ ] proactive skill suggestions appear after pattern detection
  [ ] multi-turn meeting setup completes end to end
  [ ] weekly retrospective email sends Sunday 6PM Brisbane
  [ ] skill webhook output fires correctly
  [ ] Stripe Connect OAuth connects user's own invoices

Product score after Session 7: 8.5/10
Next: Session 8 — iOS app

END OF AXIS SESSION 7 PLAN
