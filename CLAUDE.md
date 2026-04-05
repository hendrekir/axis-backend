# AXIS — CLAUDE.md v5.1
## The complete product. Not the product we can build. The product we must build.
### Updated: April 2026 — Sessions 1–12 + Full feature audit synthesised
### Author: Hendre Kirchner · Dreyco Pty Ltd · Brisbane

---

## READ THIS FIRST

This is the single source of truth for Axis. Load at the start of every Claude Code or Xcode session.

**The rule:** Build on and tweak what exists. Never full redesign. Every session moves forward.

**Before building anything, ask three questions:**
1. Does this serve the orchestration architecture or is it a feature bolted on in isolation?
2. Is it flexible and user-customizable, or hardcoded?
3. Does it reduce friction for the user and feed the apprentice loop?

**The North Star check:** Does this bring us closer to the Jarvis moment?

**The Jarvis moment:** User wakes up, glances at lock screen, knows their day, handles everything with 3 taps, and goes about their life. Axis handled the rest.

---

## 1. WHAT AXIS IS

**One sentence**
Axis is an orchestration layer between the user and their digital life. It reads everything, thinks about it, and acts on it — so the user doesn't have to.

**The tagline**
"Extend the mind."

**The positioning line**
"Every other assistant waits. Axis watches."

**The Jarvis mental model**
Not the movie character — what people imagine when they hear that name. An intelligence that:
- Knows where you need to be and when
- Knows what needs handling before you ask
- Acts on your behalf and reports back
- Learns how you think and replicates it
- Connects every system into one coherent picture
- Is accessible instantly — voice, tap, glance

Axis is not a productivity app. Not a chatbot. Not a to-do list. It is the layer that sits above all of those.

**The three simultaneous roles — not modes, the baseline**

1. **The Remote** — Direct control. Sends emails. Creates calendar events. Chases invoices. Books things. One-tap approval is all it asks.
2. **The Assistant** — Anticipates before you ask. Reads overnight email, knows your day, surfaces what matters, handles what doesn't need you. Proactive, not reactive.
3. **The Apprentice** — Watches how you work. Learns your voice, patterns, preferences, relationships. Gets smarter every week. Becomes more you over time.

All three simultaneously. Not modes. Not features. The baseline.

**The goal**
8 minutes of phone time per day. 3 deliberate sessions. Everything else handled.

**The action gap (most important thing to understand)**
The product currently reads your world and tells you what to do. The symbiote reads your world and does it for you pending your approval. This is the entire product delta between 6/10 and 9.5/10.

---

## 2. THE IDEAL DAY

```
6:50 AM  Morning digest push arrives while user is asleep
7:00 AM  Session 1 (3 min) — open thread, handle 4 things with 4 taps. "Your move."
8:30 AM  GPS triggers Builder/Work mode. Widget updates. Context loads.
9:15 AM  Hands-free Siri capture: gloves on, no phone touch needed
10:00 AM Meeting prep notification 30 min before — key points from recent email with attendee
12:30 PM Session 2 (3 min) — midday check, capture loose thoughts
5:30 PM  Finance alert with one-tap approve
6:00 PM  Session 3 (2 min) — end of day.
8:00 PM  Daily journal question arrives. 30-second answer. Axis learns.
```

---

## 3. THE ORCHESTRATION ARCHITECTURE

```
DATA INGESTION
Gmail · Calendar · Spotify · Reddit · Maps · Health · GPS · Stripe · Slack · WhatsApp · News

↓ every 15 min · on change · on GPS trigger

TRIAGE (Gemini Flash-Lite — near-zero cost)
Filter noise before expensive models

↓ relevant + urgent only

CONTEXT ASSEMBLY (backend)
User model + current state + relationships + patterns + history + context_notes

↓ assembled into structured context

SKILLS ENGINE
User-defined or built-in workflows → routes to right model

↓

MULTI-MODEL ROUTING
Claude (nuance/drafts) · Perplexity (research/news) · Grok (speed/social) · Gemini Flash (triage)
→ right brain for right task

↓ returns structured JSON with routing instructions

OUTPUT ROUTING
Lock screen · Notification + action buttons · Thread · Widget · Siri response · Silent · Execution

↓ user acts (or doesn't)

FEEDBACK LOOP
Every action logged → apprentice model improves → Claude calls improve → better decisions
```

**The dispatch job (the heartbeat)**
Runs every 15 minutes. Pulls new data from all connected OAuth sources. Assembles context. Routes through skills engine. Right model processes. Outputs routed to correct surface. **95% of what Axis processes never reaches the user. That's the product.**

**Routing rules**

| Urgency | Actionable? | Goes to |
|---------|-------------|---------|
| 8-10/10 | Yes | Push notification immediately |
| 8-10/10 | No | Push + thread |
| 6-7/10 | Yes | Push during business hours |
| 5-6/10 | Yes | Morning digest |
| 3-5/10 | Info | Morning digest |
| 1-2/10 | No | Silent |

**Signal urgency language (never numbers in UI):**
- 8-10 → "Now" → red treatment
- 5-7 → "Today" → amber treatment
- 1-4 → "When you can" → violet treatment

---

## 4. MULTI-MODEL ROUTING

| Task type | Model | Why |
|-----------|-------|-----|
| Draft email in user's voice | Claude | Nuance, context, tone, voice matching |
| Research a topic | Perplexity | Real-time web knowledge, citations |
| Social/entertainment/trending | Grok | Real-time social, X integration |
| Email triage (bulk) | Gemini Flash-Lite | $0.01/1M tokens — cheap triage |
| Morning digest assembly | Claude | Synthesis, personalisation |
| Meeting prep | Claude + Perplexity | Context from emails + web context on attendee |
| Finance analysis | Claude | Reasoning about numbers |
| News brief | Perplexity | Current events, real-time |

Users never choose the model. Axis routes automatically.

---

## 5. THE SKILLS FRAMEWORK

Skills are not hardcoded features. Skills are user-defined workflows.

**Built-in skills (seeded automatically for every new user)**

| Skill | Data sources | Model | Output | What it does |
|-------|-------------|-------|--------|--------------|
| Email Intelligence | Gmail | Claude | Push | Ranks inbox, drafts replies in user's voice, sends on approval |
| Calendar Intelligence | Google Calendar + Gmail | Claude | Push | Meeting prep 30 min before every event, conflict detection, travel time |
| Finance Intelligence | Stripe + Xero | Claude | Push | Invoice monitoring, overdue alerts, draft payment reminders |
| Research Intelligence | Perplexity | Perplexity | Thread | Deep research on demand, real-time web knowledge |
| Entertainment Intelligence | Spotify + Reddit + News | Grok | Digest | Music recommendations, community content, trending |
| Morning Brief | All sources | Claude | Push + Thread | The daily digest — what matters, what Axis handled |

**User-built skills (the real product moat)**
Users can build any skill by describing it in plain language in the app. Axis generates the Claude prompt from natural language.

**Skills marketplace (future)**
Users share custom skills. Axis takes a cut.

---

## 6. THE MEMORY ARCHITECTURE

**Layer 1 — Session context (expires 48hrs)**
Fast access: current mode, today's calendar, last 10 messages, health context, active tasks.

**Layer 2 — User model (never expires, grows forever)**
- Voice patterns: sentence length, formality by recipient type, sign-offs, common phrases
- Relationship graph: contact importance scores, avg reply time, reply rate per contact
- Productive windows: when they actually complete tasks
- Completion rates: by category
- Notification response windows: when they act on pushes
- Defer patterns: what categories they consistently avoid
- Decision patterns: recurring decision types and outcomes (SESSION 11+)

**Layer 3 — Collective intelligence (anonymised, shared)**
Patterns that help new users immediately. Compounds with scale.

**The journal as data moat**
Every day Axis asks one rotating question (7 questions, one per day of week). The user answers. Claude extracts: people mentioned, projects mentioned, emotions/tone, decisions made. Appended to user.context_notes. **After 90 days of journal entries, the switching cost is enormous. Every day you don't journal, your Axis gets relatively dumber.**

**7 rotating journal questions**
1. Monday: "What's the one thing that would make this week feel like a success?"
2. Tuesday: "Who do you need to reach out to that you've been putting off?"
3. Wednesday: "What's working right now that you should do more of?"
4. Thursday: "What decision have you been avoiding? What's actually stopping you?"
5. Friday: "What did you learn this week — about work, people, yourself?"
6. Saturday: "What would you do tomorrow if it wasn't about being productive?"
7. Sunday: "What does next week need to feel like?"

---

## 7. THE IMPROVEMENT LOOP

**What gets logged:** Every action — send, edit, dismiss, defer, open, ignore — with full context.

**Weekly improvement job (Railway cron — Sunday 3AM):**
1. Analyse past 7 days of interactions
2. Compute accuracy rates for each prediction type
3. Call Claude with the week's interaction summary
4. Claude updates the user model JSON
5. Updated model feeds into all next week's Claude calls

**Voice model builder (Railway cron — Sunday 4AM):**
Pull last 50 sent emails → analyse sentence patterns → update voice_patterns → improved drafts next week.

**Evolution timeline:**
- Day 1-3: General heuristics + collective defaults
- Week 1-2: Pattern detection begins. Voice matching starts.
- Week 3-4: "It knows me." Drafts sound like you.
- Month 2-3: Anticipation. Axis predicts before you ask.
- Month 6+: Genuinely irreplaceable. Switching cost = 6 months of learning.

---

## 8. RAILWAY CRON JOBS

```
*/15 * * * *   Dispatch job — pulls data, skills engine, routes outputs
               6:50AM user TZ — morning digest fires
               5-min check — meeting prep for events starting in 25-35 min
               8:00PM user TZ — journal prompt push
               9:00AM user TZ — streak reminder if not opened
               Hourly — watch service checks
               
0 3 * * 0      Improvement job — Sunday 3AM, update user models
0 4 * * 0      Voice model builder — Sunday 4AM
0 5 * * 0      Collective patterns — Sunday 5AM
0 18 * * 0     Weekly retrospective email — Sunday 6PM
```

---

## 9. THE THREE CRITICAL PROMPTS

**Prompt 1 — Dispatch v2**
```python
DISPATCH_V2_SYSTEM = """
You are Axis, an ambient AI agent for {name}.
Mode: {mode} | Time: {current_time} | Timezone: {timezone}

Active skills: {active_skills}
User model summary: {user_model_summary}
Active tasks: {tasks}
Recent thread: {recent_context}

New inputs since last run:
{new_data}

For each input, return JSON array:
[{
  "title": "human-readable signal title",
  "urgency": 1-10,
  "actionable": true/false,
  "surface": "push|thread|widget|digest|silent",
  "action_type": "send_reply|create_event|send_invoice|create_task|notify|none",
  "pre_prepared_action": "draft text ready to send or task title",
  "skill_name": "which skill this belongs to",
  "model_to_use": "claude|perplexity|grok"
}]

CRITICAL: Never include triage reasoning, urgency scores, or classification language in pre_prepared_action.
Only title + draft content that the user will read directly.
"""
```

**Prompt 2 — Draft reply (Email Skill)**
```python
DRAFT_REPLY_SYSTEM = """
You are drafting an email reply on behalf of {name}.
You must write EXACTLY like them. Never sound like AI.

VOICE MODEL:
Average length: {avg_words} words
Formality: {formality_score}/10
Typical opening: "{typical_opening}"
Common phrases: {common_phrases}

EXAMPLE PAST REPLIES:
{example_replies}

EMAIL TO REPLY TO:
{email_content}

Draft the reply. Match the voice exactly.
"""
```

**Prompt 3 — Morning digest (6:50AM)**
```python
MORNING_DIGEST_SYSTEM = """
You are Axis. Generate {name}'s morning brief as thread messages.
Be specific, warm, direct. Never waffle.
Max 4 messages. Each under 80 words.
End with "Your move: [specific action]." — never tell them to put the phone down.
Include both productivity and entertainment signals.
"""
```

---

## 10. ALL SESSION 11+ FEATURES (LOCKED)

These are locked and must be built exactly as described. Do not deviate. Do not move deadlines.

### TIER 1 — Build first (Pro tier justification, $19/mo)

**Feature 1: Pre-meeting identity brief ("Insider information")**
30 seconds before every calendar event, Axis surfaces a full context brief. Who you're meeting, what you last discussed, what they care about, what you need to watch for. Pulls from Gmail thread history + Calendar + relationship graph + Perplexity web context. Push notification with "Read brief" → opens full screen overlay. 

Backend: calendar cron every 5 min checks for events starting in 25-35 min → runs brief generation → APNs push with category MEETING_PREP → [Read brief] deep links to `/meeting/{event_id}`.

**Feature 2: Silence as signal (centrepiece of Pro tier)**
Axis detects absence, not just presence. Client quiet after sending a quote — Axis notices. Project disappears from user's language in captures — Axis flags it. Colleague stops mentioning stressed topic — Axis notes it. 

Backend: Sunday 3AM improvement job runs silence detection over 30-day rolling window of thread messages and journal entries. Pattern: topic X mentioned N times in weeks 1-3, mentioned 0 times in week 4 = silence signal. Surfaces as amber "Silence detected" card in Situation with dashed border.

**Feature 3: Decision memory**
Every significant decision gets logged with full context — what the situation was, what was decided, why. Over time Axis builds a decision model. "Last time you faced a similar cash flow situation you held the line on pricing. Here's what happened."

Backend: in Thread, after any message where user makes a clear choice → Axis asks "Should I remember this decision?" → [Yes] → POST /decisions with full context → GET /decisions returns timeline → displayed in Apprentice view.

**Feature 4: Relationship health tracking**
Contacts with health scores. Silence detection on personal relationships, not just business. "You haven't spoken to Josh in 14 days — he was going through something last month."

Backend: relationship_graph table tracks interaction frequency per contact. Sunday 3AM job computes health scores. Contacts below threshold → surfaces as amber relationship card in Situation.

### TIER 2 — Build second

**Feature 5: Life map**
Visual graph of the user's life across 7 domains: Work, Money, Relationships, Health, Knowledge, Growth, Ideas. Populates automatically from journal entries and captures. Never manually entered. Axis surfaces cross-cluster insights: "Your three most successful client relationships all started from one referral."

iOS: Canvas-based, pinch to zoom, tap domain to expand. Gap domains rendered at 40% opacity with "X weeks quiet" label. Dot grid background. 

**Feature 6: Skill tree with verified achievements**
Tiers: Spark → Ember → Forge → Legend. Axis verifies achievements from real activity — emails sent, deals closed, journal streak, tasks completed. Users cannot inflate their rank.

Achievement unlock moment: subtle confetti animation. Share button → iOS share sheet → achievement card image. Growth mechanic.

**Feature 7: Stats / Charts screen**
Real data graphs with Axis-generated annotation below each chart. Chart.js or SwiftCharts. Annotations written by Claude: "Up 23% since you connected Stripe." Brisbane fuel prices from API. Active tasks over time. Axis build score.

**Feature 8: Library / Book tracker**
Books in progress with % completion. Recommendations personalised to current projects and knowledge gaps — not a bestseller list. Claude reads context notes and current journal themes to recommend.

### TIER 3 — Build third

**Feature 9: Ambient monitoring ("Watch this for me")**
Set a persistent watch on a person, topic, or contract expiry. Axis runs it silently and only interrupts when something material happens. "Watch Marcus's company for any news." Hourly cron, Perplexity for web topics, Gmail for person watches.

**Feature 10: Status updates on demand ("What's the status of X?")**
Axis synthesises emails, calendar, invoices, tasks, notes into a coherent update. Chief of staff feature. Thread command detected → status_service.py → Claude synthesises → returns as thread message.

**Feature 11: Proactive skill suggestions**
When Axis notices you've manually chased 4 invoices: "I noticed you've done this manually 4 times. Want me to automate it?" Pattern detection → natural suggestion → [Create skill] or [Not now]. Runs in Sunday improvement cycle.

**Feature 12: ElevenLabs TTS voice brief**
Play button on morning digest. ElevenLabs reads it aloud. Pro tier. Voice ID: EXAVITQu4vr4xnSDxMaL (Sarah). Free tier: 10k chars/month.

**Feature 13: Streak + re-engagement**
Flame icon, day count in Situation header. 9AM push if not opened: "Your Axis streak is at risk. X signals are waiting." A "streak day" = opened the app OR submitted a journal entry.

**Feature 14: Share achievement mechanic**
Tap unlocked skill badge → iOS share sheet → auto-generated achievement card. Growth lever.

**Feature 15: Brief time flexibility**
6:50AM is too rigid. Brief timing adapts to actual wake time (user-set in Settings, default 6:50AM). Not hardcoded.

**Feature 16: Wellbeing layer**
Water intake reminders (optional, user-controlled). Daily book recommendation from Library. The book recommendation is the differentiator — not the water tracking.

**Feature 17: Apprentice visibility dashboard**
Plain English summary of what Axis has learned. "You reply to clients formally, suppliers casually." "Most productive 7–10AM." Users can tap any insight to correct it. Corrections feed back into the model. Lives in sidebar, not a tab.

**Feature 18: Weekly retrospective email**
Sunday 6PM. Claude synthesises the week: decisions made, signals handled, things missed, what Axis learned. Sent via Resend to user's email. Pro tier.

**Feature 19: World intelligence brief (Perplexity-powered)**
News section in Brief tab. Personalised — reads context notes + journals to know what you care about. Gets smarter over time. Tags: Conflict/Markets/Tech/Local. Iran situation, fuel prices, AI news — but filtered and ranked to what matters to THIS user.

**Feature 20: Learn tab**
One crucial idea per day. Rotates topics: Financial literacy, Business, Psychology, History, Science. Chunks compound over time. "Next lesson →" advances to next chunk.

### TIER 4 — Session 20+

**Feature 21: Phone agent**
ElevenLabs + Twilio. "Call the restaurant and book a table for 2 at 7PM Friday." The movie moment. Not yet.

**Feature 22: Job site / field mode**
Low-data, simplified UI. Voice-first. GPS-triggered at saved location. Gloves mode.

**Feature 23: Shared intelligence (Team plan)**
Team plan ($29/mo, 5 members). If one person has a meeting with a client, the whole team's context about that client is surfaced. Axis becomes the team's shared memory. The B2B wedge.

**Feature 24: Quick capture (already built, needs polish)**
Purple + button, 52pt, slides up modal, Claude auto-classifies: note / task / meeting / signal / idea. Voice input in the modal.

**Feature 25: Voice feedback states (5 states)**
1. Idle — mic icon
2. Listening — animated waveform (3 bars, staggered bounce)
3. Processing — pulsing Axis mark, "Axis is thinking..."
4. Error — red mic icon, auto-resets 2s
5. Noise — confidence < 0.5 → "It's loud — tap to type"

---

## 11. THE UX ARCHITECTURE (LOCKED — from expert audit)

**The core tension that must be resolved:**
The product is built around a chat interface where users have to open the app. But the premise is Axis comes to you. Those two things work against each other. The fix: Situation Dashboard is the default home, not Thread.

**Navigation (locked — do not change)**

4 bottom tabs:
- **Situation** (default Tab 1) — morning brief, signals, MITs, insights
- **Axis** (Tab 2) — conversational thread, captures, NLP scheduling
- **Mind** (Tab 3) — Map / Skill Tree / Journal sub-tabs
- **Brief** (Tab 4) — Today / World / Learn sub-tabs

Right sidebar (hamburger) — slides in from RIGHT:
Signal · Schedule · Connections · Capabilities · Settings

**What is NOT a tab:** Signal, Skills/Capabilities, Apprentice, Settings, Schedule — all in sidebar.

**Scheduling rule:** Thread = WRITE (NLP via Claude → Axis adds to calendar). Sidebar Schedule = READ-ONLY calendar view. "Talk to Axis to schedule things. The Schedule sidebar shows you what's been scheduled."

**The Dream button**
In the Axis (Thread) tab header: a Dream button that compresses the conversation thread into a context card — key decisions, commitments, open loops, saved as a note — then resets the thread. Like Claude Code's context compression. This keeps the thread usable and focused without losing what was said.

**The Focus panel (floating popup)**
Above the command bar in the Axis tab: a collapsible "Today's focus" bar. Tap to expand. Shows:
- 3 MITs ranked by importance (each linked to an Achievement)
- Each MIT has a tap-to-complete checkbox
- Below the 3 MITs: the Sequence — daily necessities, unimportant but required (dentist, grocery run, call back)
- When all 3 MITs are done: "You did it. You can relax." banner in axisGreen

The dopamine system: achievement cannot be manually marked — Axis validates it from real activity. The anticipation of the next tier is more motivating than the reward itself. Locked achievements always visible.

**Signal urgency in all UI:** NOW / TODAY / WHEN YOU CAN. Never show the number.

**Apprentice:** Invisible. Runs in background. No tab. Surfaces insights passively in Thread ("I've noticed you respond faster to clients on Tuesdays..."). Has a visibility dashboard in Settings sidebar for users who want to see what it learned.

**Brain Dump:** Gone as a concept. Everything that was Brain Dump is now either:
- Quick Capture (floating + button)
- Journal (in Mind tab)
- Thread conversation (the Axis tab)

---

## 12. THE ACTION APPROVAL MODEL

Every Axis-executed action goes through one-tap approval:
- [Send] — execute immediately
- [Edit] — open draft for modification
- [Later] — snooze 2 hours
- [No] — dismiss, Axis notes the negative signal

No action is ever taken without user approval.

**Push notification categories:**
```
EMAIL_DRAFT: [Send] [Edit] [Later]
INVOICE_REMINDER: [Send] [Call them] [Snooze 2h]
MEETING_PREP: [Read brief] [Dismiss]
SIGNAL_ALERT: [Done ✓] [Snooze 2h]
```

---

## 13. SURFACE HIERARCHY (frequency of use)

1. Lock screen widget — one signal, one action, updates every 15 min
2. Notification + action buttons — context-aware, [Send] [Edit] [Later]
3. Control Centre tile — Shazam-style, tap → Axis overlay, voice immediately active
4. Siri App Intents — hands-free from anywhere
5. Situation tab — default home, situational awareness dashboard
6. Thread/Axis tab — conversation, capture, NLP commands
7. Dynamic Island — active agent status

**App Intents (Siri):**
```swift
"Hey Siri, add to Axis: [text]"              → thread + task queue
"Hey Siri, what's my Axis signal?"            → speaks back current top task
"Hey Siri, mark my Axis signal done"          → marks done, advances queue
"Hey Siri, brain dump in Axis"                → dictation mode
"Hey Siri, tell Axis: [anything]"             → adds to thread
"Hey Siri, switch Axis to Builder mode"       → changes context
"Hey Siri, send that Axis reply"              → sends pre-drafted reply
"Hey Siri, what's in my Axis brief?"          → reads back morning digest
```

---

## 14. DESIGN SYSTEM (locked)

**Colors**
```swift
Color.axisBackground  = #0C0A15  // Primary bg
Color.axisSurface1    = #110F1C  // Cards, sheets
Color.axisSurface2    = #1A1826  // Input fields
Color.axisViolet      = #8B5CF6  // Primary accent — ALL interactive elements
Color.axisGreen       = #10B981  // Success, done
Color.axisAmber       = #F59E0B  // Warning, in-progress
Color.axisRed         = #EF4444  // Destructive, urgent
Color.axisTextPrimary = #F0EEFF  // Body copy
Color.axisTextSecondary = #F0EEFF at 55% opacity
Color.axisTextMuted   = #F0EEFF at 28% opacity
```

**Typography**
- Syne ExtraBold 800 — display, screen titles, hero numbers
- Instrument Sans 400/500 — body copy, labels, thread messages
- JetBrains Mono 400/500 — timestamps, system data, stats

**The Axis mark (locked after Session 9)**
Artillery-round body (wide, squat), single porthole eye with glancing pupil (offset to 1 o'clock), lens bubble highlight opposite gaze, kinked antenna (straight up, bend right, ball at tip), peeking crop — body emerging upward, cut below eye level. Violet (#8B5CF6) on dark.

**Always dark — no light mode.**

---

## 15. iOS SURFACES (native, no web wrappers)

**Lock screen widget (accessoryRectangular)**
- Signal text (2 lines max)
- [Done] and [Later] buttons via App Intents
- Refreshes every 15 minutes

**Home screen medium widget (systemMedium)**
- Left: top signal + [Done] button
- Right: MIT count + next event time

**Push notification categories** (see Section 12)

**Deep link routing:**
```
axis://situation       → SituationView
axis://thread          → ThreadView (Axis tab)
axis://mind            → MindView
axis://brief           → BriefView
axis://signal          → Signal sidebar open
axis://meeting/{id}    → Pre-meeting brief full screen
axis://email/{id}      → Email draft in Thread
```

---

## 16. DATA SOURCES AND INTEGRATIONS

**Priority 1 — Live now**
- Gmail (read + SEND) — OAuth API
- Google Calendar — OAuth API
- Apple Calendar — EventKit (native iOS, no OAuth)
- Apple Health — HealthKit (native iOS)
- GPS / Location — CoreLocation (native iOS)
- Stripe / Xero — OAuth API
- Contacts — CNContactStore (native iOS)
- Share Extension — iOS native
- Perplexity — API (research skills, real-time web, news, meeting prep)
- Spotify — OAuth (music recommendations, contextual drive mode)

**Spotify is NOT a morning brief feature.** Spotify is a contextual ambient trigger: user gets in car, Maps opens, Axis auto-plays music for the drive. Morning digest is user-relevant news via Perplexity plus tasks/priorities for the day. These are completely separate features.

**Priority 2 — Phase 2**
- Slack, Outlook/M365, WhatsApp Business, Reddit, Twitter/X, YouTube
- iOS Focus Modes, Dynamic Island, Apple Watch

**iOS sandbox reality — accept this**
- iMessage — no third-party API.
- WhatsApp personal — no personal API.
- Other apps' notifications — blocked on iOS.

**The Android path to 9.5/10**
Android NotificationListenerService = one permission dialog, reads every app's notifications. Build after iOS hits $18K MRR.

---

## 17. BUSINESS MODEL

| Tier | Price | Includes |
|------|-------|---------|
| Free | $0 | 50 signals/mo, basic brief, 3 MITs, read-only |
| Solo | $9/mo | Unlimited, Gmail read+send, Calendar, ElevenLabs, widgets, all skills |
| Pro | $19/mo | Solo + pre-meeting brief, silence as signal, decision memory, Perplexity research |
| Team | $29/mo | Pro + shared intelligence, 5 members, manager view |

**Revenue milestones**
- $4.5K MRR (500 Solo) — proof of life
- $18.7K MRR (2,000 Solo + 50 teams) — HIRE TRIGGER: 2 Swift contractors
- $50K MRR — OS moat features (Dynamic Island, Watch, Android demo)
- $500K MRR — Apple acquisition conversations

---

## 18. TECH STACK

| Layer | Tool | Notes |
|-------|------|-------|
| iOS UI | SwiftUI + UIKit | Native only |
| OS surfaces | WidgetKit + ActivityKit | Lock screen + Dynamic Island |
| App integration | App Intents framework | Siri + Shortcuts + widget buttons |
| iOS data | EventKit · HealthKit · CoreLocation · CNContactStore | Native frameworks |
| Backend | FastAPI on Railway | Async throughout |
| Database | Neon PostgreSQL | SQLAlchemy async |
| AI primary | Claude Sonnet 4.6 | Dispatch, drafts, digest, skills |
| AI research | Perplexity | Real-time web, news, meeting prep |
| AI speed | Grok | Fast factual, social, recency |
| AI triage | Gemini Flash-Lite | Cheap noise filter ($0.01/1M tokens) |
| Auth | Clerk (production on tryaxis.app) | Sign in with Apple + Google |
| Payments | RevenueCat (iOS) + Stripe (web/team) | |
| Email | Resend | Onboarding, digests, team invites |
| Push (iOS) | APNs | Apple Developer required |
| Push (web) | VAPID / web-push | |
| Voice | ElevenLabs | Pro tier voice brief |
| Domain | tryaxis.app (Namecheap) | Google Workspace for dev@/hendre@ |
| Frontend hosting | Vercel | Auto-deploy on push |
| Backend hosting | Railway | Auto-deploy on push |

---

## 19. CURRENT DEPLOYMENT

| Resource | URL |
|---------|-----|
| Production frontend | https://tryaxis.app |
| Backend | https://web-production-32f5d.up.railway.app |
| Backend health | https://web-production-32f5d.up.railway.app/health |
| Privacy policy | https://tryaxis.app/privacy |
| Backend repo | github.com/hendrekir/axis-backend |
| Web repo | github.com/hendrekir/axis-web |
| iOS repo | github.com/hendrekir/axis-ios |
| Local | ~/forge/axis-backend · ~/forge/axis-web · ~/forge/axis-ios |

**Re-entry commands**
```bash
cd ~/forge/axis-backend
railway status
railway logs --tail 30
curl https://web-production-32f5d.up.railway.app/health
```

---

## 20. RAILWAY ENV VARS (complete list — 25 variables)

```
ANTHROPIC_API_KEY
CLERK_JWKS_URL          = https://tryaxis.app/.well-known/jwks.json
CLERK_PUBLISHABLE_KEY   = pk_live_...
CLERK_SECRET_KEY        = sk_live_...
DATABASE_URL
ELEVENLABS_API_KEY
FRONTEND_URL            = https://tryaxis.app
GEMINI_API_KEY
GOOGLE_CALENDAR_REDIRECT_URI = https://web-production-32f5d.up.railway.app/auth/calendar/callback
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
GOOGLE_REDIRECT_URI     = https://web-production-32f5d.up.railway.app/auth/gmail/callback
GROK_API_KEY
OPENWEATHER_API_KEY
PERPLEXITY_API_KEY
RESEND_API_KEY
SPOTIFY_CLIENT_ID
SPOTIFY_CLIENT_SECRET
SPOTIFY_REDIRECT_URI    = https://web-production-32f5d.up.railway.app/auth/spotify/callback
STRIPE_PRICE_ID
STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET
VAPID_PRIVATE_KEY
VAPID_PUBLIC_KEY
APNS_KEY_ID             (when Apple Developer activates)
APNS_TEAM_ID
APNS_BUNDLE_ID          = com.dreyco.axis
```

---

## 21. THE 12 RULES

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
12. **Build on and tweak what exists. Never full redesign.**

---

## 22. ANTI-PATTERNS TO AVOID

- Building features in isolation instead of extending the orchestration system
- Hardcoding skill logic instead of making it configurable
- Building UI before the backend data exists
- Optimising for demo instead of daily use
- Adding complexity without clear user value
- Treating entertainment as a secondary feature
- Letting dispatch output (triage reasoning, urgency scores) reach user-facing thread messages
- Showing construction/niche-specific language — everything must be general
- Calling the feature "Brain Dump" — it is "Journal" or "Capture"
- Tab bar with more than 4 items
- Signal as a tab — it is a sidebar
- Apprentice as a tab — it is invisible infrastructure
- Hardcoding timezones to Brisbane — all notifications are per-user timezone
- Any reference to specific people (Marcus, Greenfield, Vantage) in placeholder text

---

## 23. WHAT THE 20-EXPERT AUDIT FOUND (from product audit session)

The audit scored the product 5.8 at the time of review. The gaps in order of severity:

**Critical (fixed or fixing):**
- C1 — Dispatch output leaking internal reasoning to thread messages (fixed in services/dispatch.py)
- C2 — "Brain dumps" language in UI (fixed, now "captures")
- C3 — No privacy policy (fixed, live at tryaxis.app/privacy)
- C4 — iOS not wired to backend end-to-end (Session 12 priority)

**High:**
- No proper onboarding (now built — 5 screens, first signal on Screen 5)
- Situation not loading properly (Clerk JWKS URL mismatch)
- Gmail OAuth broken on production domain (redirect_uri_mismatch fixed)
- Thread is chatbot-first, not ambient-first (Situation Dashboard now default)

**Medium:**
- Signal as tab instead of sidebar (fixed in nav restructure)
- No widget (needs Apple Developer account — pending)
- No push notifications on iOS (needs APNs — pending activation)
- Brief "Learn" tab not cycling lessons (fixed — 4 rotating chunks)
- Mind page domain cards hardcoded (needs live API data)
- Voice input lacks proper state machine (5-state spec in Section 10, Feature 25)

**Expert panel key findings:**
- iOS UX Designer: Tab bar correctly at 4 items now. Haptic feedback spec needed.
- Cognitive Psychologist: Situation Dashboard fixes information density. Good.
- Notification Design Expert: Notification categories spec now defined. APNs needed.
- Widget Design Expert: Widget spec defined. Needs Apple Developer.
- Scheduling Expert: NLP scheduling via Thread is correct. Confirmation flow now defined.
- Voice UX Designer: 5-state voice feedback spec now locked in Session 11+ Feature 25.
- Retention Expert: Streak + journal prompt push are the right retention mechanics.

---

## 24. CURRENT STATUS AND WHAT'S BLOCKING

**Authentication (ACTIVE BLOCKER):**
- Clerk JWKS URL issue — production instance on tryaxis.app, CLERK_JWKS_URL set to https://tryaxis.app/.well-known/jwks.json in Railway — still returning 401s on all API calls
- Root cause: JWKS client may be caching the dev URL or Clerk DNS CNAME not fully propagated
- Fix: verify curl https://tryaxis.app/.well-known/jwks.json returns valid JWKS JSON

**Apple Developer (PENDING):**
- Purchased — pending Apple activation (24-48hrs)
- Needed for: APNs push notifications, WidgetKit, TestFlight, Sign in with Apple

**Gmail OAuth (PARTIALLY WORKING):**
- OAuth flow completes (callback hits Railway, returns 307)
- Token storage may fail if user row can't be validated (auth 401)
- Retry after auth is fixed

**Next priorities after auth fixed:**
1. Gmail SEND — add gmail.send scope, voice model cron, [Send] button in notifications
2. iOS wired end-to-end — Clerk token flowing to Railway backend
3. APNs registration when Apple Developer activates
4. Pre-meeting brief (Session 11+)
5. Silence as signal (Session 11+)

---

## 25. COMPREHENSIVE BUILD CHECKLIST

### ✅ DONE (Sessions 1–12)

**Backend infrastructure**
- [x] FastAPI backend on Railway with APScheduler
- [x] Neon Postgres, SQLAlchemy async, pool_pre_ping=True
- [x] Clerk auth (production instance on tryaxis.app)
- [x] All 20+ database tables: users, tasks, thread_messages, journal_entries, user_model, interactions, relationship_graph, patterns, sent_emails_cache, collective_patterns, skills, skill_executions, api_connections, model_routes, notes, watches, follow_ups, weekly_retrospectives, skill_suggestions, push_subscriptions
- [x] Stripe paywall ($9/mo, webhook for plan upgrade)
- [x] Gmail OAuth (read + send scope)
- [x] Google Calendar OAuth
- [x] Spotify OAuth
- [x] 6 built-in skills seeded on user creation
- [x] Dispatch v3 with triage + signal filter + skills engine + calendar
- [x] Morning digest cron (per-user timezone)
- [x] APScheduler (dispatch + digest + improvement + voice rebuild + watches + streak reminders + journal prompts + meeting prep + retrospective)
- [x] Perplexity service, Grok service, Gemini Flash service
- [x] Smart notes (save/search/recall in Thread — "remember X", "what do I know about X")
- [x] Context notes (injected into every Claude call)
- [x] Status intelligence ("what's the status of X")
- [x] Watch service ("watch this for me")
- [x] Follow-up tracker wired into dispatch
- [x] Weekly retrospective email (Sunday 6PM)
- [x] Journal system (daily questions, Claude extraction, context feed)
- [x] Apprentice dashboard (GET /apprentice)
- [x] Streak system
- [x] Quick capture (POST /quick-capture with Claude classification)
- [x] NLP scheduling (POST /schedule/parse + confirm)
- [x] Weather in morning brief (OPENWEATHER_API_KEY)
- [x] Web push notifications (VAPID)
- [x] ElevenLabs TTS (POST /tts)
- [x] Proactive skill suggestions (Sunday apprentice cycle)
- [x] dispatch output sanitised (no triage language in thread messages)
- [x] Privacy policy (tryaxis.app/privacy)
- [x] Google Workspace (dev@tryaxis.app, hendre@tryaxis.app)

**Frontend (tryaxis.app)**
- [x] Situation Dashboard as default home (4 bottom tabs)
- [x] Axis tab (conversation, topic bubbles, voice input, Dream button)
- [x] Mind tab (Map / Skill Tree / Journal sub-views)
- [x] Brief tab (Today / World / Learn sub-views)
- [x] Sidebar (Signal / Schedule / Connections / Capabilities / Settings)
- [x] Onboarding (5 screens, first signal generated on entry)
- [x] Gmail connect + Calendar connect + Spotify connect
- [x] Skills screen live from DB
- [x] Apprentice dashboard
- [x] Quick capture floating button
- [x] Voice input (MicButton, 5 states)
- [x] [Send] button on email drafts
- [x] Mode switcher (Personal / Work / Builder / Student / Founder)
- [x] Streak display
- [x] PWA manifest
- [x] TTS speaker button on Thread messages
- [x] Context notes textarea in Settings
- [x] MIT completion with "You did it. You can relax." banner
- [x] Journal rotating daily questions
- [x] ElevenLabs play button on Brief

**iOS app**
- [x] Xcode project at ~/forge/axis-ios
- [x] All 7 screens scaffolded
- [x] APIService + KeychainService
- [x] Clerk iOS SDK installed
- [x] Simulator bypass for testing
- [x] Design system files (Colors.swift, Typography.swift, Spacing.swift)
- [x] AxisCard, AxisTag, AxisButton, AxisTextField, AxisMark components
- [x] Navigation shell (MainTabView + SidebarView — 4 tabs)

**Brand**
- [x] Axis mark (locked — artillery round, glancing pupil at 1 o'clock, kinked antenna, peeking crop)
- [x] 5 SVG files (full, app icon, wordmark, mono, white)
- [x] Color system (#8B5CF6 violet, #0C0A15 background)
- [x] Font stack (Syne + Instrument Sans + JetBrains Mono)

### 🔲 NEXT (blocking right now)

- [ ] Fix auth 401s — Clerk JWKS URL with production instance
- [ ] Apple Developer account activation (purchased, pending)
- [ ] Gmail SEND fully wired (scope added, voice model cron, [Send] in notifications)
- [ ] iOS wired end-to-end (Clerk token → Railway 200 responses)

### 🔲 SESSION 11+ (all features listed in Section 10)

- [ ] Pre-meeting identity brief
- [ ] Silence as signal detection
- [ ] Decision memory
- [ ] Relationship health tracking
- [ ] Life map (iOS Canvas)
- [ ] Skill tree with verified achievements
- [ ] Stats / Charts screen with Axis annotations
- [ ] Library / Book tracker
- [ ] APNs push notification registration
- [ ] WidgetKit lock screen widget
- [ ] App Intents for Siri (all 8 commands)
- [ ] HealthKit integration
- [ ] CoreLocation for auto mode switching
- [ ] RevenueCat paywall
- [ ] TestFlight build + submission

---

## 26. COMPETITIVE CONTEXT

**Apple's Siri gap = Axis's market**
Apple's AI group has been internally called "AIMLess." The WWDC 2024 demo features (Siri accessing emails, messages, photos) were described by employees as "effectively fictional" — never worked on test devices. Apple knows it's broken. Axis is what Siri was supposed to be.

**The acquisition thesis**
Build iOS to prove the concept. Build Android to demonstrate the full symbiote vision (NotificationListenerService = reads every app's notifications). Use Android demo to have the acquisition conversation with Apple. "Here's your platform running at 9.5/10 on Android using an official API. Give us the native iOS APIs and it runs at 10/10."

---

*Copy this file to ~/forge/axis-backend/CLAUDE.md, ~/forge/axis-web/CLAUDE.md, ~/forge/axis-ios/CLAUDE.md*
*Load at the start of every session. Never start without it.*
*END OF AXIS CLAUDE.md v5.1*
