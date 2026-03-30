# AXIS — Full Build Checklist
## Every task, every file, every integration. Do not summarise.
### Last updated: Session 5 · March 2026

Legend: ✅ Done · ⬜ Not started · 🔄 In progress · 🚫 Blocked (needs prior step)

---

## PART 1 — COMPLETED (Sessions 1–5)

### 1.1 Backend Infrastructure
- ✅ FastAPI project scaffolded and deployed to Railway
- ✅ Neon Postgres connected with async SQLAlchemy (asyncpg driver)
- ✅ `database.py` — async_session factory, engine, Base declarative
- ✅ `main.py` — FastAPI app, lifespan handler, CORS middleware
- ✅ CORS configured for Vercel frontend + localhost:5173
- ✅ Clerk JWT authentication middleware working
- ✅ `services/auth_service.py` — verify_clerk_token(), decode JWKS
- ✅ CLERK_JWKS_URL set in Railway environment variables
- ✅ User upsert on first authenticated request — creates row if clerk_id not found
- ✅ GET /health — returns `{"status": "ok"}` for Railway health checks
- ✅ Railway auto-deploy on git push to main branch
- ✅ APScheduler (AsyncIOScheduler) running inside FastAPI lifespan
- ✅ Dispatch job added to scheduler — interval 15 minutes
- ✅ Digest job added to scheduler — interval 15 minutes, time-gated internally
- ✅ Debug endpoint `/debug/config` removed (was leaking env var names)
- ✅ nixpacks.toml configured for correct Python build on Railway
- ✅ `$PORT` expansion working — Railway assigns port dynamically
- ✅ Dockerfile CMD uses exec form (not shell form) to avoid signal handling issues
- ✅ All sensitive credentials stored in Railway Variables, never in code
- ✅ `.gitignore` excludes `.env`, `__pycache__`, `.pyc`

### 1.2 Database — Neon Postgres Tables
- ✅ `users` table — id, clerk_id, email, name, plan, mode, timezone, apns_token, created_at
- ✅ `users` — gmail_access_token column added via ALTER TABLE
- ✅ `users` — gmail_refresh_token column added
- ✅ `users` — gmail_token_expiry column added
- ✅ `users` — gmail_connected boolean column added
- ✅ `users` — last_dispatch_run timestamp column added
- ✅ `thread_messages` table — id, user_id, role, content, message_type, source_skill, created_at
- ✅ `tasks` table — id, user_id, title, description, priority, category, is_done, due_date, created_at
- ✅ `team_signals` table — for team plan signal sharing
- ✅ `agent_activity` table — logs every agent run with status and timing
- ✅ `user_model` table — user_id, voice_patterns (JSONB), relationship_graph (JSONB), productive_windows (JSONB), defer_patterns (JSONB), updated_at
- ✅ `interactions` table — id, user_id, surface, content_type, action_taken, response_time_ms, skill_id, health_context, created_at
- ✅ `relationship_graph` table — user_id, contact_email, contact_name, importance_score, avg_reply_time_hrs, last_interaction, interaction_count
- ✅ `patterns` table — user_id, pattern_type, pattern_data (JSONB), confidence, computed_at
- ✅ `sent_emails_cache` table — user_id, to_email, subject, body_snippet, sent_at (voice model training data)
- ✅ `collective_patterns` table — anonymised cross-user patterns (no PII)
- ✅ All tables created via SQLAlchemy ORM with async engine
- ✅ Neon schema migrations run via asyncpg execute() on startup where needed

### 1.3 Gmail OAuth
- ✅ Google Cloud project created
- ✅ Gmail API enabled in Google Cloud console
- ✅ OAuth consent screen configured — external, test mode
- ✅ Test user added to OAuth consent screen (Hendre's Google account)
- ✅ OAuth client credentials created — Client ID and Secret
- ✅ GOOGLE_CLIENT_ID set in Railway Variables
- ✅ GOOGLE_CLIENT_SECRET set in Railway Variables
- ✅ GOOGLE_REDIRECT_URI set — `https://web-production-32f5d.up.railway.app/auth/gmail/callback`
- ✅ FRONTEND_URL set in Railway — `https://axis-web-chi.vercel.app` for post-OAuth redirect
- ✅ `routes/gmail.py` — GET /auth/gmail redirects to Google consent URL with clerk_id in state param
- ✅ `routes/gmail.py` — GET /auth/gmail/callback exchanges code for tokens, stores in users table, sets gmail_connected=True, redirects to frontend
- ✅ `services/gmail_service.py` — fetch_new_emails(user, since) returns list of email dicts
- ✅ Token refresh logic — checks expiry before each Gmail API call, refreshes if needed
- ✅ Gmail read working end to end — real inbox fetched in dispatch job
- ✅ Connect Gmail button in Settings screen calls correct OAuth URL

### 1.4 Intelligence Loop
- ✅ `services/dispatch.py` — main 15-minute loop, pulls Gmail, calls Claude, routes outputs
- ✅ `services/claude_service.py` — generate(system_prompt, user_message) wrapper around Anthropic API
- ✅ `services/morning_digest.py` — fires only between 6:45–7:00AM user local time, uses user.timezone
- ✅ `prompts/thread_system.py` — Axis character prompt, stays in role, ends with action not dismissal
- ✅ `prompts/brain_dump.py` — extracts and ranks tasks from free-form text input
- ✅ Morning digest prompt — overnight emails + tasks + signals, max 4 messages, ends with "your move: [specific action]"
- ✅ Dispatch reads user.last_dispatch_run and only fetches emails since that timestamp
- ✅ Dispatch updates user.last_dispatch_run after each run
- ✅ Thread messages saved to database after each dispatch run
- ✅ POST /cron/dispatch — manual trigger, auth-gated, for testing
- ✅ POST /cron/digest — manual trigger for morning digest
- ✅ ANTHROPIC_API_KEY set in Railway Variables
- ✅ Claude API calls use claude-sonnet-4-6 model

### 1.5 API Routes
- ✅ `routes/auth.py` — POST /auth/me — upsert user on login
- ✅ `routes/me.py` — GET /me (returns user profile + connections), PATCH /me (updates mode, timezone, name)
- ✅ `routes/thread.py` — GET /thread/messages (paginated), POST /thread/message (user sends, Axis responds)
- ✅ `routes/brain_dump.py` — POST /brain-dump (submit text), GET /brain-dump/usage (count + limit + is_pro)
- ✅ `routes/signals.py` — GET /signals (active tasks), PATCH /signals/:id (mark done, defer, snooze)
- ✅ `routes/brief.py` — GET /brief (today's digest messages), POST /brief/generate (trigger generation)
- ✅ `routes/push.py` — POST /push/register (store APNs device token)
- ✅ `routes/cron.py` — POST /cron/dispatch, POST /cron/digest (manual triggers)
- ✅ Brain dump logs interaction row after each submission (feeds usage counter and training data)
- ✅ Brain dump usage counter uses naive datetime comparison (UTC, no timezone issues)
- ✅ 24-hour rolling window for free usage count

### 1.6 Stripe Paywall
- ✅ Stripe account created, test mode configured
- ✅ Pro subscription product created — $9/month recurring
- ✅ STRIPE_SECRET_KEY (sk_test_...) set in Railway Variables
- ✅ STRIPE_PRICE_ID set in Railway Variables
- ✅ STRIPE_WEBHOOK_SECRET set in Railway Variables
- ✅ `routes/billing.py` — POST /billing/checkout creates Stripe Checkout session, returns URL
- ✅ `routes/billing.py` — POST /webhooks/stripe verifies webhook signature, sets user.plan='pro' on checkout.session.completed
- ✅ Webhook endpoint NOT behind Clerk auth (Stripe must reach it without JWT)
- ✅ Stripe test payment flow completed — test card 4242 4242 4242 4242
- ✅ Webhook fires correctly, user upgraded to Pro in database
- ✅ VITE_STRIPE_PUBLISHABLE_KEY set in Vercel environment variables
- ✅ ProGate modal shows after 3rd free brain dump
- ✅ ProGate modal lists Pro features, has Upgrade button that opens Stripe Checkout

### 1.7 Web Frontend — React + Vite + Tailwind on Vercel
- ✅ React + Vite project created and deployed to Vercel
- ✅ Tailwind CSS configured
- ✅ Vercel auto-deploy on push to main
- ✅ `vercel.json` — rewrites all paths to index.html for React Router SPA
- ✅ VITE_CLERK_PUBLISHABLE_KEY set in Vercel env vars
- ✅ VITE_API_URL set in Vercel env vars — points to Railway backend
- ✅ Clerk provider wrapping entire app in main.jsx
- ✅ SignedIn / SignedOut conditional rendering working
- ✅ UserButton component in navigation
- ✅ JWT token fetched via `useAuth().getToken()` and sent in Authorization header on all API calls
- ✅ Clerk auth waits for `isLoaded` before making any API call (prevents NetworkError on page load)
- ✅ `src/components/Thread.jsx` — iMessage-style conversation, auto-scrolls to newest, sends POST /thread/message
- ✅ `src/components/BrainDump.jsx` — textarea, submit button, stacks results, persists to localStorage with date expiry, shows usage counter fetched from backend
- ✅ `src/components/Signal.jsx` — active tasks list fetched from /signals
- ✅ `src/components/Skills.jsx` — 6 skill cards (Email, Calendar, Finance, Site, Study, Team)
- ✅ `src/components/Brief.jsx` — Generate Brief button, fetches digest messages, strips JSON markdown fences, renders as clean paragraphs
- ✅ `src/components/Settings.jsx` — profile display, Connect Gmail button (links to /auth/gmail), connections status list
- ✅ `src/components/ModeSwitcher.jsx` — Personal / Work / Builder / Student / Founder tabs, sends PATCH /me on change
- ✅ Navigation bar with all 6 screens
- ✅ Brief screen fixed — was rendering raw JSON, now strips ` ```json ` fences and renders text

---

## PART 2 — SESSION 6 (Build now — orchestration backbone)

### 2.1 Database — New Tables
- ⬜ Add `skills` table to `models.py`
  - id (UUID, primary key)
  - user_id (UUID, foreign key → users.id)
  - name (TEXT, not null)
  - description (TEXT)
  - is_builtin (BOOLEAN, default FALSE)
  - is_active (BOOLEAN, default TRUE)
  - data_sources (JSONB, default '[]') — e.g. ["gmail", "calendar", "spotify"]
  - reasoning_model (TEXT, default 'claude') — claude|perplexity|grok|gemini_flash
  - trigger_type (TEXT, default 'dispatch') — dispatch|schedule|location|manual
  - trigger_config (JSONB, default '{}') — schedule cron, location coords etc
  - output_routing (TEXT, default 'thread') — push|thread|widget|digest|silent
  - system_prompt (TEXT) — the actual Claude/Perplexity/Grok system prompt for this skill
  - created_at, updated_at
- ⬜ Add `skill_executions` table to `models.py`
  - id (UUID, primary key)
  - skill_id (UUID, foreign key → skills.id)
  - user_id (UUID, foreign key → users.id)
  - input_context (JSONB) — full context passed to the model
  - output_result (TEXT) — raw model response
  - model_used (TEXT) — which model actually handled it
  - surface_delivered (TEXT) — where output was sent
  - user_action (TEXT) — sent|edited|dismissed|deferred|ignored
  - execution_time_ms (INTEGER)
  - created_at
- ⬜ Add `api_connections` table to `models.py`
  - id (UUID, primary key)
  - user_id (UUID, foreign key → users.id)
  - service (TEXT, not null) — gmail|calendar|spotify|stripe|slack|reddit|youtube|xero
  - access_token (TEXT, encrypted at rest)
  - refresh_token (TEXT, encrypted at rest)
  - token_expiry (TIMESTAMP)
  - is_connected (BOOLEAN, default FALSE)
  - scopes (JSONB, default '[]') — list of granted OAuth scopes
  - metadata (JSONB, default '{}') — service-specific data (e.g. Spotify user_id)
  - updated_at
  - UNIQUE constraint on (user_id, service)
- ⬜ Add `model_routes` table to `models.py`
  - id (UUID, primary key)
  - task_type (TEXT) — email_draft|research|entertainment|triage|video_summary|reasoning|bulk
  - model (TEXT) — claude|perplexity|grok|gemini_flash|gemini_pro|gpt5|deepseek
  - reasoning (TEXT) — why this model for this task
  - cost_per_1m_input (FLOAT)
  - is_active (BOOLEAN, default TRUE)
- ⬜ Run Neon migration — create all 4 new tables
- ⬜ Seed `model_routes` table with routing rules on startup (in lifespan)
- ⬜ Seed built-in skills for every new user on first login
  - Email Intelligence — data_sources=["gmail"], reasoning_model="claude", trigger_type="dispatch", output_routing="push"
  - Calendar Intelligence — data_sources=["calendar"], reasoning_model="claude", trigger_type="dispatch", output_routing="push"
  - Finance Intelligence — data_sources=["stripe"], reasoning_model="claude", trigger_type="dispatch", output_routing="push"
  - Research Intelligence — data_sources=[], reasoning_model="perplexity", trigger_type="manual", output_routing="thread"
  - Entertainment Intelligence — data_sources=["spotify"], reasoning_model="grok", trigger_type="dispatch", output_routing="digest"
  - Morning Brief — data_sources=["gmail","calendar","tasks"], reasoning_model="claude", trigger_type="schedule", trigger_config={"cron": "50 6 * * *"}, output_routing="push"
- ⬜ Update `routes/auth.py` — call seed_default_skills(user_id, db) when user is created for first time

### 2.2 Model Router
- ⬜ Create `services/model_router.py`
- ⬜ Implement `route_to_model(model: str, system: str, user_msg: str) -> str` — master routing function
- ⬜ Implement `call_perplexity(system, user_msg)` — POST to `api.perplexity.ai/chat/completions`, model `llama-3.1-sonar-large-128k-online`, returns content string
- ⬜ Implement `call_grok(system, user_msg)` — POST to `api.x.ai/v1/chat/completions`, model `grok-4.1-fast`, OpenAI-compatible format
- ⬜ Implement `call_gemini_flash(system, user_msg)` — POST to `generativelanguage.googleapis.com`, model `gemini-2.0-flash-lite`, parse `candidates[0].content.parts[0].text`
- ⬜ Implement `call_gemini_pro(system, user_msg)` — same endpoint, model `gemini-3.1-pro`
- ⬜ Implement `call_gpt5(system, user_msg)` — OpenAI SDK, model `gpt-5.4-turbo`, optional
- ⬜ Fallback to Claude if unknown model string passed
- ⬜ Add `PERPLEXITY_API_KEY` to Railway Variables
- ⬜ Add `GROK_API_KEY` to Railway Variables
- ⬜ Add `GEMINI_API_KEY` to Railway Variables
- ⬜ Add `OPENAI_API_KEY` to Railway Variables (optional, for GPT-5)
- ⬜ All API calls use `aiohttp.ClientSession` for async HTTP
- ⬜ Error handling — catch HTTP errors, log to agent_activity, fallback to Claude on failure
- ⬜ Add response time logging to agent_activity for each model call

### 2.3 Triage Service
- ⬜ Create `services/triage_service.py`
- ⬜ Implement `triage_items(items: list, user_profile: dict) -> dict` — classifies all items before expensive processing
- ⬜ Build triage prompt — asks Gemini Flash-Lite to score each item 1–10 against user profile, returns JSON array
- ⬜ Implement `parse_triage_result(raw: str) -> list` — extracts JSON array from Gemini response, handles malformed JSON gracefully
- ⬜ Default score for unparseable items: 3 (noise, discarded)
- ⬜ Return structure: `{"urgent": [...], "relevant": [...], "noise": [...]}` — urgent is 7+, relevant is 4–6, noise is below 4
- ⬜ Wire `triage_service` into `dispatch.py` — all items triaged before any Claude call
- ⬜ Log count of discarded noise items to agent_activity per dispatch run
- ⬜ Log count of urgent and relevant items separately

### 2.4 Signal Filter
- ⬜ Create `services/signal_filter.py`
- ⬜ Implement Filter 1 — relevance check against user_model interest profile
- ⬜ Implement Filter 2 — urgency scoring cross-check (second pass after triage)
- ⬜ Implement Filter 3 — context check: calendar events in next 48hrs, current location, current mode
- ⬜ Implement Filter 4 — deduplication: hash each item by source+topic+summary, check against 24hr seen-items store (Postgres or in-memory)
- ⬜ Implement Filter 5 — apprentice filter: read user_model.defer_patterns, reduce score by 50% for topics with 8+ consecutive dismissals
- ⬜ Create `seen_items` table or Redis key for deduplication window
- ⬜ Wire signal_filter into orchestrator — apply after triage, before model calls

### 2.5 Gmail SEND
- ⬜ Update Gmail OAuth `SCOPES` list in `routes/gmail.py` — add `https://www.googleapis.com/auth/gmail.send`
- ⬜ Note: users who already connected Gmail will need to re-authorise to grant send scope
- ⬜ Create `services/gmail_send.py`
- ⬜ Implement `send_email_draft(user, to: str, subject: str, body: str, thread_id: str = None)`
  - Build `MIMEText` message with correct headers
  - Set `References` and `In-Reply-To` headers when replying to thread
  - base64 urlsafe encode the MIME message
  - Call `gmail_service.users().messages().send(userId='me', body={'raw': raw, 'threadId': thread_id})`
- ⬜ Create `POST /gmail/send` endpoint in `routes/gmail.py`
  - Requires auth (Clerk JWT)
  - Accepts `{to, subject, body, thread_id}` request body
  - Calls `gmail_send.send_email_draft()`
  - Logs to interactions table with action_taken="sent", surface="gmail_send"
  - Returns `{"success": true, "message_id": "..."}`
- ⬜ Create `prompts/email_draft.py` — voice-matched email draft prompt
  - Injects `voice_patterns` from user_model
  - Injects relationship_graph score and formality level for the specific recipient
  - Injects 3 example past replies to similar emails from sent_emails_cache
  - Injects full email thread context being replied to
  - Specifies target word count based on voice_patterns.avg_reply_length
  - Output: draft text only, no preamble, no explanation, no sign-off unless voice model uses one
- ⬜ Update dispatch to generate email drafts for high-urgency emails (urgency score 8+)
  - action_type: "draft_email" in dispatch output JSON
  - Draft text stored in `pre_prepared_action` field
  - Draft_id stored so frontend can reference it
- ⬜ Add `[Send]` action button to thread messages that have `message_type="email_draft"`
  - Calls POST /gmail/send with the draft content
  - Shows sending spinner, then confirmation
- ⬜ Add `[Edit]` action button — opens edit modal, user modifies draft, then sends
- ⬜ Add `[Dismiss]` button — marks draft as dismissed, logs to interactions

### 2.6 Google Calendar OAuth
- ⬜ Add `https://www.googleapis.com/auth/calendar.readonly` and `https://www.googleapis.com/auth/calendar.events` scopes to Google Cloud project
- ⬜ Create `routes/calendar.py`
- ⬜ Implement `GET /auth/calendar` — redirects to Google consent URL with calendar scopes
- ⬜ Implement `GET /auth/calendar/callback` — exchanges code, stores tokens in api_connections table with service="google_calendar"
- ⬜ Add `calendar_connected` boolean check in `GET /me` response
- ⬜ Add Connect Calendar button to Settings screen
- ⬜ Create `services/calendar_service.py`
- ⬜ Implement `fetch_upcoming_events(user, days=2)` — returns events with title, start_time, end_time, attendee_emails, attendee_names, location, description, hangout_link
- ⬜ Implement `detect_conflicts(events: list)` — returns pairs of overlapping events
- ⬜ Implement `calculate_travel_time(from_location, to_location)` — uses Google Maps API or hardcoded buffer if no maps key
- ⬜ Wire calendar data into dispatch context so emails about meetings are cross-referenced
- ⬜ Create `services/meeting_prep.py`
  - Runs every 5 minutes via APScheduler
  - Checks for events starting in 25–35 minutes (the 30-min pre-meeting window)
  - For each event: fetches attendee emails, pulls recent thread messages with those people, calls Perplexity for attendee background research, calls Claude with meeting prep prompt
  - Sends push notification with prep brief
  - Logs to skill_executions with skill_id=calendar_intelligence_skill_id
- ⬜ Create `prompts/meeting_prep.py`
  - 3 bullet brief, each under 15 words
  - One suggested talking point
  - One risk flag if present
  - Based on recent emails with attendees + Perplexity background — NOT generic advice
  - Total output under 80 words

### 2.7 Skills Framework (replaces monolithic dispatch)
- ⬜ Create `routes/skills.py`
  - GET /skills — returns all active skills for authenticated user (builtin + custom)
  - POST /skills — creates a new custom skill (Pro users only)
  - GET /skills/:id — returns single skill detail
  - PATCH /skills/:id — update skill config (name, description, data_sources, reasoning_model, trigger_type, output_routing, system_prompt)
  - DELETE /skills/:id — delete custom skill (cannot delete builtin skills)
  - POST /skills/:id/run — manually trigger a skill, returns result to thread
- ⬜ Create `services/orchestrator.py`
  - `run_active_skills(user, context, db)` — fetches active skills for user, runs all in parallel via asyncio.gather
  - `run_skill(skill, context)` — filters context to data sources needed by skill, builds skill prompt, calls model_router, parses result
  - `filter_context_for_skill(skill, context)` — returns only the context data the skill's data_sources require (Gmail data for email skill, calendar data for calendar skill etc)
  - `build_skill_prompt(skill, relevant_data)` — combines skill.system_prompt with relevant context data
  - `parse_skill_result(raw_result, skill)` — extracts structured routing decision from model response
- ⬜ Create `services/context_assembler.py`
  - `assemble_context(user, new_data, db)` — builds complete context object
  - Includes: user.name, user.mode, user.timezone, current_time_local
  - Includes: new_data (Gmail, calendar, Stripe, Spotify etc)
  - Includes: user_model (voice_patterns, relationship_graph, productive_windows, defer_patterns)
  - Includes: recent_thread (last 10 messages from thread_messages table)
  - Includes: health_snapshot (sleep_hrs, sleep_quality, hrv — from last POST /health/snapshot)
  - Includes: today_events (next 24hrs from calendar)
  - Returns as single Python dict
- ⬜ Create `services/output_router.py`
  - `route_result(result_items: list, user, db)` — reads surface field per item, dispatches correctly
  - surface="push" → `push_service.send_push(user.apns_token, title, body, actions)`
  - surface="thread" → `save_thread_message(user.id, content, role="assistant", message_type=item.type, db)`
  - surface="widget" → update widget cache in Postgres/Redis
  - surface="digest" → append to today's digest queue
  - surface="silent" → log to interactions only, nothing shown to user
  - action_type="send_email" → call `gmail_send.send_email_draft()` immediately (auto-send) or set action_available=True on push (user approves)
  - action_type="create_event" → call calendar_service.create_event() (future)
  - All routes log to interactions table regardless of surface
- ⬜ Create `prompts/dispatch_v2.py` — skills-aware dispatch prompt
  - Injects user.mode, location, local_time, health context (sleep, HRV)
  - Injects user_model summary (voice, top contacts, productive windows, defer patterns)
  - Injects list of active skill names and their configs
  - Injects new_data structured by source
  - Returns JSON array — one object per actionable item with: urgency (1–10), actionable (bool), surface (push|thread|widget|digest|silent), action_type (send_reply|create_task|send_invoice_reminder|research|none), pre_prepared_action (draft text or task text), model_to_use (claude|perplexity|grok), skill_id (which skill this belongs to), reason (one sentence)
- ⬜ Refactor `services/dispatch.py` — replace monolithic Claude call with orchestrator.run_active_skills()
- ⬜ Wire orchestrator into APScheduler 15-minute job

### 2.8 Perplexity Integration
- ⬜ Create `services/perplexity_service.py`
- ⬜ Implement `research(query: str, user_context: dict) -> str` — posts to Perplexity sonar-pro, contextualises to user's mode and location, returns synthesis with citations
- ⬜ Implement `research_person(name: str, company: str) -> str` — structured person/company background lookup for meeting prep
- ⬜ Create `prompts/research.py` — Perplexity system prompt
  - Contextualises to user's mode, location, active projects
  - Returns actionable summary not raw facts
  - Includes citations inline
  - Under 200 words unless user asked for deep research
- ⬜ Wire Research Intelligence skill to use perplexity_service via model_router
- ⬜ Wire meeting prep to use research_person() for attendee background

### 2.9 Grok Integration
- ⬜ Create `services/grok_service.py`
- ⬜ Implement `entertainment_brief(user_taste: dict) -> str` — calls Grok API with user's music/social interest profile, returns top 3 entertainment items worth surfacing today
- ⬜ Implement `social_trends(topics: list) -> str` — gets X/Twitter sentiment and trending content on user's followed topics
- ⬜ Implement `breaking_news(interests: list) -> str` — surfaces breaking news relevant to user's interest profile
- ⬜ Wire Entertainment Intelligence skill to use grok_service via model_router
- ⬜ Include Grok entertainment brief in morning digest assembly

### 2.10 Apprentice — Weekly Improvement
- ⬜ Create `services/apprentice.py`
- ⬜ Implement `run_improvement_cycle(user, db)` — full weekly learning loop
  - Pulls all interactions from last 7 days for this user
  - Computes `accuracy_by_skill` — for each skill, what % of push notifications did user act on vs dismiss
  - Computes `response_times_by_hour` — when does user respond fastest (identifies productive windows)
  - Computes `most_deferred_categories` — what types of tasks are consistently put off
  - Pulls last 20 sent emails from sent_emails_cache
  - Calls Claude with apprentice prompt + all data
  - Saves updated user_model back to database
- ⬜ Create `prompts/apprentice.py` — user model update prompt
  - Analyses week data with evidence, not generalisations
  - Identifies specific changes to voice_patterns (new phrases observed, formality shifts)
  - Updates relationship_graph scores based on response behaviours
  - Updates productive_windows based on interaction timing
  - Updates defer_patterns based on dismissal patterns
  - Returns full updated user_model JSON
  - Also returns plain-English explanation of what changed (for Apprentice dashboard)
- ⬜ Create `services/voice_model.py`
- ⬜ Implement `rebuild_voice_model(user, db)` — Sunday 4AM job
  - Fetches last 50 sent emails from Gmail API (not cache) — most recent real sent mail
  - Groups emails by recipient type (client, supplier, friend, colleague) using relationship_graph
  - Analyses per group: avg sentence length, formality score 1–10, common opening phrases, common closing phrases, sign-off style, emoji usage, punctuation style
  - Calls Claude to synthesise patterns into voice_patterns JSON structure
  - Updates user_model.voice_patterns in database
- ⬜ Wire apprentice and voice model jobs into APScheduler in `main.py`
  - Sunday 3AM UTC: improvement cycle for all Pro users
  - Sunday 4AM UTC: voice model rebuild for all Pro users with Gmail connected
  - Sunday 5AM UTC: collective patterns update (anonymised cross-user)

---

## PART 3 — SESSION 7 (Entertainment + lifestyle layer)

### 3.1 YouTube Integration
- ⬜ Create `services/youtube_service.py`
- ⬜ Enable YouTube Data API v3 in Google Cloud project
- ⬜ Implement `get_new_videos(user, hours=24) -> list` — OAuth, fetches videos from subscribed channels uploaded in last 24hrs, returns id + title + description + duration_seconds + channel_name + published_at
- ⬜ Implement `get_subscription_list(user) -> list` — returns user's YouTube channel subscriptions
- ⬜ Implement `gemini_video_summary(video_url: str, user_context: str) -> str` — passes YouTube URL to Gemini API for native video processing, returns 3-bullet summary under 20 words each
- ⬜ Add YouTube OAuth — GET /auth/youtube and /auth/youtube/callback
  - Scope: `https://www.googleapis.com/auth/youtube.readonly`
  - Store tokens in api_connections (service="youtube")
- ⬜ Add Connect YouTube button in Settings screen
- ⬜ Add YouTube as data source option in Entertainment Intelligence skill
- ⬜ Wire YouTube new videos into dispatch context for entertainment triage
- ⬜ Build "viewed channel" tracker — when user taps through to YouTube, log that channel as high-engagement

### 3.2 Spotify Integration
- ⬜ Create Spotify Developer app at developer.spotify.com
- ⬜ Create `services/spotify_service.py`
- ⬜ Implement `get_new_releases(user) -> list` — OAuth, fetches new releases from artists user follows, last 7 days, returns id + name + artist + type (album/single/EP) + release_date + spotify_url
- ⬜ Implement `get_listening_history(user, limit=50) -> list` — returns recently played tracks with played_at timestamp
- ⬜ Implement `get_followed_artists(user) -> list` — full list of followed artists
- ⬜ Add Spotify OAuth — GET /auth/spotify and /auth/spotify/callback
  - Scopes: `user-read-recently-played user-follow-read user-library-read user-top-read`
  - Store tokens in api_connections (service="spotify")
- ⬜ Add Connect Spotify button in Settings screen
- ⬜ Build `build_taste_profile(user, db)` — runs weekly, analyses top artists and genres from listening history, stores in user_model (new music_preferences key in JSONB)
- ⬜ Wire Spotify new releases into entertainment brief via Grok cross-check
- ⬜ Wire Spotify into morning digest — "Hozier dropped a live session at midnight" when followed artist releases

### 3.3 Reddit Integration
- ⬜ Create Reddit app at reddit.com/prefs/apps
- ⬜ Create `services/reddit_service.py`
- ⬜ Implement `get_community_posts(user, min_score=100, hours=24) -> list` — OAuth, fetches top posts from user's subscribed subreddits, filtered to communities user actually posts/comments in
- ⬜ Implement `get_subscribed_communities(user) -> list` — returns all subscribed subreddits
- ⬜ Implement `get_engagement_history(user) -> dict` — maps subreddit → number of posts/comments user has made (determines which subs are active vs lurk-only)
- ⬜ Add Reddit OAuth — GET /auth/reddit and /auth/reddit/callback
  - Scope: `read identity`
  - Store tokens in api_connections (service="reddit")
- ⬜ Add Connect Reddit button in Settings screen
- ⬜ Build community engagement weight system — active subs (user posts) get 3× weight vs lurk-only subs
- ⬜ Claude summarises Reddit thread — title + top 3 comments → "r/construction has a viral thread: [2-sentence summary]. 847 upvotes."
- ⬜ Wire Reddit into entertainment/knowledge brief based on user mode (Builder mode surfaces construction subreddits, Founder mode surfaces startup subreddits)

### 3.4 Hacker News Integration
- ⬜ Create `services/hackernews_service.py`
- ⬜ Implement `get_top_stories(min_score=200, limit=10) -> list` — no auth needed, uses HN Algolia API (`hn.algolia.com/api/v1/search`)
- ⬜ Implement `get_ask_hn(limit=5) -> list` — Ask HN posts relevant to founder/builder modes
- ⬜ Implement `filter_by_mode(stories: list, user_mode: str) -> list` — Builder/Founder see startup + tech + tools. Student sees learning resources. Work mode sees industry news.
- ⬜ Add HN as optional data source in Research Intelligence and Morning Brief skills
- ⬜ No OAuth needed — public API

### 3.5 Product Hunt Integration
- ⬜ Create `services/producthunt_service.py`
- ⬜ Get Product Hunt API key
- ⬜ Implement `get_daily_launches(categories: list) -> list` — PH GraphQL API, today's top launches in specified categories
- ⬜ Implement `filter_by_user_context(launches: list, user: dict) -> list` — only surfaces products relevant to user's mode and industry
- ⬜ Only active for Founder and Builder modes
- ⬜ Add PH as optional data source in Morning Brief skill

### 3.6 News Aggregation
- ⬜ Get Google News API key
- ⬜ Create `services/news_service.py`
- ⬜ Implement `get_relevant_news(user, topics: list) -> list` — Google News API, filtered by user's topics of interest, last 24hrs, returns title + source + url + snippet
- ⬜ Implement `get_industry_news(industry: str) -> list` — news relevant to user's detected industry (from mode + email content analysis)
- ⬜ Build topic interest profile from interactions — what news stories user has clicked → extract topics → weight future news higher from those topics
- ⬜ Perplexity synthesises competing news sources — same event from 3 sources → one 2-sentence summary with best source linked
- ⬜ Add news as data source in Morning Brief skill
- ⬜ Deduplication across news + Reddit + X covering the same story

### 3.7 Stripe Finance Intelligence (user's own Stripe — different from billing Stripe)
- ⬜ Create `services/stripe_service.py` — NOTE: this is for the USER's Stripe account, separate from the Axis billing Stripe
- ⬜ Add Stripe Connect OAuth — allows user to connect their own Stripe account
- ⬜ Implement `get_overdue_invoices(user) -> list` — invoices past due_date, returns amount + client_name + days_overdue + invoice_url
- ⬜ Implement `get_cash_flow_summary(user) -> dict` — monthly revenue and expenses
- ⬜ Add Connect Stripe (Business) in Settings screen — clearly labelled as "for your own invoices"
- ⬜ Invoice reminder feature: dispatch checks overdue invoices every 15 min, invoices 7+ days overdue trigger Claude draft using voice model, push notification with [Send] button
- ⬜ Add Xero OAuth as alternative for non-Stripe businesses

### 3.8 Apprentice Visibility Dashboard
- ⬜ Create `GET /apprentice` endpoint in new `routes/apprentice.py`
  - Returns human-readable version of user_model
  - voice_insights: list of plain-English observations about how user writes
  - time_patterns: when user is most productive, when they respond fastest
  - relationship_insights: observations about key contacts ("You reply to Marcus within 1 hour on average")
  - attention_patterns: what notifications user acts on vs ignores
  - learned_this_week: what changed in the most recent improvement cycle
- ⬜ Create `src/components/Apprentice.jsx` — new screen in React web app
  - Cards for each insight category
  - Weekly learning summary
  - "Axis learned X" statements
  - Correction interface — "Mark this as wrong" per insight
  - Confidence level indicator per pattern
- ⬜ Add Apprentice to nav and routes
- ⬜ Create `PATCH /apprentice/correct` endpoint
  - Accepts {pattern_type, pattern_key, correction}
  - Marks pattern as user-corrected in user_model
  - Feeds correction back into next improvement cycle

### 3.9 Skill Builder UI
- ⬜ Add "Create Skill" button to Skills screen
- ⬜ Build skill creator flow in `src/components/Skills.jsx`
  - Step 1: Name the skill (text input)
  - Step 2: Choose trigger (schedule / location / manual / on new data)
  - Step 3: Choose data sources (checkboxes: Gmail, Calendar, Spotify, Reddit, news, Stripe, YouTube, Hacker News)
  - Step 4: Describe what the skill should do (textarea — plain language)
  - Step 5: Choose output surface (push notification / thread message / widget / digest / silent)
  - Step 6: Preview the generated system prompt (read-only)
  - Save button → POST /skills
- ⬜ Create `POST /skills/generate-prompt` endpoint
  - Accepts user's plain-language skill description + selected data sources + output routing
  - Calls Claude to generate a proper system_prompt from the description
  - Returns generated prompt for preview before saving to database
- ⬜ Skill cards on Skills screen show: last run time, model used, action count this week, toggle to enable/disable

---

## PART 4 — SESSION 8 (iOS app)

### 4.1 Xcode Project Setup
- ⬜ Create Xcode project — AxisApp, SwiftUI lifecycle, iOS 17 minimum deployment target
- ⬜ Set bundle ID — com.dreyco.axis
- ⬜ Configure Apple Developer account — certificates, provisioning profiles
- ⬜ Add Swift Package dependencies: Clerk iOS SDK
- ⬜ Add Swift Package dependencies: RevenueCat (Purchases)
- ⬜ Load all 5 AXIS context files into repo root as reference for Cursor
- ⬜ Create `.cursorrules` file — describes Axis architecture for Cursor AI assistance
- ⬜ Create `APIService.swift` — centralised API layer with auth header injection
  - `baseURL = "https://web-production-32f5d.up.railway.app"`
  - `getToken()` — fetches JWT from Clerk iOS SDK
  - Generic `request<T: Decodable>()` method for all endpoints

### 4.2 Authentication
- ⬜ Sign in with Apple — primary auth
  - `ASAuthorizationAppleIDProvider`
  - `ASAuthorizationController` with presentation context
  - Exchange Apple identity token for Clerk session JWT
  - Store JWT securely in Keychain (never UserDefaults)
- ⬜ Clerk iOS SDK integration
  - `ClerkProvider` wrapping app root
  - `Clerk.shared.session?.getToken()` for all API calls
  - Auto-refresh expired tokens
  - Sign out clears Keychain
- ⬜ Auth state observation — `@StateObject` observing Clerk session changes
- ⬜ Unauthenticated users see onboarding/sign-in screen
- ⬜ `KeychainService.swift` — save/load/delete JWT token

### 4.3 Core Screens — SwiftUI
- ⬜ `ThreadView.swift` — iMessage-style persistent conversation
  - Fetch `GET /thread/messages` on appear
  - ScrollView with LazyVStack of message bubbles
  - Auto-scroll to newest message
  - Text input field + send button
  - POST /thread/message on send
  - Axis messages: left-aligned, user messages: right-aligned
  - Show message_type indicator for email drafts (different bubble style)
  - Action buttons on email draft messages: [Send] [Edit] [Dismiss]
  - Pull to load older messages (pagination)
- ⬜ `SignalView.swift` — current signal + task queue
  - Large hero card showing current top signal (urgency, title, category)
  - Task list below sorted by urgency
  - Swipe left to dismiss
  - Swipe right to defer 2 hours
  - Tap to mark done
  - Pull to refresh
  - Empty state: "Nothing urgent right now."
- ⬜ `BrainDumpView.swift` — voice + text capture
  - Large text area
  - Microphone button — starts `SFSpeechRecognizer` dictation
  - Live transcription shown in text area
  - Submit button — POST /brain-dump
  - Results display: ranked task list
  - Usage counter (X/3 today) fetched from GET /brain-dump/usage
  - Paywall modal after 3rd dump if not Pro
- ⬜ `SkillsView.swift` — skill management
  - LazyVGrid of skill cards
  - Each card: skill name, model badge, last run time, active toggle
  - Tap to open skill detail sheet
  - Skill detail: description, data sources, output routing, recent executions
  - FAB (+) to create custom skill
  - Custom skill creator sheet
- ⬜ `BriefView.swift` — daily brief
  - Date header
  - Generate Brief button if not yet generated today
  - Message list from GET /brief
  - Formatted text rendering (markdown-ish)
- ⬜ `SettingsView.swift` — connections + preferences
  - Connected accounts list: Gmail ✓, Calendar, Spotify, YouTube, Reddit, Stripe
  - Connect/Disconnect per service
  - Mode picker (Personal/Work/Builder/Student/Founder)
  - Notification preferences
  - Plan status + Upgrade button (if free)
  - Sign out button
- ⬜ `ApprenticeView.swift` — what Axis learned
  - Fetches GET /apprentice
  - Cards per insight category
  - Weekly learning summary
  - Correction interface
- ⬜ `AppContentView.swift` — tab bar root
  - TabView with: Signal, Thread, BrainDump, Skills, Settings
  - Tab icons + labels
  - Badge on Signal tab showing urgency count

### 4.4 WidgetKit
- ⬜ Create `AxisWidgetExtension` target in Xcode
- ⬜ Create `SignalWidget.swift`
  - Supports `.accessoryCircular`, `.accessoryRectangular` (lock screen), `.systemMedium` (home screen)
  - Fetches `GET /widget/signal` with stored user JWT
  - Displays: urgency indicator, signal title, category label
  - Interactive buttons: [Done] [Snooze] using App Intents (iOS 17+)
  - `TimelineProvider` with 15-minute refresh policy
- ⬜ Create `GET /widget/signal` endpoint in `routes/signals.py`
  - Returns: signal_title, signal_category, urgency_score, action_available, action_type
  - Must be very lightweight — widget budget is limited
- ⬜ Create `TodayWidget.swift` — summary widget
  - `.systemSmall` and `.systemMedium`
  - Shows: tasks_due_today count, next event title + time, one key signal
- ⬜ Share JWT between main app and widget via App Group UserDefaults
  - Create App Group: `group.com.dreyco.axis`
  - Store JWT in shared UserDefaults (not Keychain — widgets can't access Keychain)
  - Main app writes token on login, widget reads it for API calls
- ⬜ Widget timeline reload triggered on app foreground via `WidgetCenter.shared.reloadAllTimelines()`

### 4.5 App Intents — Siri + Shortcuts
- ⬜ Create `AxisIntents.swift` with `AppShortcutsProvider`
- ⬜ `AddToAxisIntent` — "Hey Siri, add to Axis: [text]"
  - `@Parameter var text: String`
  - Calls `POST /brain-dump`
  - Returns `"Added to Axis. [N] tasks extracted."`
  - Register phrase: "Add to Axis [text]"
- ⬜ `GetSignalIntent` — "Hey Siri, what's my Axis signal?"
  - Calls `GET /widget/signal`
  - Returns spoken: "Your current signal is [title]. Urgency [N] out of 10."
  - Register phrase: "What's my Axis signal", "Show my Axis signal"
- ⬜ `MarkDoneIntent` — "Hey Siri, mark my Axis signal done"
  - Calls `PATCH /signals/:id` with is_done=true for top signal
  - Returns: "Done. Your next signal is [next_title]."
  - Also used as widget button action
  - Register phrase: "Mark Axis signal done", "Done in Axis"
- ⬜ `SnoozeSignalIntent` — "Hey Siri, snooze my Axis signal"
  - Calls `PATCH /signals/:id` with snooze_until = now + 2 hours
  - Returns: "Snoozed for 2 hours."
  - Also used as widget button action
- ⬜ `BrainDumpIntent` — "Hey Siri, brain dump in Axis"
  - Opens app to BrainDump screen in listening mode
  - Or handles via Siri if no UI needed: uses `SFSpeechRecognizer` in background
- ⬜ `SetModeIntent` — "Hey Siri, switch Axis to Builder mode"
  - `@Parameter var mode: AxisMode` (enum: personal/work/builder/student/founder)
  - Calls `PATCH /me` with new mode
  - Returns: "Axis switched to Builder mode."
  - Register phrase: "Switch Axis to [mode] mode"
- ⬜ `GetBriefIntent` — "Hey Siri, what's in my Axis brief?"
  - Calls `GET /brief`
  - Reads first message as spoken response
  - Register phrase: "What's my Axis brief", "Read my Axis brief"
- ⬜ `SendEmailDraftIntent` — triggered from notification action button
  - Accepts draft_id parameter
  - Calls `POST /gmail/send`
  - Works from notification without opening app
- ⬜ Register all intents in `AppShortcutsProvider` with phrase variations
- ⬜ All intents work from lock screen without unlocking (where supported by iOS)

### 4.6 HealthKit
- ⬜ Create `HealthKitService.swift`
- ⬜ Request read authorization for:
  - `HKCategoryTypeIdentifierSleepAnalysis` — last night's sleep
  - `HKQuantityTypeIdentifierHeartRateVariabilitySDNN` — morning HRV
  - `HKQuantityTypeIdentifierStepCount` — activity level
  - `HKQuantityTypeIdentifierActiveEnergyBurned` — energy
- ⬜ Implement `getLastNightSleep() -> (hours: Double, quality: Double)` — reads HKCategoryValueSleepAnalysis, calculates total sleep and efficiency
- ⬜ Implement `getMorningHRV() -> Double?` — reads HRV from midnight to 9AM today
- ⬜ Implement `getDailySteps() -> Int` — today's step count
- ⬜ Create `POST /health/snapshot` endpoint in new `routes/health.py`
  - Accepts: sleep_hrs, sleep_quality (0–100), hrv, steps
  - Stores in user session context (ephemeral — used in next dispatch call)
  - Does NOT store in long-term database (health data stays on device except for aggregate metrics)
- ⬜ Call POST /health/snapshot on app open and each morning
- ⬜ Backend dispatch reads health_snapshot when assembling context — routes light tasks on bad sleep days

### 4.7 CoreLocation
- ⬜ Create `LocationService.swift`
- ⬜ Request `CLLocationManager` "When in Use" authorisation
- ⬜ Implement geofencing — `CLCircularRegion` per saved location
- ⬜ On `didEnterRegion` — call `PATCH /me` with the mode associated with that location
- ⬜ `SettingsView` — "Add this as a location" button when on Site/Work screen
  - Gets current GPS, prompts user for label + associated mode
  - Saves to `CLLocationManager` as monitored region
  - Also POST to new `POST /locations` backend endpoint for persistence
- ⬜ Background location permission NOT requested — only when-in-use (App Store compliance)
- ⬜ Geofence radius: 200 meters (enough for building/site detection)

### 4.8 Push Notifications (APNs)
- ⬜ `UNUserNotificationCenter.requestAuthorization` on first app open
- ⬜ Register for remote notifications — `UIApplication.shared.registerForRemoteNotifications()`
- ⬜ Send device token to `POST /push/register` on receipt
- ⬜ Handle `UNUserNotificationCenterDelegate` — `userNotificationCenter(_:didReceive:)`
- ⬜ Register notification categories with action buttons:
  - Category "email_draft": [Send Reply] [Edit] [Dismiss]
  - Category "task": [Mark Done] [Snooze 2hrs]
  - Category "signal": [View] [Dismiss]
  - Category "invoice": [Send Reminder] [Dismiss]
- ⬜ Deep link from notification tap — route to correct screen based on `deep_link` in payload
- ⬜ Handle [Send Reply] action — call POST /gmail/send with draft_id from notification payload, without opening app
- ⬜ Handle [Mark Done] action — call PATCH /signals/:id without opening app
- ⬜ Background notification handler — update badge count when new signal arrives

### 4.9 Control Centre Tile
- ⬜ Create `AxisControlWidget.swift` implementing `ControlWidget`
- ⬜ Tile shows Axis icon + current urgency count badge
- ⬜ Tap action: opens Axis overlay view OR runs `AddToAxisIntent` directly
- ⬜ Appears in Control Centre customisation panel
- ⬜ `AxisOverlayView.swift` — full-screen overlay
  - Shows current signal at top
  - Text input + microphone button
  - 3 quick actions: [Mark Done] [New Task] [Research]
  - Dismiss on swipe up or tap outside
  - Light blur background

### 4.10 RevenueCat + App Store Payments
- ⬜ Create $9/month Pro subscription product in App Store Connect
- ⬜ Create RevenueCat account, link to App Store app
- ⬜ Add RevenueCat SDK: `Purchases.configure(withAPIKey: "rc_...")`
- ⬜ Implement `PaywallView.swift` — shows after 3rd brain dump or blocked Pro feature
  - Lists Pro features
  - Monthly $9 price prominently
  - Restore Purchases button
  - Terms + Privacy links
- ⬜ `Purchases.shared.purchase(package:)` on subscribe tap
- ⬜ RevenueCat webhook → POST /webhooks/revenuecat → sets user.plan='pro' in backend
- ⬜ Check user.plan on app open — sync entitlements
- ⬜ Free tier limits enforced on device (brain dump counter) AND on server

### 4.11 TestFlight + App Store
- ⬜ Archive build and upload to App Store Connect
- ⬜ Internal testing — Hendre's device
- ⬜ External TestFlight — 500 beta user slots
- ⬜ Beta tester onboarding email via Resend
- ⬜ NPS survey link sent to TestFlight users at Day 7 — must be 40+ before public launch
- ⬜ App Store screenshots — all required sizes (6.7", 6.1", iPad if applicable)
- ⬜ App Store description — lead with "Be phone lazy. Be world productive."
- ⬜ Keywords optimisation — ambient AI, AI assistant, smart notifications, productivity
- ⬜ App Store submission — Privacy policy URL required, support URL required
- ⬜ App Review — ensure HealthKit usage description in Info.plist
- ⬜ App Review — ensure Location usage description in Info.plist
- ⬜ App Review — ensure all background modes declared
- ⬜ App Review — ensure no hidden features behind test accounts

---

## PART 5 — SESSION 9 (Revenue + Growth)

### 5.1 Landing Page
- ⬜ Domain — axis.app (or backup: useaxis.app)
- ⬜ Single page — hero, 3 features, 1 testimonial, app store badge
- ⬜ Hero line: "Be phone lazy. Be world productive."
- ⬜ Subheader: "The AI that reads your inbox, knows your day, and handles what it can — before you wake up."
- ⬜ 45-second screen recording demo embedded — shows brain dump → tasks, morning brief, email draft
- ⬜ Email capture for iOS waitlist
- ⬜ App Store badge linking to TestFlight (then production)
- ⬜ Mobile-first design — most traffic will come from iPhone
- ⬜ Deploy on Vercel (separate from web app)
- ⬜ PostHog snippet added for visitor tracking

### 5.2 Email Sequences — Resend
- ⬜ Welcome email — fires immediately on signup
  - Subject: "You're in. Here's what Axis does while you sleep."
  - Body: what Axis will do, one call to action: Connect Gmail
  - From: hendre@axis.app (custom domain)
- ⬜ Day 3 email — fires if gmail_connected is still FALSE
  - Subject: "Axis is smart. But it's smarter with your inbox."
  - Body: "Axis can read, rank, and draft replies to your emails. It takes 30 seconds to connect." Link to Settings.
- ⬜ Day 7 email — fires if user.plan is still 'free'
  - Subject: "Your first week with Axis"
  - Body: personalised stats — brain dump count, tasks extracted, signals surfaced, time saved estimate
  - CTA: Upgrade to Pro — $9/month
- ⬜ Day 14 email — fires if user has connected Gmail but not upgraded
  - Subject: "You've used Axis [N] times. Here's what Pro unlocks."
  - Specific to their usage pattern
- ⬜ Cancellation flow — email when plan cancelled: "We'll keep your data for 30 days."
- ⬜ All emails use Resend API with custom domain sending

### 5.3 Analytics
- ⬜ PostHog installed on React web app
- ⬜ PostHog installed in iOS app
- ⬜ Track events: `user_signed_up`, `gmail_connected`, `brain_dump_submitted`, `task_extracted`, `signal_actioned`, `signal_dismissed`, `brief_generated`, `skill_run`, `converted_to_pro`, `email_draft_sent`, `email_draft_dismissed`, `session_opened`, `app_opened`
- ⬜ Funnel analysis: signup → gmail_connected → brain_dump → converted_pro
- ⬜ Retention: Day 1, Day 7, Day 30 active users
- ⬜ Key metric dashboard: MRR, active users, gmail_connected %, conversion rate

### 5.4 Team Plan
- ⬜ Team plan product in Stripe — $14/user/month
- ⬜ Team creation flow — user creates team, becomes admin, gets link to invite members
- ⬜ Invite by email — invited user gets email, signs up, automatically added to team with Pro access
- ⬜ Team signals view — admin sees all team members' signals in one queue
- ⬜ Shared skill library — admin creates skills visible to all team members
- ⬜ Manager dashboard — team completion rates, top signals this week, per-member activity

---

## PART 6 — SESSION 10+ (OS Moat — requires contractors)

### 6.1 Dynamic Island (ActivityKit)
- ⬜ Create `AxisLiveActivity.swift` — ActivityKit Live Activity
- ⬜ Define `AxisLiveActivityAttributes` — static: user_id; dynamic: current_status_text, urgency_count, is_dispatching
- ⬜ Compact leading view: Axis icon
- ⬜ Compact trailing view: urgency count badge
- ⬜ Minimal view: pulsing dot when dispatch is running
- ⬜ Expanded view: "Reading inbox...", "3 emails ranked", "Invoice flagged: $4,200"
- ⬜ Backend sends push-to-start Live Activity updates during dispatch runs
- ⬜ Live Activity ends after dispatch completes (auto-dismiss 30 seconds after completion)

### 6.2 Apple Watch
- ⬜ WatchOS extension target in Xcode
- ⬜ `SignalWatchView.swift` — current signal on watch face
- ⬜ Tap to mark done — Digital Crown haptic confirmation
- ⬜ Brain dump via voice dictation on wrist
- ⬜ Watch complication — current signal title + urgency

### 6.3 iOS Focus Mode API
- ⬜ Auto-set Work Focus when first email actioned in morning
- ⬜ GPS arrival at site → set custom Site Focus mode silently
- ⬜ Focus filter: only Axis notifications permitted in Site/Work modes

### 6.4 Android App — the acquisition demo
- ⬜ Android project — Kotlin + Jetpack Compose
- ⬜ NotificationListenerService — reads ALL app notifications with one permission
  - WhatsApp personal messages
  - Instagram DMs
  - Every app notification — the thing iOS literally cannot do
- ⬜ Android accessibility service — full ambient awareness
- ⬜ Show feature delta vs iOS — "This is what happens when the OS gives us access"
- ⬜ This is the Apple acquisition demo — live demonstration of platform potential

### 6.5 Llama 4 On-Device Privacy Layer
- ⬜ Core ML export of Llama 4 Scout (17B) for on-device inference
- ⬜ Health data analysis entirely on-device — sleep, HRV never leaves iPhone
- ⬜ Full email archive analysis on-device — no raw emails sent to any server
- ⬜ On-device voice model fine-tuning — Llama 4 learns user patterns locally
- ⬜ Privacy dashboard — shows user exactly what data goes to which server
- ⬜ On-device inference results (not raw data) sent to backend for orchestration

### 6.6 Skills Marketplace
- ⬜ User can publish custom skills — "Make public" toggle on skill
- ⬜ Marketplace browse page — skills by category, sorted by installs
- ⬜ One-tap install another user's skill
- ⬜ Paid skills — creator sets price, Axis takes 30%
- ⬜ Skill reviews — rating + text
- ⬜ Featured skills curated by Axis team

---

## REVENUE MILESTONES (not a checklist — a forcing function)

- ⬜ $4.5K MRR — proof of life (500 Pro users × $9)
- ⬜ Post Swift contractor brief on Upwork — DO THIS NOW, contractors book weeks ahead
- ⬜ $18.7K MRR — HIRE TRIGGER — 2 Swift contractors (Dynamic Island, Watch, Android demo)
- ⬜ $50K MRR — OS moat features fully funded
- ⬜ $500K MRR — Apple acquisition conversation

---

## THE 12 RULES (non-negotiable)

1. Never build Phase 2 before Phase 1 NPS > 40
2. One repo per layer — never mix iOS and backend code
3. Real device testing for ALL OS features — simulator is not enough
4. Raw personal data (health, emails) never leaves the device unless user explicitly authorised
5. Battery usage under 5%/day — measure before every TestFlight build
6. App Store review is a design constraint — build within it, not around it
7. Update CLAUDE.md and all context files after every significant session
8. Build Android before Month 6 — the acquisition demo requires it
9. No acquisition conversations before $500K MRR
10. 18-month sprint — this is not a 10-year company
11. Never paste API credentials in any chat window, ever
12. Build on and tweak — never full redesign mid-sprint

---

*Every task above maps directly to a file, endpoint, or feature in the product.*
*Do not summarise. Do not combine tasks. Every item is one specific thing.*
*Update this checklist at the end of every session.*

**END OF AXIS BUILD CHECKLIST v1**

---

## PART 7 — SESSION 7 ADDITIONS (from expanded vision)

### 7.1 Smart Notes
- ⬜ Add notes table to models.py (id, user_id, content, tags[], source, context_snapshot, created_at)
- ⬜ GIN index on content for full-text search
- ⬜ Run Neon migration for notes table
- ⬜ Create services/notes_service.py — save_note(), search_notes(), get_related_notes()
- ⬜ Create routes/notes.py — POST /notes, GET /notes, GET /notes/search?q=
- ⬜ Register notes router in main.py
- ⬜ Update prompts/thread_system.py to detect: "remember [x]", "note that [x]", "what do I know about [x]"
- ⬜ Wire notes into context_assembler.py — inject last 7 days of notes into dispatch context
- ⬜ Wire notes into meeting prep — surface notes about attendees
- ⬜ Wire notes into morning brief — surface notes relevant to today's calendar

### 7.2 Context Notes
- ⬜ ALTER TABLE users ADD COLUMN IF NOT EXISTS context_notes TEXT
- ⬜ PATCH /me accepts context_notes field
- ⬜ context_assembler.py injects context_notes at TOP of every Claude call
- ⬜ Settings.jsx — "What Axis should always know" textarea with autosave

### 7.3 [Send] Button on Email Drafts
- ⬜ Thread.jsx — detect message_type="email_draft" or "Draft reply ready:" in content
- ⬜ Render [Send] [Edit] [Dismiss] action buttons below draft messages
- ⬜ sendDraft() function — calls POST /gmail/send with extracted draft
- ⬜ editDraft() — opens edit modal, user modifies, then sends
- ⬜ dismissDraft() — logs to interactions, removes buttons
- ⬜ Show "Sent ✓" confirmation inline after send

### 7.4 Status Intelligence
- ⬜ Create services/status_service.py — get_status(user_id, topic, db)
- ⬜ Semantic search across emails, tasks, notes, invoices, calendar for topic
- ⬜ Create prompts/status.py — specific, dated, actionable briefing under 150 words
- ⬜ Thread command detection: "status of [x]", "update on [x]", "where are we with [x]"
- ⬜ daily_situation_briefing() — "what's on my plate today" full synthesis

### 7.5 Fix User Name from Clerk
- ⬜ routes/auth.py — extract first_name from JWT claims on upsert
- ⬜ Save to users.name if currently null
- ⬜ Every prompt uses real name immediately

### 7.6 Voice Input on Web
- ⬜ Thread.jsx — mic button next to send using webkitSpeechRecognition
- ⬜ BrainDump.jsx — mic button on textarea
- ⬜ Visual indicator: pulsing dot while recording
- ⬜ lang set to 'en-AU' default

### 7.7 Watch Service
- ⬜ Add watches table (id, user_id, topic, watch_type, last_checked_at, last_result, threshold, is_active)
- ⬜ Create services/watch_service.py — create_watch(), run_all_watches()
- ⬜ Hourly cron in APScheduler
- ⬜ Thread commands: "watch [x]", "monitor [x]", "let me know if [x] changes", "stop watching [x]"
- ⬜ Perplexity for news watches, Gmail scan for person watches

### 7.8 Follow-Up Tracker
- ⬜ Add follow_ups table (id, user_id, email_id, to_email, subject, sent_at, follow_up_due, is_done)
- ⬜ Create services/followup_service.py — scan_for_missing_replies()
- ⬜ Wire into dispatch job — runs every 15 min
- ⬜ Surface no-reply emails as urgency 6 push with draft follow-up

### 7.9 Weekly Retrospective Email
- ⬜ Add RESEND_API_KEY to Railway
- ⬜ Add weekly_retrospectives table
- ⬜ Create services/retrospective_service.py
- ⬜ Create prompts/retrospective.py — warm, personal, specific, under 200 words
- ⬜ Sunday 6PM cron wired in APScheduler
- ⬜ Sends to user.email via Resend

### 7.10 PWA Manifest
- ⬜ axis-web/public/manifest.json
- ⬜ axis-web/public/icon-192.png + icon-512.png
- ⬜ index.html — apple-mobile-web-app meta tags
- ⬜ Add to Home Screen prompt after 3rd session

### 7.11 Proactive Skill Suggestions
- ⬜ Add skill_suggestions table
- ⬜ Create services/suggestion_service.py — detect_patterns()
- ⬜ Wire into Sunday apprentice cycle
- ⬜ Thread message: "I noticed X. Want me to automate it? [Create skill] [Not now] [Never]"

### 7.12 Stripe Finance Intelligence (user's own Stripe)
- ⬜ Stripe Connect OAuth — GET /auth/stripe-connect + callback
- ⬜ Create services/stripe_service.py — get_overdue_invoices(), get_cash_flow_summary()
- ⬜ Invoice chasing wired into dispatch
- ⬜ Cash flow in morning brief

### 7.13 Weather + Travel Time
- ⬜ Add OPENWEATHER_API_KEY to Railway (free)
- ⬜ Create services/weather_service.py
- ⬜ For each calendar event with location: weather forecast + drive time
- ⬜ Add to morning brief: "Site visit 8AM. 14°C raining. Leave by 7:20."
- ⬜ User sets home location in Settings

### 7.14 Multi-Turn Task Execution
- ⬜ Update thread_system.py to detect multi-step intent
- ⬜ State machine: intent → gather info → confirm → execute
- ⬜ MANDATORY confirmation step before any send/create
- ⬜ "Set up a meeting with Marcus next week" → full flow end to end

### 7.15 Risk + Opportunity Detection
- ⬜ Extend dispatch v3 with risk scanning pass
- ⬜ Detect: quote expiry, silent important contacts, calendar conflicts, invoice thresholds
- ⬜ Surface as urgency 8 push with context

### 7.16 Relationship Health
- ⬜ Add last_interaction_at to relationship_graph
- ⬜ Weekly scan for important contacts silent 21+ days
- ⬜ Surface in morning digest with check-in draft

