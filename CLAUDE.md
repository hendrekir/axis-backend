# AXIS — CLAUDE.md v2.0
## Complete product context, UX architecture, intelligence system, build plan
### Last updated: March 2026 — Session 3 complete, Sessions 4+ planned
### Author: Hendre (Dreyco Pty Ltd, Brisbane)

---

## READ THIS FIRST

This is the single source of truth for Axis. Load at the start of every Claude Code or Cursor session. Update after every significant session — what changed, what broke, what was decided and why.

**Current status:** Backend live on Railway. React frontend live on Vercel. Brain dump working end to end. Gmail OAuth and intelligence loop not yet built.

**The rule:** Build on and tweak what exists. Never full redesign. Every session moves forward.

---

## 1. WHAT AXIS IS

### One sentence
Axis is an ambient AI agent that reads your email, calendar, health, location, and finances continuously — and communicates back through one persistent thread, smart notifications, and a lock screen widget. You stop managing your phone. It manages your life.

### The core insight
Every productivity app makes you more phone-dependent. Axis inverts this. Your phone already has all the data needed to run your life. Axis is the AI that reads it, handles 95% silently, and surfaces only what genuinely needs you — at the right moment, on the right surface, with the action pre-prepared.

### The slogan
**Be phone lazy. Be world productive.**

### The goal
8 minutes of phone time per day. 3 deliberate sessions. Everything else handled.

### Product score
- **Current build (brain dump only):** 6/10
- **With Gmail + Calendar OAuth + intelligence loop:** 8.5/10
- **With Android NotificationListenerService:** 9.5/10
- **After Apple acquisition (native OS access):** 9.5/10 on iOS

### Acquisition target
**Apple** — 18-month window. iOS 8.5 proves the concept. Android 9.5 is the acquisition demo. Apple is the only company that can complete the last 1 point natively on iOS.

---

## 2. THE UX ARCHITECTURE

### Core principle
**Axis is the HQ. Everything else is a surface that points back to HQ.**

The app is the command centre — the thread, brain dump, skills, day plan. But most users most of the time should never need to open it. They get what they need from the lock screen widget, a smart notification, or Siri. When they do open the app, it's deliberate.

**Axis comes to you. You go to Axis only when you choose to.**

### The surfaces

| Surface | Tech | Phase | What it shows |
|---|---|---|---|
| The Thread (HQ) | SwiftUI / React | Phase 1 | Persistent iMessage-style conversation. Axis messages you proactively. |
| Lock screen widget | WidgetKit | Phase 1 | One signal — most important action right now. Interactive buttons (mark done, snooze). |
| Smart notifications | APNs + action buttons | Phase 1 | Context-aware pushes with pre-prepared actions. [Send] [Edit] [Later] |
| Siri voice capture | App Intents framework | Phase 1 | "Hey Siri, add to Axis: call supplier Thursday." Hands-free input. |
| Dynamic Island | ActivityKit | Phase 2 | Live agent status — what Axis is reading right now. |
| Apple Watch | ClockKit | Phase 3 | One-tap done. Current signal. Haptic alerts. |
| macOS menu bar | NSStatusBar | Phase 3 | Current signal in one line. Click to expand thread. |

### The interaction patterns

**Pattern 1: Axis reads → you act**
Axis reads Gmail, Calendar, Health, GPS continuously. Detects what matters. Surfaces via notification or thread message with action pre-prepared. You tap one button.
Example: "Marcus replied — high intent, draft ready." [Send] [Edit]

**Pattern 2: You speak → Axis handles**
Voice capture via Siri, brain dump text, or Share Extension. You give Axis raw information. It structures, prioritises, and adds to thread or task list.
Example: "Hey Siri, brain dump in Axis: waterproof membrane failing on Level 2, need to reorder"

**Pattern 3: Widget → deep link**
Every widget tap goes exactly to the right place — not the app home screen. Signal widget opens that specific task. Email widget opens the draft.

**Pattern 4: One tap done**
Every surface has a one-tap action. The user almost never types. Axis pre-prepares everything.

### The ideal Axis day (target state)

```
6:50 AM  Morning digest push arrives while user is asleep
7:00 AM  Session 1 (3 min) — open thread, handle 4 things with 4 taps. "Put the phone down."
8:30 AM  GPS triggers Builder mode. Widget updates. Site context loads.
9:15 AM  Hands-free: "Hey Siri, tell Axis: membrane failing on Level 2, call supplier"
10:00 AM Meeting prep notification 30 min before — key points from recent email with Marcus
12:30 PM Session 2 (3 min) — midday check, brain dump loose thoughts
5:30 PM  Finance alert: "Invoice #47 overdue 14 days" [Send reminder] → done in 3 seconds
6:00 PM  Session 3 (2 min) — end of day, tomorrow's signal set. "You're done. Put the phone down."

Total phone time: ~8 minutes
```

---

## 3. THE INTELLIGENCE ARCHITECTURE

### The 5-layer system

```
Layer 1 — Data ingestion
Gmail OAuth · Google Calendar · Apple Calendar (EventKit) · HealthKit · CoreLocation
Stripe/Xero · Slack OAuth · Contacts graph · Brain dump text · Siri voice · Share Extension

↓ every 15 min · on change · on GPS trigger

Layer 2 — Context assembly (backend)
New inputs since last run · User model (learned patterns) · Current mode + location
Health context · Today's calendar · Relationship graph · Last 10 thread messages

↓ assembled into one structured prompt

Layer 3 — Claude processing (claude-sonnet-4-5)
Dispatch job · Email ranker · Morning digest · Meeting prep · Signal ranker · Voice model

↓ returns structured JSON with routing instructions

Layer 4 — Output routing
Push notification + action buttons · Lock screen widget update · Thread message
Dynamic Island · Signal queue update · Silent (handled, no interrupt)

↓ user acts (or doesn't)

Layer 5 — Feedback loop
Every action logged → user model updated weekly → Claude calls improve → better decisions
```

### The dispatch job (the heartbeat)
Runs every 15 minutes on Railway. Pulls new data from all connected OAuth sources. Assembles context. Calls Claude once. Routes outputs to correct surfaces. This is what makes Axis feel "always watching."

**Claude's job in the dispatch job:** Make decisions, not suggestions. For each input: urgency score (1-10), actionable (bool), surface to route to, action to pre-prepare, one-sentence reason. Return structured JSON only.

### The routing rules

| Urgency | Actionable? | Goes to | Example |
|---|---|---|---|
| 8-10/10 | Yes | Push notification immediately | High-intent email reply |
| 8-10/10 | No | Push + thread | Meeting location changed |
| 6-7/10 | Yes | Push during business hours | Overdue invoice |
| 5-6/10 | Yes | Morning digest | Meeting prep for tomorrow |
| 3-5/10 | Info | Morning digest | Health context |
| 1-2/10 | No | Silent | Newsletters, low-value emails |

**95% of what Axis processes never reaches the user.** That's the product.

---

## 4. THE MEMORY ARCHITECTURE

### Three layers of memory

**Layer 1 — Session context (expires 48hrs)**
Fast access for every Claude call. Current mode, today's calendar, last 10 messages, health context, active tasks.

**Layer 2 — User model (never expires, grows forever)**
Everything Axis has learned about this specific person:
- Voice patterns: sentence length, formality by recipient type, sign-offs, common phrases
- Relationship graph: contact importance scores, avg reply time, reply rate per contact
- Productive windows: when they actually complete tasks
- Completion rates: by category (work/health/admin etc)
- Notification response windows: when they act on pushes
- Defer patterns: what categories they consistently avoid
- Reply velocity: per contact, per category

**Layer 3 — Collective intelligence (anonymised, shared across users)**
Patterns that help new users immediately. Compounds with scale. This is the moat.

### Database tables to add (Session 4)

```sql
CREATE TABLE user_model (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) UNIQUE,
  voice_patterns JSONB DEFAULT '{}',
  relationship_graph JSONB DEFAULT '{}',
  productive_windows JSONB DEFAULT '{}',
  completion_rates JSONB DEFAULT '{}',
  notif_response_rates JSONB DEFAULT '{}',
  defer_patterns JSONB DEFAULT '{}',
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE interactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  surface TEXT NOT NULL,
  content_type TEXT NOT NULL,
  content_id TEXT,
  action_taken TEXT NOT NULL,
  response_time_ms INTEGER,
  mode TEXT,
  health_context JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE relationship_graph (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  contact_email TEXT NOT NULL,
  importance_score FLOAT DEFAULT 5.0,
  avg_reply_time_hrs FLOAT,
  reply_rate FLOAT,
  total_interactions INTEGER DEFAULT 0,
  last_interaction TIMESTAMP,
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, contact_email)
);

CREATE TABLE patterns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  best_productive_hours JSONB,
  deferred_categories JSONB,
  notif_response_windows JSONB,
  draft_acceptance_rate FLOAT,
  email_ranking_accuracy FLOAT,
  week_of DATE,
  UNIQUE(user_id, week_of)
);

CREATE TABLE sent_emails_cache (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  recipient TEXT,
  recipient_type TEXT,
  subject TEXT,
  body_summary TEXT,
  word_count INTEGER,
  formality_score FLOAT,
  sent_at TIMESTAMP
);

CREATE TABLE collective_patterns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  mode TEXT,
  pattern_type TEXT,
  pattern_data JSONB,
  sample_size INTEGER,
  confidence FLOAT,
  updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## 5. THE IMPROVEMENT LOOP

Every user action is a training signal. Every week the system gets smarter automatically.

**What gets logged:** Send, edit, dismiss, defer, open, ignore — every interaction. Mode, time, health context, what was shown, response time.

**Weekly improvement job (Sunday 3AM):**
1. Analyse past 7 days of interactions
2. Compute accuracy rates for each prediction type
3. Call Claude with interaction summary
4. Claude updates user model JSON
5. Updated model feeds into all next week's Claude calls

**Voice model builder (Sunday 4AM):**
1. Pull last 50 sent emails via Gmail API
2. Analyse sentence patterns, formality by recipient type, length, phrases
3. Update voice_patterns in user_model
4. Improved drafts the following week

**Evolution timeline:**
- Day 1-3: General heuristics. Useful but generic.
- Week 1-2: Pattern detection begins. Voice matching starts.
- Week 3-4: "It knows me." Drafts sound like you.
- Month 2-3: Anticipation. Axis predicts before you ask.
- Month 6+: Genuinely irreplaceable. Switching cost = 6 months of learning.

---

## 6. RAILWAY CRON JOBS

```
*/15 * * * *   Dispatch job — pulls data, calls Claude, routes outputs
50 6 * * *     Morning digest — 6:50AM user local time
0 3 * * 0      Improvement job — Sunday 3AM
0 4 * * 0      Voice model builder — Sunday 4AM
0 5 * * 0      Collective patterns — Sunday 5AM
```

---

## 7. THE THREE CRITICAL PROMPTS

### Prompt 1 — Dispatch

```python
DISPATCH_SYSTEM = """
You are Axis, an ambient AI agent for {name}.
Your job: decide what matters right now and what to do about it.
Make decisions, not suggestions. Return ONLY structured JSON.

For each item return:
{
  "urgency": 1-10,
  "actionable": true/false,
  "surface": "push|thread|widget|digest|silent",
  "action_type": "send_reply|create_task|update_widget|notify|none",
  "pre_prepared_action": "draft text or task title or notification copy",
  "reason": "one sentence"
}
"""
```

### Prompt 2 — Draft reply

```python
DRAFT_REPLY_SYSTEM = """
You are drafting an email reply on behalf of {name}.
Write EXACTLY like them. Never sound like AI.
Match their voice patterns precisely. Ready to send without editing.

Voice model: {voice_patterns}
Example past replies: {example_replies}
Email to reply to: {email_content}
Thread context: {thread_summary}
Target length: {target_word_count} words
"""
```

### Prompt 3 — Morning digest

```python
MORNING_DIGEST_SYSTEM = """
You are Axis. Generate {name}'s morning brief as thread messages.
Specific, warm, direct. Never waffle.
Max 4 messages. Each under 80 words.
End with "put the phone down."

Overnight data: {overnight_summary}
Today's calendar: {calendar_today}
Axis handled silently: {silent_count} items
"""
```

---

## 8. DATA SOURCES AND INTEGRATIONS

### Priority 1 — Build now
| Source | Method | What Axis does |
|---|---|---|
| Gmail | OAuth API | Ranks inbox, drafts replies in user's voice |
| Google Calendar | OAuth API | Meeting prep, conflict detection, travel time |
| Apple Calendar | EventKit (native) | iCloud calendar events |
| Apple Health | HealthKit (native) | Sleep routing, energy-based task weighting |
| GPS | CoreLocation (native) | Mode switching on arrival |
| Stripe/Xero | API OAuth | Invoice alerts, cash flow |
| Contacts | CNContactStore (native) | Relationship scoring |
| Share Extension | iOS native | User shares anything from any app into Axis |

### Priority 2 — Phase 2
| Source | Method | What Axis does |
|---|---|---|
| Slack | OAuth API | Channel reading, draft replies |
| Outlook/M365 | Microsoft Graph API | Enterprise email + Teams |
| WhatsApp Business | Business API | Business message reading |
| iOS Focus Modes | FocusAPI | Auto-sets Focus mode |

### iOS sandbox reality
- iMessage, WhatsApp personal, Instagram DMs, Snapchat — **blocked on iOS**
- Android NotificationListenerService = all notifications, official API = 9.5/10 product
- Build Android after iOS hits $18K MRR — use as Apple acquisition demo

---

## 9. APP INTENTS (SIRI + WIDGET BUTTONS)

```
"Hey Siri, add to Axis: [text]" → thread + task queue
"Hey Siri, what's my Axis signal?" → speaks back current task
"Hey Siri, mark my Axis signal done" → marks done, advances queue
"Hey Siri, brain dump in Axis" → dictation mode, returns ranked tasks
"Hey Siri, switch Axis to Builder mode" → changes context
"Hey Siri, open Email Skill in Axis" → deep links to skill
"Hey Siri, send that Axis reply" → sends pre-drafted reply
"Hey Siri, what's in my Axis brief?" → reads back digest
```

Interactive widget buttons (iOS 17+ App Intents):
- [Done] — marks signal complete, widget updates instantly
- [Snooze] — defers 2 hours, shows next priority
- [Quick add] — opens text input from lock screen
- [Send reply] — sends pre-drafted email reply

---

## 10. TECH STACK

| Layer | Tool | Notes |
|---|---|---|
| iOS UI | SwiftUI + UIKit | Native only |
| App integration | App Intents framework | Siri + Shortcuts + widget buttons |
| iOS data | EventKit · HealthKit · CoreLocation · CNContactStore | Native |
| OS surfaces | WidgetKit + ActivityKit | Lock screen + Dynamic Island |
| Backend | FastAPI on Railway | Async throughout |
| Database | Neon Postgres | All tables defined above |
| AI | Anthropic claude-sonnet-4-5 | Dispatch, drafts, digest |
| Dev AI (backend) | Claude Code | Primary dev |
| Dev AI (iOS) | Cursor + Claude 3.5 Sonnet | .cursorrules in iOS root |
| Auth | Sign in with Apple + Clerk | |
| Payments | RevenueCat (iOS) + Stripe (web) | |
| Email | Resend | |
| Analytics | PostHog | |

---

## 11. BUSINESS MODEL

| Tier | Price | Includes |
|---|---|---|
| Free | $0 | Thread, Signal, 3 brain dumps/day |
| Pro | $9/mo | Gmail, all Skills, unlimited brain dump, daily brief |
| Team | $14/user/mo | Signal sharing, manager dashboard |

Revenue milestones:
- $4.5K MRR — proof of life
- $18.7K MRR — **HIRE TRIGGER: 2 Swift contractors**
- $500K MRR — acquisition conversations

---

## 12. SESSION 4 PRIORITIES (DO IN THIS ORDER)

1. Add 4 new database tables (user_model, interactions, relationship_graph, patterns)
2. Gmail OAuth integration — connect inbox, poll every 15 min
3. Dispatch job — 15-min Railway cron, calls Claude, routes outputs
4. Morning digest cron — 6:50AM
5. Skills screens in React
6. Daily brief screen in React
7. Mode switcher
8. Stripe $9/mo paywall
9. Interactive WidgetKit widget with App Intent buttons
10. Landing page

**Start command for Session 4:**
```bash
cd ~/forge/axis-backend && claude
```
Tell Claude Code: "Read CLAUDE.md v2.0. Add the 4 new database tables first, then build Gmail OAuth integration and the dispatch job."

---

## 13. CURRENT DEPLOYMENT

- Backend: https://web-production-32f5d.up.railway.app
- Frontend: https://axis-web-chi.vercel.app
- Backend repo: github.com/hendrekir/axis-backend
- iOS repo: github.com/hendrekir/axis-ios
- Web repo: github.com/hendrekir/axis-web
- Local: ~/forge/axis-backend · ~/forge/axis-ios · ~/forge/axis-web

---

## 14. THE 12 RULES

1. Never build Phase 2 before Phase 1 NPS > 40
2. One repo per layer — never mix iOS and backend
3. Real device testing for all OS features
4. Raw personal data never leaves the device
5. Battery under 5%/day — measure before every TestFlight
6. App Store review is a design constraint
7. Update CLAUDE.md after every significant session
8. Build Android version before Month 6 — the acquisition demo
9. No acquisition talks before $500K MRR
10. 18-month sprint — not a 10-year company
11. Never paste credentials in any chat window
12. Build on and tweak. Never full redesign.

---

---

## 15. INTELLIGENCE ARCHITECTURE (full detail in AXIS_INTELLIGENCE_v1.md)

AI Models: Claude (email/voice/reasoning) · Perplexity (research/news) · Grok (social/entertainment)
Gemini Flash-Lite (triage//bin/sh.01) · Gemini Pro (reasoning) · GPT-5 (code/images) · DeepSeek (bulk) · Llama 4 (on-device)

Data Sources: Gmail · Calendar · Spotify · Reddit · YouTube · HN · X/Twitter · Stripe · Xero
OpenWeather · Google Maps · HealthKit · CoreLocation · Contacts · Perplexity web

Signal Over Noise: Gemini triage (95% discarded) → 5-layer filter → specialist model → output

Cost: ~.37/user/month vs  revenue = ~74% gross margin

---

## 16. COMPLETE FEATURE RANKING (24 features — AXIS_BUILD_FRAMEWORK_v2.md)

Tier 1: Smart notes · Status on anything · Expert intelligence · Context notes · Proactive skill suggestions · Planning partner
Tier 2: Ambient monitoring · Risk detection · Multi-turn execution · [Send] button · PWA · Follow-up tracker · Voice input
Tier 3: Daily briefing command · Relationship health · Weather+travel · Weekly email · Zapier · Stripe finance
Tier 4 (iOS/Phase 6): HomeKit · Hugging Face · Predictive scheduling · Dynamic Island · Phone agent

---

## 17. CURRENT STATUS

Date: 29 March 2026 — Session 7 in progress

Live in production:
- Backend: https://web-production-32f5d.up.railway.app
- Frontend: https://axis-web-chi.vercel.app
- Gmail OAuth (read + send) · Google Calendar OAuth · Spotify OAuth
- Dispatch v3 (triage + signal filter wired) every 15 min
- Morning digest 6:50AM Brisbane
- Meeting prep cron every 5 min
- Auto email drafts for urgency 8+ emails
- 6 skills seeded and live (email/calendar/finance/research/entertainment/site)
- Apprentice crons (Sunday 3AM + 4AM)
- Apprentice screen · Skills screen (live DB) · Settings (3 connected services)
- API keys: Anthropic + Clerk + Google + Spotify + Stripe + Gemini + Grok

Session 7 builds next:
context_notes · [Send] button · smart notes · status command · expert intelligence
voice input · PWA · follow-up tracker · weather+travel · ambient monitoring
risk detection · proactive suggestions · multi-turn execution · planning skill
weekly email · Zapier webhook · Stripe Connect

Context files (load all 6 every session):
- AXIS_CLAUDE.md
- AXIS_VISION_v1.md
- AXIS_BUILD_FRAMEWORK_v2.md
- AXIS_INTELLIGENCE_v1.md
- AXIS_BUILD_CHECKLIST_v2.md
- AXIS_SESSION_7_PLAN.md

Session start: cd ~/forge/axis-backend && claude
First message: Read all 6 AXIS context files. Session 7 — start with A1 context_notes.

**END OF AXIS CLAUDE.md v2.3**
