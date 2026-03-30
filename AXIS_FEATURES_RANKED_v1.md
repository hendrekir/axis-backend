# AXIS — Complete Feature Rankings
## Every planned feature, ranked by impact. The full Jarvis vision.
### Updated: Session 7 · March 2026

---

## THE JARVIS PRINCIPLE

What people imagine Jarvis doing:
1. **Proactive status awareness** — knows the state of every project, deal, relationship without being asked
2. **Ambient monitoring** — watches everything and only interrupts when it matters
3. **Instant expert intelligence** — any question answered with depth in seconds
4. **End-to-end execution** — you say it, it handles it completely
5. **Environmental awareness** — knows where you are, what you're doing, what's coming

Every one of these is buildable with Axis's existing architecture. The question is sequencing.

---

## TIER 1 — Transforms what the product is

### 1. Smart notes — "remember this" + readback + cross-reference
**Status:** Build now
**What it does:** Say or type "remember this: the membrane supplier said lead time is now 6 weeks." Axis stores it with timestamp, source context, and tags. Later: "what did I think about the membrane supplier?" pulls the note plus every related email, task, and calendar event.
**Why it's number 1:** Used 5-10 times a day regardless of what else is happening. The stickiest feature in the product. Unlike Apple Notes it connects to everything — notes become inputs to dispatch, morning brief, meeting prep.
**Build:**
- New table: `notes` (id, user_id, content, tags[], source, context_links[], created_at)
- Thread commands: "remember [anything]" → saves + confirms
- Thread commands: "what do I know about [topic]" → semantic search + readback
- GET /notes · POST /notes · GET /notes/search?q= · GET /notes/related?topic=
- Morning brief: surfaces notes relevant to today's calendar or emails
**Jarvis parallel:** "JARVIS, note that the reactor stabiliser needs recalibrating." Stores it, cross-references with schematics, flags in next relevant briefing.

---

### 2. Status updates on anything — projects, deals, people, tasks
**Status:** Build now
**What it does:** "What's the status of the Greenfield deal?" Axis pulls from emails, calendar, invoices, tasks, notes — everything it knows — and gives a complete current picture. "Last email was 4 days ago. Invoice outstanding $4,200. Next meeting Tuesday. Marcus mentioned cash flow concerns." No app switching. One question, complete answer.
**Why it ranks here:** The most natural thing you'd say to a real assistant. Axis already has all the data — it just needs to synthesise it on demand. One thread command, one prompt.
**Build:**
- Thread command: "what's the status of [anything]"
- Claude synthesises from: emails mentioning the topic, calendar events, tasks tagged with it, invoices, notes
- Returns structured briefing: last contact, open items, risks, next step
- "Watch [topic]" sets a persistent monitor that alerts on changes
**Jarvis parallel:** "JARVIS, status on Stark Tower?" → "73% complete, 3 days ahead. One invoice outstanding. Arc reactor install pending."

---

### 3. Expert intelligence with personal relevance
**Status:** Build now
**What it does:** "What's happening with the Iran situation?" → Axis gives expert-verified facts from Reuters/AP/named academics only, then checks user's context: "Your steel supplier ships through the Gulf. Your Greenfield quote locks in pricing for 30 more days. This may matter." The connection between world events and your specific life.
**Source filter (critical design decision):**
- Tier 1 (always): Reuters, AP, BBC, ABC, financial regulators, government sources, peer-reviewed institutions
- Tier 2 (domain expertise): Named academics with institutional affiliation, industry bodies, central banks
- Tier 3 (context only): Major newspapers — flagged as opinion vs fact
- Excluded: social media, unverified blogs, partisan commentary, anonymous sources
**Build:**
- Perplexity sonar-pro with source whitelist in system prompt
- Second Claude call: "Does this briefing connect to anything in the user's context?"
- Source credibility scoring in prompts/research.py
- User can configure trusted source list in Settings
**Jarvis parallel:** Gives military briefing then adds "Colonel Rhodes is currently in that region — his convoy route passes through the contested area."

---

### 4. Context notes — what Axis always needs to know
**Status:** Build now (2 hours)
**What it does:** A persistent field: "Greenfield is my most important client. Trying to close $200K with Marcus. On leave Dec 20." Injected into every single Claude call forever. Immediately makes every interaction smarter. No training period required.
**Why it ranks here:** Highest leverage per hour of build time. Makes every interaction smarter immediately. The simplest possible personalisation with the highest possible impact.
**Build:**
- `users.context_notes TEXT` column
- PATCH /me accepts context_notes
- Context assembler injects above user model in every Claude call
- Settings screen: "What Axis should always know" text area, no character limit

---

### 5. Proactive skill suggestions — Axis proposes its own automations
**Status:** Session 7
**What it does:** Axis detects patterns and proposes: "I notice you've manually chased 4 invoices this month. Want me to automate that?" or "You've asked about construction news 3 times. Want a daily briefing?" Gets smarter by proposing — every accepted suggestion improves the product, every rejection trains it.
**Build:**
- In dispatch + apprentice cycle: detect repeated manual actions or search patterns
- Threshold: 3+ similar actions → generate skill_suggestion
- Surface in thread: "I noticed X. Want me to automate it? [Create skill] [Not now]"
- [Create skill] → auto-generates skill config + system_prompt + saves to skills table
- [Not now] → logs dismissal, suppresses same suggestion for 14 days
**Jarvis parallel:** "I've noticed you review the same power reports every Tuesday. Shall I automate and alert you only when consumption exceeds 15% variance?"

---

### 6. Planning + brainstorming partner
**Status:** Session 7
**What it does:** "Help me plan the Greenfield Level 2 install" or "I want to start a furniture business online." Axis asks the right questions, uses Perplexity for real market data, Claude for structure, then saves as a living skill that monitors relevant news and updates the plan.
**Build:**
- New skill types: brainstorm · plan · research_project
- Thread commands: "brainstorm [idea]" → multi-turn structured conversation
- Thread commands: "plan [project]" → phases, tasks, risks, calendar blocks
- End of session: "Save this as a plan?" → creates skill + note + tasks automatically
- Plan skill: monitors relevant Perplexity news weekly, updates when something material changes
**Jarvis parallel:** "Help me design a new propulsion system." → asks questions → pulls research → generates phased build plan → monitors patent filings → flags competitor announcements.

---

## TIER 2 — Meaningfully better product

### 7. Ambient monitoring — "watch this for me"
**Status:** Session 7
**What it does:** "Watch the Greenfield contract." "Monitor news about building code changes." "Let me know if Marcus emails." User sets a watch on any topic, person, or situation. Axis runs silently and only surfaces when something material happens.
**Build:**
- New watches table: (id, user_id, watch_type, subject, threshold, last_checked, is_active)
- Watch types: person (email), topic (Perplexity), contract (email + date), news (RSS + Perplexity)
- Dispatch checks active watches every 15 min
- Surface only when match found above threshold
- "Stop watching [X]" cancels the watch
**Jarvis parallel:** "Monitor all communications from Senator Stern." → alerts only when something matters.

---

### 8. Risk and opportunity detection — proactive flags
**Status:** Session 7
**What it does:** Axis scans the situation and flags before you think to ask. "Your Greenfield quote expires in 3 days and Marcus hasn't responded." "Your biggest client hasn't emailed in 18 days." "Two meetings overlap Tuesday." Genuinely watching.
**Build:**
- Risk detector runs in dispatch: check quote expiry dates, communication gaps, calendar conflicts
- Opportunity detector: unanswered emails from new contacts, invoice payment opportunities
- Threshold-based alerts: configurable per user (days, amounts, frequency)
**Jarvis parallel:** "Sir, the palladium core is becoming unstable. At current consumption rates, you have 72 hours before critical failure."

---

### 9. Multi-turn task execution — say it, Axis handles it
**Status:** Session 7
**What it does:** "Set up a meeting with Marcus next week." → Axis reads availability → "Marcus is free Tuesday 2PM or Thursday 10AM" → "Tuesday" → sends invite + email to Marcus in user's voice. End to end.
**Build:**
- Thread system prompt updated to detect multi-step intent
- State machine: intent → gather info → confirm → execute
- Execution calls: gmail_send, calendar_service.create_event, tasks endpoint
- Confirmation step mandatory before any send/create action

---

### 10. [Send] button on email drafts
**Status:** Build now (1 hour)
**What it does:** Dispatch generates drafts. Thread shows them as text. No button. One hour to close the most important action loop.
**Build:** Frontend only. POST /gmail/send exists. Add button to thread messages with message_type="email_draft".

---

### 11. PWA — Axis on home screen before iOS ships
**Status:** Session 7
**What it does:** Add to Home Screen on iPhone today. Full screen, push notifications, no browser chrome. Bridges the 3-month gap until the native app.
**Build:**
- manifest.json + app icons (all sizes)
- Service worker for offline caching
- apple-mobile-web-app-capable meta tags
- Add to Home Screen prompt after 3rd session
- Push notification permission on PWA install

---

### 12. Follow-up tracker — sent emails with no reply
**Status:** Session 7
**What it does:** Tracks sent emails with no reply after 3 days. "Your quote to Greenfield has been unread 5 days. Follow up?" Draft ready, one tap sends.
**Build:**
- sent_emails_cache already exists
- New job: scan sent emails older than 3 days with no reply thread
- Surface as dispatch item with urgency 6-7
- Draft follow-up using voice model

---

### 13. Voice input on web — mic button in Thread
**Status:** Build now (2 hours)
**What it does:** Web Speech API in Chrome. Hold mic, speak, release to send. No backend changes. First taste of voice-first before iOS.
**Build:** BrainDump.jsx + Thread.jsx: mic button → SpeechRecognition → fills textarea → user sends

---

### 14. Daily situation briefing — full picture on demand
**Status:** Session 7
**What it does:** "What's my situation today?" → Complete synthesis: active deals and status, outstanding invoices, people who need response, risks on radar, what's coming, one thing to focus on. Not a task list. A situational awareness briefing.
**Jarvis parallel:** "Good morning. 3 priority items. Arc reactor efficiency down 4%. Rhodes called twice. Board meeting in 90 minutes."

---

### 15. Relationship health — people going cold
**Status:** Session 7
**What it does:** "You haven't spoken to Marcus in 23 days. Last interaction was a quote with no reply." Tracks communication frequency with important contacts. Prevents relationships going cold without realising.
**Build:**
- Weekly scan of relationship_graph table
- Flag contacts with importance_score > 7 and last_interaction > 14 days
- Surface in weekly brief and dispatch

---

### 16. Weather + travel time in morning brief
**Status:** Build now (2 hours)
**What it does:** "Site visit at 8AM. 14 degrees and raining. Leave by 7:20 based on current traffic." OpenWeather + Google Maps distance matrix + Calendar event location. Free APIs.
**Build:**
- OpenWeather API key (free tier)
- Google Maps Distance Matrix API
- In morning_digest.py: for each calendar event with location, calculate travel time + weather

---

### 17. Weekly retrospective email
**Status:** Session 7
**What it does:** Sunday 6PM Axis emails your week summary. Tasks completed, emails handled, patterns noticed, one suggestion. Users share these. Organic word-of-mouth. Resend already integrated.
**Build:**
- Sunday 6PM cron in APScheduler
- Pulls week stats from interactions table
- Claude generates narrative summary (not a list)
- Resend sends to user.email

---

### 18. Zapier / webhook skill output
**Status:** Session 7
**What it does:** Any skill can fire a webhook as output. Zapier receives it. 5,000+ integrations instantly connected. Turns Axis into the brain of someone's entire workflow stack.
**Build:**
- output_routing option: "webhook"
- skill.trigger_config stores webhook_url
- After skill execution: POST to webhook_url with result payload

---

### 19. Stripe invoice chasing — Axis makes you money directly
**Status:** Session 7
**What it does:** User's own Stripe connected. Overdue detected. Draft in user's voice. [Send] one tap. First time Axis directly generates revenue for the user.
**Build:** Already started. Stripe Connect OAuth. services/stripe_service.py. Wire into dispatch + morning digest.

---

### 20. Quick reply chips on email drafts
**Status:** Session 7
**What it does:** 3 chips under each email: "Yes", "I'll call you", "Need more time." Tap → full draft pre-filled → one more tap sends. Removes the thinking entirely.

---

## TIER 3 — Jarvis environmental intelligence (iOS era)

### 21. Smart home + environment control
**Status:** Phase 3 (after iOS ships)
**What it does:** HomeKit integration. "Turn off the lights and lock up, I'm leaving." GPS-aware: heading home → pre-warms the house. At site → opens relevant calendar events.
**Jarvis parallel:** The suit powering up, the workshop responding to presence.

---

### 22. Predictive scheduling — AI time-blocks your calendar
**Status:** iOS / Phase 2
**What it does:** "You have 12 tasks and 7 meetings this week. Based on your energy patterns, here's a suggested schedule." Calendar blocks created automatically. The week plans itself.

---

### 23. Dynamic Island — live agent status
**Status:** iOS Phase 2
**What it does:** Axis pulsing in Dynamic Island while dispatch runs. "Reading inbox... 3 emails ranked... Invoice flagged." The ambient presence of intelligence always working in the background.
**Jarvis parallel:** The HUD always present, always aware, not intrusive.

---

### 24. Hugging Face specialist model import
**Status:** Phase 3 (after Llama 4 on-device infrastructure)
**What it does:** Import specialist fine-tuned models — legal contract analysis, medical summarisation, construction compliance. Runs on-device via Core ML. Privacy-preserving. Built on same Llama 4 infrastructure.
**Why phase 3:** Same Core ML work as Llama 4 on-device. Do together after iOS ships.

---

## TIER 4 — The full Jarvis (future)

### 25. Axis makes phone calls on your behalf
**Status:** Future
**What it does:** ElevenLabs voice + Twilio outbound calling. "Call the restaurant and book a table for 2 at 7PM Friday." Axis calls, makes the reservation, confirms back to you.
**Technology available today:** ElevenLabs API + Twilio. Not a research problem — an execution sequencing decision.
**Jarvis parallel:** "JARVIS, call Pepper and tell her I'll be 20 minutes late." This is the movie moment.

---

### 26. Axis as a real-time conversation partner
**Status:** Future
**What it does:** Real-time voice conversation (not push-to-talk). Like calling someone who knows everything about your life. Whisper while in a meeting: "Who is this person?" Axis whispers back: "David Chen, CFO Greenfield, ex-Deloitte, watch the payment terms."

---

### 27. Axis watches and learns from everything on screen
**Status:** Future (requires Apple entitlements or jailbreak equivalents)
**What it does:** Screen awareness — Axis sees what you're looking at and offers contextual intelligence. Reading an email → suggests reply. Looking at a contract → flags risks. On a LinkedIn profile → pulls background. The full OS intelligence layer.

---

## BUILD PRIORITY FOR CURRENT SESSIONS

### Session 7 (now):
1. Smart notes + readback
2. Status command ("what's the status of X")
3. Context notes field
4. [Send] button on email drafts
5. Proactive skill suggestions
6. Voice input on web (mic button)
7. PWA manifest
8. Weather + travel time in morning brief
9. Planning + brainstorming commands
10. Expert intelligence with source filter

### Session 8 (next):
- Ambient monitoring ("watch this")
- Risk + opportunity detection
- Multi-turn task execution
- Follow-up tracker
- Relationship health monitoring
- Weekly retrospective email
- Zapier webhook output
- Stripe invoice chasing

### iOS (Sessions 9-12):
- All native iOS features from checklist
- Dynamic Island
- HealthKit energy routing
- Control Centre tile

### Phase 3 (funded by revenue, contractors):
- Hugging Face on-device models
- HomeKit / smart environment
- Predictive calendar scheduling
- Phone call agent (ElevenLabs + Twilio)

---

*This document is the complete feature roadmap.*
*Every feature maps to the Jarvis vision.*
*Build top to bottom. Don't skip tiers.*

**END OF AXIS FEATURES RANKED v1**
