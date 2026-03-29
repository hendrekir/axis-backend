# AXIS — Full Build Checklist
## Every task, every file, every integration. Do not summarise.
### Last updated: Session 6 · March 2026

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
- ✅ Add `skills` table to `models.py` — id, user_id, name, description, is_builtin, is_active, data_sources (JSONB), reasoning_model, trigger_type, trigger_config (JSONB), output_routing, system_prompt, created_at, updated_at
- ✅ Add `skill_executions` table to `models.py` — id, skill_id, user_id, input_context (JSONB), output_result, model_used, surface_delivered, user_action, execution_time_ms, created_at
- ✅ Add `api_connections` table to `models.py` — id, user_id, service, access_token, refresh_token, token_expiry, is_connected, scopes (JSONB), metadata (JSONB), updated_at, UNIQUE(user_id, service)
- ✅ Add `model_routes` table to `models.py` — id, task_type, model, reasoning, cost_per_1m_input, is_active
- ✅ Run Neon migration — all 4 tables created via Base.metadata.create_all on startup
- ✅ Seed built-in skills on first GET /skills call — email, calendar, finance, research, entertainment, site (6 skills)
- ✅ `users` table — calendar_access_token, calendar_refresh_token, calendar_token_expiry, calendar_connected columns added via ALTER TABLE IF NOT EXISTS startup migration

### 2.2 Model Router
- ✅ Create `services/model_router.py` — route(), resolve_model(), _call_model()
- ✅ `route()` returns { text, model, elapsed_ms } — single entry point for all AI calls
- ✅ `_call_openai_compatible()` shared caller for Perplexity, Grok, OpenAI (all use chat/completions)
- ✅ `_call_perplexity()` — sonar-pro model
- ✅ `_call_grok()` — grok-3-fast model
- ✅ `_call_gemini()` — gemini-2.0-flash-lite and gemini-2.0-pro
- ✅ `_call_openai()` — gpt-4o model
- ✅ Fallback to Claude if model API key missing or call fails
- ✅ DEFAULT_ROUTES dict maps task_type → model (matches AXIS_INTELLIGENCE_v1.md)
- ✅ Uses httpx (already in requirements) for async HTTP
- ✅ Response time logged via logger.info per call
- ⬜ Add PERPLEXITY_API_KEY to Railway Variables (when ready)
- ⬜ Add GROK_API_KEY to Railway Variables (when ready)
- ⬜ Add GEMINI_API_KEY to Railway Variables (when ready)
- ⬜ Add OPENAI_API_KEY to Railway Variables (optional)

### 2.3 Triage Service
- ✅ Create `services/triage_service.py` — triage_items(), _parse_triage()
- ✅ Routes through model_router as task_type="triage" → Gemini Flash-Lite
- ✅ Scores each item 1-10 against user profile (name, mode, tasks, calendar)
- ✅ Strips markdown fences, parses JSON, merges classifications with original items
- ✅ Safe fallback: marks all as "relevant" if parse fails (nothing silently dropped)
- ✅ Returns { "urgent": [...], "relevant": [...], "noise": [...] }
- ✅ Logs counts via logger.info per triage run

### 2.4 Signal Filter
- ✅ Create `services/signal_filter.py` — apply_filters(), 5-layer noise reduction
- ✅ Filter 1 — relevance: boosts score if item keywords match active tasks or user model interests
- ✅ Filter 2 — urgency: threshold routing (7+ push, 4-6 digest, <4 silent)
- ✅ Filter 3 — context: +1 boost if item category matches current mode (work/builder/student/founder/personal)
- ✅ Filter 4 — deduplication: SHA256 hash of normalised text, same content silenced within session
- ✅ Filter 5 — apprentice: 8+ dismissals of a content_type in last 14 days → score drops by 3
- ✅ Returns { "push": [...], "digest": [...], "silent": [...] }

### 2.5 Gmail SEND
- ✅ Gmail OAuth SCOPES already included gmail.send since Session 4
- ✅ `send_email()` added to `services/gmail_service.py` — MIMEText, base64 encode, In-Reply-To/References headers for thread replies
- ✅ `POST /gmail/send` endpoint in `routes/gmail.py` — auth required, accepts { to, subject, body, thread_id, in_reply_to }
- ✅ Returns { status: "sent", message_id, thread_id }
- ⬜ Create `prompts/email_draft.py` — voice-matched draft prompt (needs voice model data)
- ⬜ Add [Send] / [Edit] / [Dismiss] action buttons to thread messages in React frontend
- ⬜ Update dispatch to generate email drafts for urgency 8+ emails

### 2.6 Google Calendar OAuth
- ✅ `routes/calendar.py` — GET /auth/calendar → consent → /auth/calendar/callback stores tokens
- ✅ `services/calendar_service.py` — fetch_todays_events(), fetch_upcoming_events(), get_next_event(), detect_conflicts()
- ✅ Calendar tokens stored on users table (calendar_access_token, calendar_refresh_token, calendar_token_expiry, calendar_connected)
- ✅ GET /calendar/today — returns events + conflicts
- ✅ GET /calendar/upcoming?hours=24 — events in next N hours
- ✅ /me returns calendar_connected status
- ✅ Calendar data wired into dispatch v2 context
- ✅ /auth/calendar and /auth/calendar/callback added to PUBLIC_PATHS
- ⬜ Add Connect Calendar button to Settings screen in React
- ⬜ Add GOOGLE_CALENDAR_REDIRECT_URI to Railway Variables
- ⬜ Add calendar callback as authorized redirect URI in Google Cloud Console
- ⬜ Create `services/meeting_prep.py` — 30-min pre-meeting cron with Perplexity attendee research

### 2.7 Skills Framework (replaces monolithic dispatch)
- ✅ `routes/skills.py` rewritten — GET /skills, POST /skills, PATCH /skills/{id}, DELETE /skills/{id}, POST /skills/{id}/run, POST /skills/{id}/chat (legacy compat)
- ✅ `services/skill_engine.py` — execute_skill(), seed_builtin_skills(), run_dispatch_skills()
- ✅ execute_skill() injects user context into system prompt, routes to configured model, logs to skill_executions
- ✅ 6 built-in skills seeded on first GET /skills: email (Claude), calendar (Claude), finance (Claude), research (Perplexity), entertainment (Grok), site (Claude)
- ✅ run_dispatch_skills() loops all dispatch-triggered active skills for a user
- ✅ `prompts/dispatch_v2.py` — skills-aware prompt with model_to_use + skill_name per item
- ✅ `services/dispatch.py` rewritten — uses dispatch_v2, pulls calendar + gmail, assembles user model + skills context, calls run_dispatch_skills() after classification
- ✅ Dispatch triggers for any connected user (gmail OR calendar)
- ✅ Dispatch strips markdown fences before JSON parse

### 2.8 Perplexity Integration
- ✅ `services/perplexity_service.py` — research(), person_lookup(), news_briefing()
- ✅ All route through model_router as task_type=research/person_lookup/news → Perplexity sonar-pro
- ✅ Falls back to Claude if PERPLEXITY_API_KEY not set
- ✅ Research skill built-in wired to use perplexity via reasoning_model="perplexity"
- ⬜ Wire meeting prep to use person_lookup() for attendee background

### 2.9 Grok Integration
- ✅ `services/grok_service.py` — entertainment_digest(), social_trends(), sports_update()
- ✅ All route through model_router as task_type=entertainment/social_trends/sports → Grok grok-3-fast
- ✅ Falls back to Claude if GROK_API_KEY not set
- ✅ Entertainment skill built-in wired to use grok via reasoning_model="grok"
- ⬜ Include Grok entertainment brief in morning digest assembly

### 2.10 Apprentice — Weekly Improvement
- ✅ `services/apprentice.py` — run_improvement_cycle(), rebuild_voice_model(), run_all_improvement(), run_all_voice_rebuild()
- ✅ Improvement cycle: pulls 7 days of interactions grouped by surface/content_type/action, sends to Claude with existing user_model, updates productive_windows/completion_rates/notif_response_rates/defer_patterns
- ✅ Voice model rebuild: reads last 50 sent emails from sent_emails_cache, Claude extracts voice patterns (avg_word_count, formality_by_type, sign_offs, openers, sentence_style, tone), updates user_model.voice_patterns
- ✅ Both strip markdown fences from Claude response before JSON parse
- ✅ APScheduler wired in main.py: Sunday 3AM UTC improvement, Sunday 4AM UTC voice rebuild
- ✅ Improvement runs for all Pro users, voice rebuild for Pro + gmail_connected users
- ⬜ Sunday 5AM UTC: collective patterns update (anonymised cross-user)

---

## PART 3 — SESSION 7 (Entertainment + lifestyle layer)

### 3.1 YouTube Integration
- ✅ Create `services/youtube_service.py` — fetch_subscription_videos(), fetch_trending_videos(), summarise_video() (Gemini via model_router)
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
- ✅ Create `services/reddit_service.py` — fetch_subreddit_posts(), fetch_multiple_subreddits(), search_reddit() (app-only OAuth token)
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
- ✅ Hacker News integrated in `services/news_service.py` — fetch_hacker_news() uses free Firebase API
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
- ✅ `services/news_service.py` — fetch_google_news() (RSS, no key), fetch_hacker_news() (free API), fetch_news_for_topics(), fetch_rss_feed() (generic RSS/Atom)
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
