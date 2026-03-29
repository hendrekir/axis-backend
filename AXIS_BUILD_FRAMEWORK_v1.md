# AXIS — Build Framework
## How we build the product without losing the vision
### Session 5 · March 2026

---

## THE CORE ARCHITECTURE

Everything connects to one orchestration system. Not features bolted together. One spine.

```
DATA INGESTION
Gmail · Calendar · Spotify · Reddit · Maps · Health · GPS · Stripe · Slack · WhatsApp · News
↓
CONTEXT ASSEMBLY
User model + current state + relationships + patterns + history
↓
SKILLS ENGINE
User-defined or built-in workflows → routes to right model
↓
MULTI-MODEL ROUTING
Claude (nuance) · Perplexity (research) · Grok (speed) → right brain for right task
↓
OUTPUT ROUTING
Lock screen · Notification · Thread · Widget · Siri response · Silent · Action execution
↓
FEEDBACK LOOP
Every user action → apprentice model → improves routing → better decisions
```

This is the system. Everything gets built to serve this system.

---

## WHAT EXISTS (DO NOT REBUILD)

- FastAPI backend on Railway ✅
- Neon Postgres with memory tables ✅
- Gmail OAuth + dispatch job ✅
- Morning digest cron ✅
- APScheduler running internally ✅
- Clerk auth ✅
- Stripe paywall ✅
- React web app (6 screens) ✅
- CLAUDE.md in all repos ✅

Build ON these. Never around them.

---

## THE BUILD PHASES

### Phase 1 — Orchestration backbone (Weeks 1-2)
**Goal:** Replace hardcoded dispatch job with flexible skills engine

**axis-backend changes:**
```python
# New tables needed
skills               # user-defined or built-in skill definitions
skill_executions     # every time a skill runs, log it
api_connections      # which external APIs each user has connected
model_routes         # which AI model handles which skill type
```

**New endpoints:**
- GET/POST/PATCH /skills — CRUD for user skills
- POST /skills/{id}/run — manually trigger a skill
- GET /api-connections — which APIs the user has connected
- POST /orchestrate — the main dispatch → skills engine entry point

**The skills engine replaces the dispatch job.** Instead of one Claude prompt that does everything, each skill has its own prompt, its own data sources, its own output routing.

**Deliverable:** Backend can run user-defined skills. Dispatch job feeds into skills engine.

---

### Phase 2 — Multi-model routing (Week 2)
**Goal:** Claude is not the only brain

**New service: services/model_router.py**
```python
def route_to_model(task_type, context):
    if task_type == "research":
        return call_perplexity(context)
    elif task_type == "email_draft":
        return call_claude(context)  # nuance needed
    elif task_type == "quick_fact":
        return call_grok(context)
    elif task_type == "summarise_news":
        return call_perplexity(context)
    else:
        return call_claude(context)  # default
```

**API keys needed (Railway variables):**
- PERPLEXITY_API_KEY
- GROK_API_KEY (xAI)

**Deliverable:** Skills can specify which model processes them. Research skills use Perplexity. Email drafts use Claude. Speed tasks use Grok.

---

### Phase 3 — New data source integrations (Weeks 3-4)
**Priority order based on user value:**

1. **Gmail SEND** (highest value — close the action loop)
   - Add gmail.send OAuth scope
   - Voice model builder cron (Sunday 4AM — reads sent emails)
   - Draft reply endpoint that uses voice_patterns
   - [Send] button in thread and notifications

2. **Google Calendar OAuth** (meeting prep)
   - Connect calendar API
   - Meeting prep job: 30 min before every event
   - Push notification with context brief
   - Conflict detection

3. **Spotify OAuth** (entertainment layer)
   - Read current playing, liked songs, playlists
   - Morning brief includes music suggestion
   - "Play my focus playlist" skill

4. **Stripe OAuth** (finance intelligence)
   - Invoice monitoring
   - Overdue detection
   - Draft payment reminders in user's voice

5. **Perplexity integration** (research skill)
   - "Research [topic]" skill type
   - Morning brief includes relevant news
   - On-demand research via thread

6. **Reddit API** (entertainment + knowledge)
   - Follow communities
   - Surface trending posts in user's interests
   - Morning brief entertainment section

**Each integration follows the same pattern:**
- OAuth route in routes/
- Service in services/
- Adds data to dispatch context
- Skills can reference it

---

### Phase 4 — Apprentice model visibility (Week 4)
**Goal:** Users see what Axis learned. Trust is built through transparency.

**New endpoint: GET /apprentice**
Returns:
```json
{
  "voice_insights": ["You reply to clients formally, suppliers casually"],
  "time_patterns": ["Most productive 7-10AM", "Defer health tasks to Friday"],
  "relationship_insights": ["Reply to Marcus within 1 hour on average"],
  "attention_patterns": ["Act on finance notifications 89% of the time"],
  "learned_this_week": ["You dismissed 8 entertainment notifications — reducing frequency"]
}
```

**New screen in React + iOS:** Apprentice dashboard. Shows what the system knows. Users can correct it. Corrections feed back into user_model.

---

### Phase 5 — iOS app (Weeks 5-10)
**This is a ground-up build, not a port.**

**Philosophy:** Every screen is designed for one-handed use, voice-first, glance-readable.

**Core screens:**
1. **Lock screen widget** (primary surface — most seen)
   - One signal
   - One piece of relevant info (entertainment OR productivity)
   - One action button
   - Updates every 15 min from dispatch

2. **Control Centre tile** (Shazam-style quick access)
   - Tap → Axis overlay appears
   - Voice input immediately active
   - Shows current signal + 2 quick actions
   - Swipe up to dismiss

3. **Thread** (depth + history)
   - iMessage-style
   - All Axis messages + user messages
   - Skill results appear here
   - Long-form requests

4. **Skills** (customization)
   - Pre-built skills to enable/disable
   - User-built skill creator
   - Skill performance stats

5. **Apprentice** (what it learned)
   - Visual profile
   - Weekly learning summary
   - Correction interface

6. **Settings** (connections)
   - All OAuth connections
   - Model preferences
   - Notification preferences
   - Mode configuration

**iOS surfaces:**
- WidgetKit (lock screen + home screen widgets)
- App Intents (Siri + Shortcuts + widget buttons)
- ActivityKit (Dynamic Island — Phase 2)
- CoreLocation (GPS geofencing)
- HealthKit (sleep + energy)
- APNs (smart push notifications with action buttons)
- UNNotificationAction (notification action buttons)

---

### Phase 6 — OS moat (Funded by revenue, contractors)
- Dynamic Island Live Activities
- Apple Watch
- iOS Focus Mode API
- Android NotificationListenerService (acquisition demo)
- On-device ML (privacy-sensitive routing)

---

## HOW TO NOT LOSE THE VISION BETWEEN SESSIONS

**Before every session:**
1. Load AXIS_VISION_v1.md
2. Load CLAUDE.md
3. Ask: "Does what I'm about to build serve the orchestration layer?"

**The three questions for every feature:**
1. Is it flexible (user-customizable) or hardcoded?
2. Does it reduce friction or add it?
3. Does it feed the apprentice loop?

If a feature fails any of these — redesign before building.

**The anti-patterns to avoid:**
- Building separate features instead of extending the orchestration system
- Hardcoding skill logic instead of making it configurable
- Building UI before the backend data exists
- Optimising for demo instead of daily use
- Adding complexity without clear user value

---

## THE NORTH STAR CHECK

Before shipping anything, ask: "Does this bring us closer to the Jarvis moment?"

The Jarvis moment is: User wakes up, glances at lock screen, knows their day, handles everything with 3 taps, and goes about their life. Axis handled the rest.

If the feature doesn't contribute to that moment — cut it or defer it.

---

## SESSION START TEMPLATE

Every new session paste this:

```
Read AXIS_VISION_v1.md and CLAUDE.md.

We are building an orchestration layer — not features in isolation.
Today's session goal: [specific goal]

Before building anything, confirm:
1. Does this serve the orchestration architecture?
2. Is it flexible/customizable or hardcoded?
3. Does it reduce friction for the user?

Start with: [first task]
```

---

*This document is the build framework. The vision is in AXIS_VISION_v1.md.*
*Together they answer: what are we building and how do we build it without losing it.*

**END OF AXIS BUILD FRAMEWORK v1**
