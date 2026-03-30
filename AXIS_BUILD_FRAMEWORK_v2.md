# AXIS — Build Framework v2
## Complete architecture, feature set, and build sequence
### Updated: Session 7 · March 2026

---

## THE PRODUCT DEFINITION

Axis is a Jarvis-level ambient intelligence layer for iPhone.

Not a chatbot. Not a productivity app. An intelligence that watches everything, thinks about your life as a whole, acts on your behalf without being asked, answers any question with expert depth and personal context, proposes its own improvements, remembers everything you tell it, and becomes more you over time.

The Jarvis standard: would Tony Stark use this? Not the movie character — what people imagine when they hear "Jarvis."

---

## THE FULL INTELLIGENCE ARCHITECTURE

```
LAYER 0 — INPUT COLLECTION (continuous)
Gmail · Google Calendar · Spotify · Reddit · YouTube · Hacker News
Product Hunt · Google News/RSS · X/Twitter (Grok native) · Stripe (user's own)
Xero · OpenWeather · Google Maps Distance Matrix · Eventbrite
HealthKit (iOS) · CoreLocation (iOS) · Contacts (birthdays)
Brain dump · Smart notes · Siri/App Intents (iOS) · Share Extension
Webhooks inbound (Zapier/Make) · Perplexity sonar-pro (real-time web)

LAYER 1 — CHEAP TRIAGE (Gemini Flash-Lite $0.01/1M)
Classify each item: spam / noise / relevant / urgent
Score 1-10 against user profile · Deduplicate (24hr window)
~95% discarded here at near-zero cost

LAYER 2 — SIGNAL FILTER (5 layers)
1. Relevance — connects to something user cares about
2. Urgency — score threshold
3. Context — calendar/location/mode aware
4. Deduplication — same story once, best source wins
5. Apprentice — 8+ dismissals = auto-deprioritise

LAYER 3 — CONTEXT ASSEMBLY (injected into every AI call)
User model · Context notes (permanent user instructions) · Smart notes
Session state (mode, location, health, time) · Today's calendar
Recent thread · Active projects + status · Watch list · Collective patterns

LAYER 4 — SPECIALIST MODEL ROUTING
Claude — email drafts, voice matching, reasoning, notes, planning
Perplexity — research, expert intelligence, news, people lookup
Grok — social, entertainment, X/Twitter, sports, breaking news
Gemini Flash-Lite — triage, video, images, bulk classification
Gemini Pro — complex reasoning, mathematical analysis
GPT-5 — code execution, image generation, data analysis
DeepSeek — bulk non-sensitive public content only
Llama 4 — privacy-sensitive on-device (iOS Phase 3)

LAYER 5 — INTELLIGENCE EXECUTION
Status queries · Expert briefings with personal relevance
Planning + brainstorming sessions · Risk + opportunity detection
Follow-up tracking · Relationship health monitoring
Ambient watch list monitoring · Proactive skill suggestions
Multi-turn task execution

LAYER 6 — OUTPUT ROUTING
Push notification · Thread message · Lock screen widget (iOS)
Dynamic Island (iOS Phase 2) · Siri response (iOS) · Control Centre (iOS)
Digest · Weekly email (Resend) · Action execution (send/create/remind)
Webhook outbound (Zapier/Make) · Silent (logged only)

LAYER 7 — FEEDBACK + APPRENTICE LOOP
Every action logged → Sunday 3AM improvement cycle
Sunday 4AM voice model rebuild · Sunday 5AM collective patterns
Pattern detection → proactive skill suggestions
Corrections from Apprentice screen → re-train
```

---

## THE CORE DATA MODEL

### Live in Neon (Sessions 1–6)
```
users                  — clerk_id, mode, plan, gmail_connected, calendar_connected,
                         spotify_connected, apns_token, timezone, context_notes (new)
thread_messages        — user_id, role, content, message_type, source_skill
tasks                  — user_id, title, priority, category, is_done, due_date
user_model             — voice_patterns, relationship_graph, productive_windows,
                         completion_rates, defer_patterns
interactions           — every user action logged
relationship_graph     — contact importance scores
patterns               — weekly computed patterns
sent_emails_cache      — voice model training data
collective_patterns    — cross-user anonymised intelligence
skills                 — user-defined and built-in workflows (6 seeded)
skill_executions       — every skill run logged
api_connections        — OAuth tokens per service
model_routes           — task_type → model routing rules
```

### New tables (Session 7)
```sql
-- Smart notes — "remember this" + readback + cross-reference
CREATE TABLE notes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  content TEXT NOT NULL,
  tags TEXT[] DEFAULT '{}',
  source TEXT DEFAULT 'manual',       -- manual|voice|dispatch|email
  context_snapshot JSONB DEFAULT '{}',-- mode, location, time at capture
  related_email_ids TEXT[] DEFAULT '{}',
  related_task_ids UUID[] DEFAULT '{}',
  related_event_ids TEXT[] DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_notes_user ON notes(user_id);
CREATE INDEX idx_notes_created ON notes(user_id, created_at DESC);

-- Ambient monitoring — "watch this for me"
CREATE TABLE watches (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  topic TEXT NOT NULL,
  description TEXT,
  watch_type TEXT DEFAULT 'topic',    -- topic|person|project|email_thread
  sources TEXT[] DEFAULT '{}',
  threshold TEXT DEFAULT 'material',  -- material|any|urgent_only
  is_active BOOLEAN DEFAULT TRUE,
  last_checked TIMESTAMP,
  last_triggered TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Follow-up tracker — sent emails with no reply
CREATE TABLE followups (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  email_id TEXT NOT NULL,
  to_email TEXT NOT NULL,
  subject TEXT,
  sent_at TIMESTAMP NOT NULL,
  follow_up_at TIMESTAMP NOT NULL,   -- sent_at + 3 days default
  status TEXT DEFAULT 'pending',     -- pending|replied|snoozed|dismissed
  draft_followup TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Proactive skill suggestions
CREATE TABLE skill_suggestions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  pattern_detected TEXT NOT NULL,
  suggested_skill_config JSONB NOT NULL,
  suggestion_text TEXT NOT NULL,
  status TEXT DEFAULT 'pending',     -- pending|accepted|dismissed
  dismissed_until TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Users table additions (ALTER TABLE)
```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS context_notes TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS spotify_connected BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS spotify_access_token TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS spotify_refresh_token TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS spotify_token_expiry TIMESTAMP;
```

---

## THE COMPLETE FEATURE RANKING

### Tier 1 — transforms what the product is

**1. Smart notes** — "remember this" + readback + cross-reference
`notes` table + thread commands + semantic search. Connected to emails, tasks, calendar, dispatch. The stickiest feature — used 5-10x daily regardless of other activity.
- Thread: "remember [anything]" → saves with context snapshot
- Thread: "what do I know about [topic]" → semantic search + readback
- Thread: "what did I note about [person/project]" → filtered notes + related emails
- Morning brief: surfaces notes relevant to today's calendar
- Meeting prep: pulls notes about attendees

**2. Status on anything** — "what's the status of the Greenfield deal?"
Thread command → Claude synthesises from emails + calendar + invoices + notes + tasks. One question replaces checking 4 apps. Works for any project, person, deal, or situation.
- "What's the status of X?" → full current picture
- "Where are we with Marcus?" → last email + outstanding invoice + next meeting + notes
- "What's happening with the Level 2 install?" → tasks + emails + notes + risks

**3. Expert intelligence + personal relevance**
Perplexity sonar-pro with trusted source filter, then second Claude pass connecting findings to user's specific context. "Iran situation → your steel supplier ships via Gulf → Greenfield quote expires in 30 days."
- Source filter: Reuters, AP, BBC, named academics with institution, regulatory bodies
- Personal relevance: checks user's emails, projects, suppliers, investments
- Never speculative — only surfaces connection if it's direct and specific

**4. Context notes** — what Axis always needs to know
`users.context_notes` TEXT injected into every Claude call via context_assembler.py. User writes once: "Greenfield is my most important client. Closing $200K with Marcus. On leave Dec 20."

**5. Proactive skill suggestions**
Dispatch detects repeated manual patterns → surfaces proposal in thread. "I notice you've chased 4 invoices manually this month. Want me to automate that?" Accepted → auto-generates skill config and saves.

**6. Planning + brainstorming partner**
Structured multi-turn session: Claude asks right questions → Perplexity validates market/competition in real-time → Claude synthesises plan → saves as living skill that monitors relevant news weekly.

### Tier 2 — meaningfully better product

**7. Ambient monitoring** — "watch this for me"
`watches` table + cron checks + notification only on material changes. "Watch the Greenfield contract." "Let me know if the building code changes." User sets it and forgets it.

**8. Risk + opportunity detection**
Built into dispatch: quote expires in 3 days unreplied, client silent 18 days, supplier mentions shortage, two meetings overlap. Flags before user thinks to check.

**9. Multi-turn task execution**
"Set up a meeting with Marcus next week." Thread state machine: intent detected → gather availability info → confirm with user → execute (calendar invite + email in user's voice). End to end, no app switching.

**10. [Send] + [Edit] buttons on email drafts**
Thread messages with message_type="email_draft" get action buttons. Calls POST /gmail/send. Frontend only — 1 hour. Closes the most important action loop.

**11. PWA — home screen before iOS ships**
manifest.json + service worker + apple meta tags. Users add to home screen on iPhone today. Full-screen, push notifications, no browser chrome. Bridges 3-month gap until native iOS.

**12. Follow-up tracker**
`followups` table populated when emails sent via Gmail API. 3-day cron checks for no reply. "Your quote to Greenfield has been unread 5 days. Follow up?" Draft ready, one tap sends.

**13. Voice input on web**
Web Speech API mic button in Thread + Brain Dump. Hold to speak, release to send. No backend changes. Chrome desktop + mobile. First taste of voice-first before iOS.

### Tier 3 — Jarvis environmental + life intelligence

**14. Daily situation briefing** — "what's my situation today?"
Thread command → Claude synthesises complete picture: active deals + status, outstanding invoices, people awaiting reply, risks on radar, what's coming, one focus.

**15. Relationship health** — people going cold
Detect contacts with declining interaction frequency. "You haven't spoken to Marcus in 23 days — last was your unanswered quote." Especially valuable for sales and client work.

**16. Weather + travel time in morning brief**
OpenWeather + Google Maps Distance Matrix (both free tiers). "Site visit 8AM. 14°C rain. Leave by 7:20 based on current traffic." Combines 3 things no one remembers to check together.

**17. Weekly retrospective email**
Sunday 6PM via Resend. Tasks completed, emails handled, patterns noticed, one suggestion for next week. Users share these — organic word of mouth.

**18. Zapier/webhook skill output**
Any skill fires a webhook as output. Receives webhooks from external services. 5,000+ integrations unlocked instantly. Founders and builders become dependent.

**19. Stripe finance intelligence**
User's own Stripe OAuth (separate from billing Stripe). Overdue detection + voice-matched reminder draft. Invoice chase sequence: 7 days → 14 days → 30 days, runs automatically.

### Tier 4 — iOS Phase 2 / contractors / funded by revenue

**20. HomeKit + smart home** — "turn off the lights, I'm leaving." Location-aware environment control.

**21. Hugging Face specialist model import** — legal, medical, construction compliance. On-device via Core ML, same infrastructure as Llama 4. Build after Llama 4 on-device works.

**22. Predictive scheduling** — "you have 12 tasks and 7 meetings, here's your week." Calendar blocks created automatically based on energy patterns.

**23. Dynamic Island — live agent status** — ActivityKit, shows "Reading inbox... 3 ranked... Invoice flagged." The Jarvis ambient presence moment.

**24. Phone agent** — ElevenLabs + Twilio. "Call the restaurant and book a table for 2 Friday 7PM." Technology exists today. Sequence after iOS + $50K MRR.

---

## BUILD PHASES

### Phase 1 — Foundation ✅ Sessions 1–5
FastAPI + Railway + Neon + Clerk + Stripe · Gmail OAuth + dispatch · 6 web screens · $9/mo paywall

### Phase 2 — Orchestration backbone ✅ Session 6
Skills framework · Multi-model router · Triage + signal filter · Dispatch v3 · Calendar + Spotify OAuth · Apprentice crons · YouTube/Reddit/News services

### Phase 3 — Intelligence layer ← Session 7 (building now)
Context notes · Smart notes · Status command · Expert intelligence · [Send] buttons · Voice input · PWA · Follow-up tracker · Proactive skill suggestions · Ambient monitoring · Risk detection · Multi-turn execution · Weather + travel · Weekly retrospective · Zapier webhook · Stripe finance · Planning skill · Relationship health

### Phase 4 — iOS app · Sessions 8–10
SwiftUI screens · WidgetKit · App Intents (8 Siri commands) · HealthKit + CoreLocation · APNs with action buttons · Control Centre tile · RevenueCat · TestFlight → App Store

### Phase 5 — Revenue + growth
Landing page · Resend email sequences · PostHog analytics · Team plan · $4.5K MRR

### Phase 6 — OS moat (contractors, funded by revenue)
Dynamic Island · Apple Watch · Android NotificationListenerService · Llama 4 on-device · Hugging Face import · Phone agent (ElevenLabs + Twilio) · HomeKit · Skills marketplace

---

## JARVIS ALIGNMENT

| Jarvis capability | Axis equivalent | Status |
|---|---|---|
| Watches everything silently | Dispatch + watches table | Session 7 |
| Status on any project/person | Status command in Thread | Session 7 |
| Expert intelligence briefings | Perplexity + source filter + personal context | Session 7 |
| Proactively flags risks | Risk detection in dispatch | Session 7 |
| Remembers everything told | Smart notes table | Session 7 |
| Executes multi-step tasks | Multi-turn thread state machine | Session 7 |
| Proposes improvements | Proactive skill suggestions | Session 7 |
| Improves over time | Sunday apprentice crons | Live ✅ |
| Ambient presence | Dynamic Island + Control Centre | iOS Phase 2 |
| Voice from anywhere | App Intents + Control Centre | iOS |
| Controls environment | HomeKit | Phase 6 |
| Makes calls | ElevenLabs + Twilio | Phase 6 |

---

**END OF AXIS BUILD FRAMEWORK v2**
