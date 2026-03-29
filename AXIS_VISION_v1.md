# AXIS — Full Product Vision
## The product we are building. Not the product we can build. The product we must build.
### Captured: Session 5 · March 2026

---

## THE CORE IDEA

Axis is not a productivity app. Axis is not a chatbot. Axis is not a to-do list.

**Axis is an orchestration layer between the user and their digital life.**

It reads everything, thinks about it, and acts on it — so the user doesn't have to. The phone becomes less of a tool you operate and more of a system that operates for you.

The closest mental model is Jarvis from Iron Man — not the movie character, but what people imagine when they hear that name. An intelligence that:
- Knows where you need to be and when
- Knows what needs handling before you ask
- Acts on your behalf and reports back
- Learns how you think and replicates it
- Connects every system you use into one coherent picture
- Is accessible instantly from anywhere — voice, tap, glance

---

## WHAT AXIS IS

### Three simultaneous roles:

**1. The Remote**
Direct control over your digital life. Sends emails. Creates calendar events. Chases invoices. Books things. Posts. Searches. Navigates. You don't switch between apps — you tell Axis and it executes.

**2. The Assistant**
Anticipates before you ask. Reads overnight email, knows your day, surfaces what matters, handles what doesn't need you. Proactive, not reactive. The person who handled it while you were sleeping.

**3. The Apprentice**
Watches how you work. Learns your voice, your patterns, your preferences, your relationships. Gets smarter every week. Becomes more you over time. The longer you use it, the less you have to tell it.

All three simultaneously. Not modes. Not features. The baseline.

---

## THE PHONE IS NOT A TOOL. IT'S A SURFACE.

The iPhone is already used for:
- Communication (messages, email, calls, WhatsApp, social)
- Productivity (tasks, calendar, notes, files)
- Entertainment (music, video, news, Reddit, sports)
- Knowledge (search, AI, research, learning)
- Navigation (Maps, transit, traffic)
- Finance (banking, invoices, spending)
- Health (sleep, activity, wellbeing)

Every single one of these is a data source for Axis AND an output surface.

Axis doesn't compete with any of these. It connects them. It becomes the intelligence layer that makes all of them work together without the user having to think about it.

---

## THE UX IS AMBIENT, NOT ACTIVE

The app is not the product. The phone is the product.

**Primary surfaces (in order of frequency):**
1. Lock screen — signal widget, one-tap actions
2. Notification — context-aware, action buttons attached
3. Control Centre — swipe down, tap Axis icon, speak or read
4. Dynamic Island — live agent status
5. Siri — "Hey Siri, tell Axis to..."
6. The app — for depth, configuration, history

**The user should be able to:**
- Glance at lock screen and know their signal for the day
- Swipe down and tap Axis like Shazam — instant access
- Speak to it hands-free from anywhere
- Act on suggestions with one tap without opening the app
- Never feel like they're managing the system

---

## SKILLS — THE CUSTOMIZATION LAYER

Skills are not hardcoded features. Skills are user-defined workflows.

**Structure of a Skill:**
- Name: what the user calls it
- Trigger: what activates it (schedule, event, location, manual)
- Data sources: which APIs it reads (Gmail, Spotify, Calendar, Reddit, etc.)
- Reasoning model: which AI processes it (Claude for nuance, Perplexity for research, Grok for speed)
- Output: where the result goes (notification, thread, widget, action, silent)
- Feedback loop: what user actions teach it

**Built-in skills (starting point):**
- Email Intelligence (Gmail read + rank + draft)
- Calendar Intelligence (prep + conflict + travel)
- Finance Intelligence (Stripe + Xero + invoices)
- Site Intelligence (Builder mode — suppliers, inspections, crew)
- Research Intelligence (Perplexity + summarise + surface)
- Entertainment Intelligence (Spotify + Reddit + news + events)
- Health Intelligence (sleep routing + energy windows)
- Knowledge Intelligence (research on demand)

**User-built skills (the real product):**
Users can build any skill by describing it in plain language. "When I get an email from a client, draft a reply and show me before sending." "Every morning tell me what new music dropped from artists I follow." "If I'm near a hardware store, remind me about the supplies list."

The skills framework is the moat. It makes every user's Axis different from every other user's Axis.

---

## MULTI-MODEL INTELLIGENCE

Not every task needs the same brain. Axis routes to the right model.

| Task | Model | Why |
|---|---|---|
| Draft email in user's voice | Claude | Nuance, context, tone |
| Research a topic | Perplexity | Real-time web knowledge |
| Quick factual answer | Grok | Speed, recency |
| Code generation | Claude | Depth |
| News summary | Perplexity | Current events |
| Creative writing | Claude | Imagination |
| Market data | Perplexity + Grok | Speed + accuracy |

The user doesn't choose. Axis routes automatically based on the task. But advanced users can configure which model handles which skill type.

---

## THE APPRENTICE LAYER

The apprentice model is what makes Axis irreplaceable over time.

**What it learns:**
- Voice patterns (sentence length, formality, sign-offs per contact type)
- Relationship graph (who matters, how fast you reply, who you ignore)
- Productive windows (when you actually get things done)
- Attention patterns (what notifications you act on, what you dismiss)
- Preference signals (what content you engage with, what you skip)
- Decision patterns (what categories of decisions you make the same way every time)

**How it learns:**
- Every send/dismiss/edit/defer is a training signal
- Weekly improvement job processes the week's interactions
- Voice model builder reads sent emails and messages
- Collective patterns across all users improve cold-start

**Making it visible:**
Users should see what Axis learned. Not as a settings page — as a living profile. "Axis knows you respond to suppliers within 2 hours. Axis knows you defer health tasks to Friday. Axis knows you like electronic music on Monday mornings." Transparency builds trust. Trust builds retention.

---

## THE APIs — LEAN ON WHAT EXISTS

Don't build what already exists. Connect it.

**Communication:**
- Gmail (read + send) — OAuth
- Google Calendar — OAuth
- Outlook / Microsoft 365 — Graph API
- Slack — OAuth
- WhatsApp Business — Business API

**Entertainment + Knowledge:**
- Spotify — OAuth (music, podcasts, recommendations)
- Reddit — API (communities, trending, notifications)
- Twitter/X — API (follows, trending, DMs)
- YouTube — API (subscriptions, trending)
- Perplexity — API (real-time research)
- News APIs — multiple sources

**Productivity + Finance:**
- Stripe — OAuth (invoices, payments, cash flow)
- Xero — OAuth (accounting, invoices)
- Google Maps — API (navigation, travel time, location-based triggers)
- Apple Maps — native iOS

**Health + Context:**
- Apple Health — HealthKit (sleep, HRV, activity)
- CoreLocation — GPS (geofencing, arrival detection)
- Apple Calendar — EventKit

**AI Models:**
- Anthropic Claude — primary reasoning
- Perplexity — research + real-time web
- Grok — speed + recency
- On-device ML — privacy-sensitive tasks

---

## WHAT WE ARE NOT BUILDING

- A to-do list app
- Another AI chatbot
- A notification manager
- A productivity dashboard
- A Notion competitor
- A replacement for individual apps

We are building the layer that sits above all of them.

---

## THE PRODUCT AT FULL VISION

A person wakes up. Their lock screen shows: one thing they need to do, one thing they should know, one thing that will make their day better.

They swipe down. Axis is there. They speak: "What's my day?" Axis tells them — 2 meetings, 3 emails that need them, an invoice that's overdue, and Hozier dropped a new single at midnight.

They tap "Reply to Marcus." The draft is there, sounds exactly like them. They tap Send.

They get in the car. Axis says "You have a meeting in 40 minutes at 123 Eagle St. Leave in 8 minutes based on current traffic."

At the site, gloves on: "Hey Siri, tell Axis the membrane on Level 2 is failing, add to urgent tasks." Done without touching the phone.

At 5PM a notification: "Invoice #47 — $4,200 — Greenfield. 14 days overdue. Send reminder?" One tap. Sent.

Evening: "Sounds like you had a productive day. Spotify queued your wind-down playlist. Tomorrow's first task is ready on your lock screen."

**That is the product. Build toward that.**

---

## THE FINANCIAL PATH

- $9/mo Pro (unlimited skills, all data sources, apprentice learning)
- $14/user/mo Team (shared skills, signal sharing, manager view)
- Skills marketplace (users share custom skills, Axis takes a cut)

Revenue milestones:
- $4.5K MRR — proof of life
- $18.7K MRR — hire 2 Swift contractors
- $50K MRR — OS moat features (Dynamic Island, Watch, Android demo)
- $500K MRR — Apple acquisition conversation

---

## THE ACQUISITION STORY

Apple acquires Axis because it demonstrates exactly what iOS could be with native OS access. Every workaround we built — Gmail OAuth instead of native mail access, Siri App Intents instead of system-level voice, HealthKit permission instead of always-on health — becomes native overnight.

The Android app (built after $18K MRR) is the demonstration of what's possible with full OS access. That's the acquisition pitch. "Here's your platform running at 9.5/10. Give us the native APIs and it runs at 10/10."

---

*This document is the north star. Every build decision gets evaluated against it.*
*If a feature doesn't serve this vision, it doesn't get built.*
*If a feature serves this vision, it gets prioritised.*

**END OF AXIS VISION v1**
