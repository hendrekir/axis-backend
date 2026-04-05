# AXIS — CLAUDE.md v6.0
## The complete product. Locked. No deviation.
### Updated: April 2026 — Sessions 1–13 synthesised. Vision finalised.
### Author: Hendre Kirchner · Dreyco Pty Ltd · Brisbane

---

## READ THIS FIRST — EVERY SESSION

This is the single source of truth for Axis. Load at the start of every Claude Code or Xcode session. Read it fully before touching any code.

**The rule:** Build on and tweak what exists. Never full redesign. Every session moves forward.

**The three questions before building anything:**
1. Does this serve voice, widget, or notifications — the three surfaces that are the actual product?
2. Does it work before OAuth is connected — day one value without setup friction?
3. Does it reduce the number of times the user needs to open the app?

**The success metric:** User wakes up, AirPods in, Axis briefs them in 90 seconds. Three notifications during the day, each handled in one tap. App opened zero times. Axis was working the whole time. That is the product working correctly.

---

## 1. WHAT AXIS IS

**One sentence:**
Axis catches what falls out of your head and handles it — so you can be present in your actual life.

**The positioning line:**
"Everything you're trying to hold in your head. Held."

**The human framing:**
The note on the fridge. Everywhere you go.

Everyone understands a fridge note. It catches the thought at the moment you know you'll forget. It works because it's always there when you walk past. Axis is that note — everywhere. On your lock screen, in your ear, on your wrist. It catches the thought the moment you have it and surfaces it at the moment it actually matters. Not when you happen to walk past the kitchen.

**The fridge note's one flaw:** It only works in one room. Axis fixes that.

**What Axis is not:**
- Not a productivity app
- Not a chatbot you open and ask things
- Not a business tool
- Not an AI assistant that waits to be summoned
- Not another app competing for your attention

**The three things Axis does:**

1. **Catches** — anything you say, type, or photograph. No category, no tag, no friction. Just caught. Voice, text, photo. The moment you think it.

2. **Coordinates** — quietly handles what it can without asking. Books the calendar gap. Drafts the reply. Finds the podcast. Calculates travel time. Does the labour of following through that humans are bad at.

3. **Reaches** — delivers the right thing at the right moment through surfaces you're already looking at. Lock screen. Notification. Voice. Never makes you open an app to act on something simple.

**The fundamental shift from every other product:**
Every other app waits. You open it, it responds. You set a reminder, it fires. You ask a question, it answers. Axis doesn't wait. It watches. It notices. It acts. It reaches you. That difference — initiative — is the entire product.

---

## 2. THE PRIMARY MARKET

**Primary: Normal people who want their life held together.**

Not founders specifically. Not knowledge workers specifically. Anyone who has ever written a note on a fridge, set a reminder they dismissed, or said "I'll remember that" and didn't. That is every adult on earth.

The problem isn't disorganisation. The problem is that the human brain wasn't designed to hold a to-do list, a social calendar, a news feed, a shopping list, and a relationship maintenance schedule simultaneously while also trying to be present in their actual life.

Axis holds it. They live it.

**What normal people actually lose track of:**
- They meant to call their mum back three days ago
- They said they'd look into that insurance quote and forgot
- They've been meaning to book the dentist for four months
- They told their friend they'd send that article and never did
- They want to read more but somehow never do
- They started a course, did two lessons, and drifted
- The gym streak broke and they haven't gone back
- They keep meaning to sort the garage

These aren't business problems. They're the texture of a life where good intentions outpace follow-through.

**Secondary: Solo founders, freelancers, tradespeople running a business.**
High willingness to pay. Complex external lives — inboxes, invoices, clients, calendars full of other people. The Pro tier ($19/month) is built for them. But they are not the only market.

**Do not target:**
- Students — low WTP, wrong life stage
- Enterprise — too early, no compliance infrastructure

**The three audience framings:**

For normal people: "Everything you're trying to hold in your head. Held."
For solo founders: "Your chief of staff. At $9 a month."
For tradespeople: "What your phone should have been doing all along."

---

## 3. THE THREE SURFACES — THE ACTUAL PRODUCT

The app is not the product. The app is the configuration layer. The actual product is delivered through:

**Voice. Widgets. Notifications.**

The user never needs to open Axis for Axis to be working. The app is where they set things up, review what happened, and go deeper when they want to. Daily interaction with Axis is: glance at the widget, tap the notification, talk to it hands-free. Three seconds. One tap. Then put the phone down.

### Surface 1 — Lock screen widget (most important screen in the product)

More important than any tab in the app. First thing seen when the phone is picked up. One signal. One action button. Updates every 15 minutes from the dispatch loop.

7AM: top signal from overnight
3PM Thursday: "Leave in 18 minutes for school pickup"
Saturday morning: nothing work-related — personal only

The intelligence decides what to show. The user never configures it.

### Surface 2 — Notifications (primary interrupt)

Not alerts. Decisions delivered to the lock screen.

"Invoice overdue — Tom Harris, $3,400. [Send reminder] [Snooze]"
"Meeting in 28 minutes — Sarah Chen. Last discussed: the Henderson project. [Read brief]"
"You haven't spoken to Josh in 3 weeks. [Message him]"
"Quiet gap 2-3PM. You've been meaning to call the dentist. [Add to calendar]"

Maximum 2-3 notifications per day. The discipline is knowing what NOT to interrupt with. 95% of what Axis processes never becomes a notification. That restraint is the product.

### Surface 3 — Voice (primary input and output)

Input — capture anything hands-free:
"Hey Siri, add to Axis — call the insurance company about the renewal"
"Hey Siri, remind me to check in on Josh this week"
"Hey Siri, what's on today?"
"Hey Siri, push my 3 o'clock — I'm running 10 minutes late"

Output — AirPods morning brief. Plays while making coffee. No screen. Calm voice. 90 seconds. What matters today, what Axis caught overnight, two things that need a decision.

The AirPods angle is the most underrated surface. AirPods are in people's ears for hours. Axis whispering "leave in 10 minutes for school pickup" through AirPods is more intimate and useful than any screen notification.

### Dynamic Island — active state indicator

When Axis is actively handling something — sending an email, researching, watching a situation — it lives in the Dynamic Island. Always visible. User knows it's working without opening anything.

### The app's actual role

Configuration: connect services, set preferences, tell Axis what matters.
Review: see what Axis handled, what it caught, what it learned.
Depth: go deeper on anything surfaced. Full email thread, full meeting brief.
Journal: daily question. The intelligence input that makes everything smarter.

That is all the app needs to do. Measure success by how rarely it needs to be opened.

---

## 4. THE CAPTURE LAYER — DAY ONE VALUE

**Critical rule: Axis must be valuable before any OAuth connection is made.**

Current onboarding starts with "connect your Gmail." This is wrong. It gates day one value behind setup friction. The correct onboarding starts with capture.

**The correct first screen after the brand moment:**
"What have you been meaning to do?"

One text field. One voice button. No connections required. The user types or says anything — "call mum," "sort the garage," "book that dentist," "send Tom the article I promised." Axis catches it. No category. No due date. No project. Just caught.

The intelligence layer runs in the background — classifies each capture, decides when and how to surface it, builds context from patterns across captures. The user never sees the machinery.

**Natural language capture auto-classification:**

"Remind me to check on Sarah — she was going through something"
→ Relationship task, surfaces after 7 days if no contact detected

"I want to read more about stoicism"
→ Discovery intent, feeds into daily recommendation

"Book dentist sometime next month"
→ Calendar task, Axis finds a gap and suggests a time

"Find a plumber — the tap has been dripping two weeks"
→ Research task, Axis finds options and surfaces with quotes

"Call mum this week"
→ Relationship task, surfaces Wednesday when calendar is light

"Send Tom the compound interest article"
→ Follow-up task, surfaces next time email to Tom is opened

Claude classifies in real time on backend. User sees none of this — just that things get handled.

**OAuth as the upgrade, not the gate:**
After first capture is saved, show: "Connect Gmail to let Axis read your inbox and handle email." Optional. Not required. The product works without it and gets smarter with it.

---

## 5. THE COORDINATION LAYER — DOING THE LABOUR

Axis doesn't just remind. It closes the loop.

**Email:**
Reads inbox overnight. Morning brief in plain language — "Three emails need attention, one is urgent, two are FYIs. Your accountant sent the quarterly figures." Drafts replies in user's voice. Sends on one-tap approval.

**Calendar:**
Finds gaps, schedules captured tasks, warns about conflicts. Calculates travel time. "Leave in 18 minutes — the school is 14 minutes away and you need 4 minutes to get to the car." Sets alarms for early starts without being asked. "You mentioned an early Thursday — I've set 6AM."

**Travel time (critical feature for normal people):**
Google Maps API or Apple Maps + calendar events. The school pickup example is the product in one sentence. User captured "pick up kids at 3:30 school" → Axis reads the calendar, knows the school location, calculates drive time, sends a notification at the right moment. This is what Siri promised in 2011. Nobody delivered it. Axis does.

**Shopping and discovery:**
User captured "find a good standing desk under $400." Axis searches across sources, finds the best option, surfaces it with a link. Not Amazon-specific. Best result from anywhere.

One personalised recommendation per day — one podcast, one article, one book — drawn from the memory layer, not a generic bestseller list. Axis knows from journal entries and captures what the user is thinking about right now. The recommendation is relevant to their life this week.

**News:**
Three things worth knowing today, filtered through what the user actually cares about. Not a firehose. Personalised via Perplexity. Gets more relevant every week as the memory layer grows.

**Relationships:**
"You haven't spoken to Josh in 3 weeks — he was going through something last month." This is the friendship maintenance layer nobody else has. Requires relationship graph built from captures and journal. Axis knows who matters to the user because the user has told it, directly or indirectly.

**Finance:**
Invoice overdue, bill coming, spending pattern worth noting. One notification, one action. High perceived value, low build cost.

---

## 6. THE MEMORY LAYER — THE MOAT

Everything that makes Axis smarter than a generic AI assistant.

**Layer 1 — Captures (immediate)**
Every thought caught, classified, surfaced at the right moment. The raw input.

**Layer 2 — User model (cumulative)**
Built weekly from all interactions:
- Voice patterns — how they write, their vocabulary, their tone
- Relationship graph — who matters, interaction frequency, last contact
- Productive windows — when they actually complete things
- Interest graph — what they read, what they ask about, what they capture
- Decision patterns — how they make decisions, what they defer
- Life domains — which areas of life are active vs quiet

**Layer 3 — Journal intelligence (compounding)**
Daily question, 30-second answer. Claude extracts entities, emotions, decisions, people, projects. Appended to the user model. After 30 days Axis knows how this person thinks. After 90 days the switching cost is enormous — they're not leaving an app, they're leaving a record of how they think.

**The 7 rotating journal questions:**
Monday: "What's the one thing that would make this week feel like a success?"
Tuesday: "Who do you need to reach out to that you've been putting off?"
Wednesday: "What's working right now that you should do more of?"
Thursday: "What decision have you been avoiding? What's actually stopping you?"
Friday: "What did you learn this week — about work, people, yourself?"
Saturday: "What would you do tomorrow if it wasn't about being productive?"
Sunday: "What does next week need to feel like?"

**The moat features no competitor will build:**

Silence as signal — noticing what stopped happening. Client quiet after a quote. Project disappeared from language. Relationship going cold. Requires accumulated data. Cannot be faked on day one. Competitors optimise for engagement. Axis optimises for awareness of absence. Philosophically opposite goals.

Decision memory — logs significant decisions with context, surfaces patterns over time. "Last time you faced a similar cashflow situation you held the line on pricing. Revenue recovered in 6 weeks." Becomes a personal board of directors.

These two features are the Pro tier ($19/month). They require the memory layer to exist first. They cannot be rushed.

---

## 7. THE ANDROID VISION

iOS is the proof of concept. Android is the full product.

Android's NotificationListenerService gives Axis access to every notification from every app — WhatsApp, Slack, banking, delivery, iMessage on Android, everything — with one permission dialog. The iOS sandbox prevents this entirely.

On Android, Axis sees your whole life, not just Gmail and Calendar. Every message from every app. Every alert. Every notification that matters and every one that doesn't. The ambient intelligence layer becomes complete.

Build Android after iOS hits $18K MRR. The Android demo is also the Apple acquisition pitch. "Here's your platform running at 9.5/10 on Android using an official API. Give us the native iOS APIs and it runs at 10/10."

**The browser extension angle:**
Chrome extension reads browser notifications, captures context from active tabs. No App Store required. Reaches people who won't download an app. Low build cost, wide distribution. Build alongside Android.

---

## 8. THE WIDGET PLATFORM — LATER

Eventually Axis becomes the intelligence layer that any widget can consume. Not configured by users — curated by Axis in real time. "What should I show this user right now?" Axis answers. The widget renders it.

No widget app does this because no widget app has an intelligence layer. Axis already has the intelligence. The widget platform is the natural extension.

**Build order:** Axis widget works for Axis users first → prove the intelligence layer → open the API → widget platform emerges from proven foundation.

**Do not build the widget platform now.** Nobody pays for an intelligence API until the intelligence is proven. Finish Axis first.

---

## 9. THE ORCHESTRATION ARCHITECTURE

```
DATA INGESTION
Captures (voice/text/photo) · Gmail · Calendar · Spotify
Apple Health · GPS · Stripe · WhatsApp Business · News

↓ on capture · every 15 min · on GPS trigger · on webhook

TRIAGE (Gemini Flash-Lite — near-zero cost)
Filter noise. Only pass relevant + time-sensitive items.
Skip entirely if new_data_parts is empty.

↓ relevant only

CONTEXT ASSEMBLY
User model + captures + relationships + patterns +
journal intelligence + current schedule + location

↓

SKILLS ENGINE
Routes to correct skill based on data type and urgency

↓

MULTI-MODEL ROUTING (via OpenRouter)
Claude — nuanced, drafts, coordination, journal
Perplexity — real-time web, research, news, discovery
Grok — social, speed, trending
Gemini Flash — triage, bulk classification

↓

OUTPUT ROUTING
Notification + action buttons · Widget update ·
Voice response · Silent (95% of processing) · Action execution

↓ user acts (or doesn't)

FEEDBACK LOOP
Every action logged → memory layer improves →
better decisions → higher signal quality over time
```

**The dispatch discipline:**
95% of what Axis processes never reaches the user. The skill is knowing what to suppress, not what to surface. Noise kills the product faster than missing a signal.

**Skip-if-empty rule (must be live):**
```python
if not new_data_parts and not pending_captures:
    skip_claude_call()
    # Still run: meeting prep check, travel time, skill triggers
```

---

## 10. MULTI-MODEL ROUTING VIA OPENROUTER

Single service. One API key. Automatic fallback. Cost monitoring.

```python
TASK_MODEL_MAP = {
    "triage":        "google/gemini-flash-1.5",
    "capture_classify": "google/gemini-flash-1.5",
    "dispatch":      "anthropic/claude-sonnet-4-6",
    "draft_reply":   "anthropic/claude-sonnet-4-6",
    "digest":        "anthropic/claude-sonnet-4-6",
    "research":      "perplexity/sonar-online",
    "news":          "perplexity/sonar-online",
    "discovery":     "perplexity/sonar-online",
    "meeting_prep":  "anthropic/claude-sonnet-4-6",
    "social":        "x-ai/grok-beta",
}
```

Route everything through `services/openrouter_service.py`. Remove separate claude_service, perplexity_service, grok_service, gemini_service. One service replaces four.

---

## 11. RAILWAY CRON JOBS

```
*/15 * * * *   Dispatch — pulls data, skips if empty, routes outputs
               6:50AM user TZ — morning digest + AirPods brief
               T-30min check — meeting prep for upcoming events
               T-leave check — travel time notification
               8:00PM user TZ — journal prompt
               9:00AM user TZ — streak reminder if not captured today

0 3 * * 0      Improvement job — update user models
0 4 * * 0      Voice model rebuild from sent emails
0 5 * * 0      Collective patterns update
0 18 * * 0     Weekly retrospective email
```

---

## 12. THE CRITICAL PROMPTS

**Dispatch v3 — capture-aware:**
```python
DISPATCH_V3_SYSTEM = """
You are Axis. Ambient intelligence for {name}.
Time: {current_time} | Timezone: {timezone}

User model: {user_model_summary}
Recent captures: {pending_captures}
Active tasks: {tasks}
Schedule today: {todays_events}

New data since last run:
{new_data}

Return JSON array. Each item:
{
  "title": "plain English, no jargon",
  "urgency": 1-10,
  "surface": "notification|widget|voice|silent",
  "action_type": "send_reply|create_event|set_alarm|search|none",
  "pre_prepared_action": "ready to execute or empty",
  "when_to_surface": "now|morning|quiet_gap|contextual"
}

RULES:
- Most items should be "silent" — process but don't interrupt
- Notification urgency threshold: 7+
- Never repeat a signal surfaced in last 48hrs unless status changed
- Never include triage reasoning in pre_prepared_action
- Match tone to user's voice model
"""
```

**Capture classifier:**
```python
CAPTURE_CLASSIFY_SYSTEM = """
Classify this capture into one of:
- relationship_task (involves a person)
- calendar_task (needs scheduling)
- research_task (find information or product)
- reminder (time or location based)
- discovery_intent (want to learn about something)
- follow_up (something promised to someone)
- personal_goal (habit, aspiration, improvement)

Extract:
- person (if any)
- urgency (1-10)
- suggested_surface_time (morning|quiet_gap|contextual|weekly)
- location_trigger (if location-relevant)

Return JSON only.
"""
```

---

## 13. THE BUILD ORDER — LOCKED

Do not deviate. Do not build features out of order. Each step unlocks the next.

### NOW — This week

**Step 1: Get on real device**
Clerk token flowing to Railway. Axis running on a physical iPhone with a real inbox. Everything before this is simulation.

**Step 2: Signal deduplication**
`dispatched_signals` table. Never surface the same signal twice in 48hrs without a status change. This is the difference between a product people keep and one they delete in a week.

**Step 3: Skip-if-empty dispatch**
One if-statement. Cuts cost 60%. Should already be live.

**Step 4: OpenRouter**
Replace 4 separate API integrations with one service. Triage through Gemini Flash immediately.

### NEXT — Two weeks

**Step 5: Capture-first onboarding**
Remove OAuth as the first screen. Replace with "What have you been meaning to do?" — one text field, one voice button. OAuth is the upgrade screen, not the gate. Day one value before any setup.

**Step 6: Natural language capture classifier**
POST /capture receives any text or voice transcript. Claude classifies into task type, extracts person/urgency/timing. No user-facing categories. Just caught and handled.

**Step 7: Travel time in dispatch**
Google Maps API + calendar events. School pickup notification. Meeting departure alert. Leave now push. The feature Siri promised in 2011.

### WHEN APPLE DEVELOPER ACTIVATES — Same day

**Step 8: APNs with action buttons**
Notification categories: [Done] [Snooze] [Later] inline. No app open required to act. First real ambient surface.

**Step 9: Lock screen widget**
WidgetKit. One signal. One button. Fed by dispatch in real time. This single surface communicates the entire product value proposition.

**Step 10: App Intents for Siri**
Eight voice commands. Capture and query hands-free. The tradesperson use case depends entirely on this.

### MONTH TWO

**Step 11: Calendar actions — Axis writes, not just reads**
"Find me a time for the dentist next week" creates the event. User approves in one tap. This is coordination, not just awareness.

**Step 12: Daily discovery recommendation**
One podcast, one article, one thing per day from the memory layer. Personalised. Not generic. Appears in Brief tab and morning digest.

**Step 13: AirPods brief**
ElevenLabs reads the morning digest aloud. Plays through AirPods while making coffee. No screen. Already integrated — just needs the audio output routing.

**Step 14: Dynamic Island live activity**
Active agent status. "Axis is handling 3 things." Always visible without opening the app.

### MONTH THREE — THE MOAT

**Step 15: Silence as signal**
Pattern detection on what stopped appearing in captures and journal. Surfaces relationship drift, project abandonment, forgotten follow-ups. Pro tier.

**Step 16: Decision memory**
Log decisions with context. Surface patterns over time. Personal board of directors. Pro tier.

**Step 17: Android**
NotificationListenerService. Full ambient vision. Every notification from every app. The real product.

---

## 14. BUSINESS MODEL

| Tier | Price | Core value |
|------|-------|------------|
| Free | $0 | 50 captures/month, basic widget, morning brief |
| Solo | $9/mo | Unlimited captures, Gmail + Calendar, notifications, all surfaces |
| Pro | $19/mo | Solo + silence as signal, decision memory, pre-meeting brief, discovery |
| Team | $29/mo | Pro + shared intelligence, 5 members |

**Revenue milestones:**
- $4,500 MRR (500 Solo) — proof of life, intelligence layer validated
- $18,700 MRR (2,000 Solo + 50 teams) — hire trigger: 2 contractors
- $50K MRR — Android build starts
- $500K MRR — acquisition conversations

---

## 15. TECH STACK

| Layer | Tool | Notes |
|-------|------|-------|
| iOS | SwiftUI + UIKit | Native only. No web wrappers. |
| OS surfaces | WidgetKit + ActivityKit | Lock screen + Dynamic Island |
| App integration | App Intents | Siri + Shortcuts + widget buttons |
| iOS data | EventKit · HealthKit · CoreLocation · CNContactStore | Native |
| Backend | FastAPI on Railway | Async throughout |
| Database | Neon PostgreSQL | SQLAlchemy async |
| AI routing | OpenRouter | Single service, all models |
| Primary model | Claude Sonnet 4.6 | Dispatch, drafts, digest |
| Research | Perplexity sonar-online | Real-time web, news, discovery |
| Triage | Gemini Flash-Lite | Cheap noise filter |
| Auth | Clerk (tryaxis.app) | Google + Apple sign-in |
| Payments | RevenueCat (iOS) + Stripe (web) | |
| Email delivery | Resend | Onboarding, weekly retrospective |
| Push iOS | APNs | Needs Apple Developer |
| Voice output | ElevenLabs | Morning brief audio |
| Travel time | Google Maps API | School pickup, meeting departure |
| Domain | tryaxis.app | Google Workspace dev@/hendre@ |
| Frontend | Vercel | Auto-deploy on push |
| Backend | Railway | Auto-deploy on push |

---

## 16. CURRENT DEPLOYMENT

| Resource | URL |
|---------|-----|
| Production frontend | https://tryaxis.app |
| Backend | https://web-production-32f5d.up.railway.app |
| Health check | https://web-production-32f5d.up.railway.app/health |
| Privacy policy | https://tryaxis.app/privacy |
| Backend repo | github.com/hendrekir/axis-backend |
| Web repo | github.com/hendrekir/axis-web |
| iOS repo | github.com/hendrekir/axis-ios |
| Local backend | ~/forge/axis-backend |
| Local web | ~/forge/axis-web |
| Local iOS | ~/forge/axis-ios |

**Re-entry commands:**
```bash
cd ~/forge/axis-backend
railway logs --tail 30
curl https://web-production-32f5d.up.railway.app/health
```

---

## 17. RAILWAY ENV VARS

```
ANTHROPIC_API_KEY
OPENROUTER_API_KEY          ← new, replaces separate model keys
CLERK_JWKS_URL              = https://clerk.tryaxis.app/.well-known/jwks.json
CLERK_PUBLISHABLE_KEY
CLERK_SECRET_KEY
DATABASE_URL
ELEVENLABS_API_KEY
FRONTEND_URL                = https://tryaxis.app
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
GOOGLE_REDIRECT_URI         = https://web-production-32f5d.up.railway.app/auth/gmail/callback
GOOGLE_CALENDAR_REDIRECT_URI
GOOGLE_MAPS_API_KEY         ← new, for travel time
OPENWEATHER_API_KEY
PERPLEXITY_API_KEY
RESEND_API_KEY
SPOTIFY_CLIENT_ID
SPOTIFY_CLIENT_SECRET
SPOTIFY_REDIRECT_URI
STRIPE_PRICE_ID
STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET
VAPID_PRIVATE_KEY
VAPID_PUBLIC_KEY
APNS_KEY_ID                 (when Apple Developer activates)
APNS_TEAM_ID
APNS_BUNDLE_ID              = com.dreyco.axis
```

---

## 18. THE 12 RULES

1. The three surfaces are voice, widget, notifications — build everything to serve them
2. Capture works before any OAuth connection is made — day one value, no gates
3. The app is the configuration layer — measure success by how rarely it needs to open
4. Signal deduplication is non-negotiable — noise kills faster than missing a signal
5. Skip-if-empty dispatch always — never waste a Claude call on nothing new
6. Real device testing before any PR — simulator is pretend
7. Battery under 5%/day — measure before every TestFlight build
8. Update CLAUDE.md after every significant session
9. No acquisition talks before $500K MRR
10. Android after $18K MRR — not before
11. Never paste credentials in any chat window
12. Build on and tweak what exists. Never full redesign.

---

## 19. ANTI-PATTERNS — NEVER DO THESE

- OAuth as onboarding gate — value must exist before connections
- Building new features before deduplication is live
- Optimising the in-app UI instead of the OS surfaces
- Generic recommendations — everything must be personalised to this user's memory layer
- Showing urgency numbers in UI — always Now / Today / When you can
- More than 3 notifications per day — restraint is the product
- Any tab labelled "Brain Dump" — it is Capture
- Signal as a tab — it is a sidebar destination
- Apprentice as a tab — it is invisible infrastructure
- Hardcoding timezones to Brisbane — all timing is per-user timezone
- Widget platform before Axis widget works for Axis users
- Talking about AI agents, dispatch loops, or model routing to users — invisible infrastructure

---

## 20. THE PROOF IT'S WORKING

One moment. One test.

User wakes up. AirPods already in. Axis briefs them in 90 seconds while they make coffee — what matters today, what it caught overnight, two things that need a decision. They say "done" twice. Phone goes in pocket.

Three times during the day the lock screen shows something worth knowing. Each time one tap handles it.

They get in the car. Music starts. Travel time to the next thing appears without asking.

School pickup — notification arrives 20 minutes before with exactly how long the drive takes.

Evening. Axis asks one question. They answer in two sentences.

App opened: zero times.

When that happens once — genuinely, not in a test — the product is real.

---

*Copy to ~/forge/axis-backend/CLAUDE.md, ~/forge/axis-web/CLAUDE.md, ~/forge/axis-ios/CLAUDE.md*
*Load at the start of every session. Never start without it.*
*END OF AXIS CLAUDE.md v6.0*
