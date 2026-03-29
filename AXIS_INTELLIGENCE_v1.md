# AXIS — Intelligence Architecture v1
## Every AI model, every data source, signal over noise, optimal routing
### Created: Session 5 · March 2026

---

## THE CORE PRINCIPLE

Axis is not a chatbot. It is an **intelligence orchestration layer**.

Every AI model is a specialist. Every data source is a signal feed. Axis's job is to:
1. Pull from all connected sources
2. Triage with cheap models first
3. Route to the right specialist model with the user's personal context injected
4. Filter 95% as noise before it reaches the user
5. Deliver signal with pre-prepared action

The combination of **user data + right model + right source** produces intelligence no standalone AI can replicate.

---

## THE AI MODEL ROSTER

### Claude (Anthropic) — Primary reasoning engine
**API:** `claude-sonnet-4-6` / `claude-opus-4-6`
**Context:** 1M tokens
**Best at:** Voice matching, nuanced writing, long document analysis, complex reasoning, fewest hallucinations

**Why Claude is the core:**
- Trained on examples of how the user writes → drafts people can't distinguish from the user
- 1M context = entire email archive, full contract, complete project history in one call
- Lowest hallucination rate of any major model
- Best at understanding intent, not just completing prompts

**Axis routes to Claude for:**
- Email drafts (voice-matched to user)
- Morning brief writing
- Thread responses (Axis character)
- Document analysis (contracts, reports)
- Dispatch decisions requiring nuance
- Apprentice improvement (updating user model)
- Meeting prep writing
- Task extraction from brain dumps

**Cost:** ~$3–15/1M tokens depending on model tier

---

### Perplexity — Real-time research engine
**API:** `llama-3.1-sonar-large-128k-online` / `sonar-pro`
**Best at:** Current web search + synthesis, cited sources, person/company research, news synthesis

**Why Perplexity is unique:**
- Real-time web access is core, not bolted on
- Returns cited sources — verifiable, not hallucinated
- Deep research mode synthesises 10+ sources automatically
- Purpose-built for research, not chat

**Axis routes to Perplexity for:**
- Research skills ("research council compliance changes in Brisbane")
- Attendee background before meetings ("who is David Chen from Greenfield")
- Competitor intelligence
- Industry news synthesis
- Technical documentation lookup
- Product/price comparisons with current data
- Any task requiring "what is happening right now"

**Cost:** ~$1 per research request flat

---

### Grok (xAI) — Social and entertainment engine
**API:** `grok-4.1` / `grok-4.1-fast`
**Context:** 2M tokens
**Best at:** Real-time X/Twitter data, social trends, entertainment, breaking news, speed

**Why Grok is unique:**
- Native X/Twitter data — no other model has this
- Cheapest major model ($0.20/1M tokens)
- Social-native intelligence — knows what's trending, who's talking about what
- Witty, personality-forward — fits entertainment context

**Axis routes to Grok for:**
- Entertainment digest (music drops, sports, social trends)
- Breaking news and live events
- X/Twitter sentiment on topics user follows
- Quick factual lookups where speed matters
- Social buzz detection ("is this artist trending right now?")
- Pop culture, sports scores, viral content

**Cost:** $0.20/1M tokens — cheapest for what it does

---

### Gemini Flash-Lite (Google) — Triage and multimodal engine
**API:** `gemini-flash-lite` / `gemini-3.1-flash`
**Context:** 1M tokens
**Best at:** Near-zero cost triage, YouTube video processing, image analysis, multimodal

**Why Gemini Flash-Lite is the triage layer:**
- $0.01/1M tokens — effectively free for bulk classification
- Processes YouTube video content natively (no other model does this)
- Image analysis for photos of receipts, documents, site photos
- Fast enough for real-time pre-filtering

**Axis routes to Gemini Flash-Lite for:**
- Pre-triage of all incoming items (spam/noise/relevant/urgent classification)
- YouTube video summarisation from followed channels
- Receipt/invoice photo processing
- Image analysis from Share Extension
- Any bulk processing where cost matters and quality threshold is "good enough"

**Cost:** $0.01/1M tokens — near-zero

---

### Gemini 3.1 Pro (Google) — Complex reasoning
**API:** `gemini-3.1-pro`
**Best at:** Best reasoning benchmarks (77.1% ARC-AGI-2), mathematical/logical analysis, multimodal

**Why Gemini Pro for specific tasks:**
- Highest ARC-AGI-2 score of any model — genuinely best at complex logic
- 1M+ context
- Use when the task requires structured multi-step reasoning, not nuanced writing

**Axis routes to Gemini Pro for:**
- Complex financial analysis
- Multi-variable scheduling problems
- Legal document logical analysis
- Scientific/technical research synthesis
- Tasks where logical correctness > voice quality

**Cost:** ~$2–12/1M tokens

---

### GPT-5 (OpenAI) — Ecosystem and code execution
**API:** `gpt-5.4`
**Context:** 1M tokens
**Best at:** Code interpreter (runs Python live), image generation, broadest plugin ecosystem

**Why GPT-5 for specific use cases:**
- Code interpreter executes actual Python on the user's data — no other model does this natively
- DALL-E image generation built in
- Best memory system of any consumer AI
- Broadest API ecosystem

**Axis routes to GPT-5 for:**
- Data analysis requiring code execution ("analyse my Stripe data and show trends")
- Image generation skills ("create a site diagram from my description")
- Tasks where the user explicitly wants OpenAI

**Cost:** ~$1.75–14/1M tokens

---

### DeepSeek V4 — Cost-optimised bulk processing
**API:** OpenAI-compatible format
**Cost:** $0.04/1M tokens (40× cheaper than ChatGPT)
**Best at:** Bulk non-sensitive processing, open-weight (self-hostable)

**IMPORTANT CAVEAT:** Chinese servers. Never route personal data (emails, health, finance, location) through DeepSeek. Data sovereignty concern for sensitive information.

**Axis routes to DeepSeek for:**
- Public content classification (categorising news articles by topic)
- Non-sensitive bulk summarisation
- Open content triage where privacy is not a concern
- High-volume low-stakes background tasks

**Cost:** $0.04/1M tokens

---

### Llama 4 (Meta) — Privacy-first on-device processing
**Model:** `llama-4-scout` (17B params, 10M context) / `llama-4-maverick` (400B params)
**Deployment:** Self-hosted or via Together AI / Replicate
**Context:** 10 million tokens — largest of any model
**Best at:** Privacy-sensitive tasks, no external API call, full data control

**Why Llama 4 is strategically important for Axis:**
- NO external API call — health data, personal emails, financial data never leaves the user's infrastructure
- 10M token context = process YEARS of emails in one prompt
- Free after compute (no per-token cost)
- Can be fine-tuned on user data for even more personalisation
- HIPAA-safe for health data processing

**The key insight about Llama 4:**
It has NO context outside the individual — which is not a limitation, it's a feature. When we inject the user's data, it is ONLY the user's data. No training contamination from other people's patterns. This makes it ideal for highly sensitive personal intelligence.

**Axis routes to Llama 4 for (future iOS on-device):**
- HealthKit data analysis (sleep, HRV, activity — never leaves device)
- Full email archive analysis for voice model training
- On-device user model inference
- Privacy-sensitive pattern detection
- Any task where the user's data should never touch an external server

**Deployment:** Initially via Together AI API. Phase 2: on-device via Core ML on iPhone.

---

## THE OPTIMAL INTELLIGENCE STRUCTURE

```
LAYER 0: INPUT COLLECTION (every 15 min + on demand)
├── Gmail (OAuth read)
├── Google Calendar (OAuth)
├── Stripe/Xero (OAuth)
├── Slack (OAuth)
├── Spotify (OAuth)
├── Reddit (API)
├── YouTube (API)
├── X/Twitter (via Grok API)
├── Hacker News (free API)
├── Product Hunt (API)
├── Google News/RSS (API)
├── OpenWeather (API)
├── HealthKit (iOS native)
├── CoreLocation (iOS native)
├── EventKit (iOS native)
├── Brain dump (user input)
├── Siri/voice (App Intents)
└── Share Extension (any app)

LAYER 1: CHEAP TRIAGE (Gemini Flash-Lite — $0.01/1M)
├── Classify each item: spam / noise / relevant / urgent
├── Score relevance 1-10 against user profile
├── Deduplicate across sources
├── Only urgent (7+) and relevant (4-6) pass to Layer 2
└── ~95% items discarded here at near-zero cost

LAYER 2: SPECIALIST PROCESSING (right model for right task)
├── Email drafts → Claude (voice model + relationship context)
├── Research items → Perplexity (real-time web + synthesis)
├── Entertainment/social → Grok (X data + taste profile)
├── YouTube videos → Gemini (video processing native)
├── Images/receipts → Gemini (multimodal)
├── Complex reasoning → Gemini 3.1 Pro (best benchmarks)
├── Health analysis → Llama 4 (privacy-first, no external call)
├── Bulk non-sensitive → DeepSeek (40× cheaper)
└── Code/data execution → GPT-5 (Code Interpreter)

LAYER 3: CONTEXT INJECTION (user data injected into every call)
├── Voice patterns (from sent email history)
├── Relationship graph (contact importance scores)
├── Productive windows (when they get things done)
├── Current mode + location + time
├── Health context (sleep quality, energy level)
├── Today's calendar (upcoming events)
├── Defer patterns (what they consistently avoid)
└── Collective intelligence (cross-user patterns)

LAYER 4: OUTPUT ROUTING (right surface at right time)
├── Urgency 8-10 + actionable → push notification immediately
├── Urgency 6-7 + actionable → push during business hours
├── Urgency 4-6 + informational → morning digest
├── Urgency 1-3 → silent (logged, never shown)
├── Action type "send_email" → execute via Gmail API
├── Action type "create_event" → execute via Calendar API
└── Action type "send_invoice_reminder" → execute via Stripe + Gmail

LAYER 5: FEEDBACK LOOP (apprentice learning)
├── Every user action logged with full context
├── Sunday 3AM: improvement cycle (Claude analyses week)
├── Sunday 4AM: voice model rebuild (sent email analysis via Claude)
├── Sunday 5AM: collective patterns update
└── Updated user model → better decisions next week
```

---

## THE SIGNAL OVER NOISE SYSTEM

### The 5 filters applied to every item:

**Filter 1 — Relevance**
Does this connect to something the user already demonstrably cares about?
- Pass: Artist user has played 10+ times in last 30 days dropped new music
- Fail: "Top 10 albums of the week" from editorial team
- Data used: Spotify history, Reddit engagement, relationship graph

**Filter 2 — Urgency**
Does this require action now, later, or never?
- Pass: Invoice 14 days overdue (action needed today)
- Fail: Interesting industry article (no action required)
- Scoring: 1-10. Below 5 = digest or silent. Below 3 = discarded.

**Filter 3 — Context**
Is this relevant to what's happening in the user's life RIGHT NOW?
- Pass: Rain warning when site visit is 2 days away
- Fail: Rain warning on a day with no outdoor activity
- Data used: Calendar + location + mode + scheduled tasks

**Filter 4 — Deduplication**
Has this story appeared from another source?
- Same event across Reddit + Twitter + news = shown once
- Highest-quality version from most relevant source wins
- Dedup window: 24 hours

**Filter 5 — Apprentice learning**
Has this type of content been dismissed repeatedly?
- 8+ consecutive dismissals from a source/topic → deprioritise automatically
- No explanation to user — system just learns
- Resets if user re-engages with that topic

### The signal vs noise distinction:

**Signal (reaches user):**
- Marcus replied to your quote — high intent, draft ready
- Invoice #47 — 14 days overdue, reminder drafted
- Hozier dropped a live session (user has played him 40 times)
- 10AM meeting location changed (email arrived at 11PM)
- New council compliance requirements (user has site inspection Friday)
- Competitor just raised $10M (user follows that space on X)
- r/construction — viral thread about waterproofing (user is a builder)
- Rain Thursday AM — site visit affected

**Noise (silently discarded):**
- 47 newsletters (Substack, product updates)
- "Top 10 productivity tips" articles
- Spotify generic "Discover Weekly" recommendations
- Reddit front page (not user's communities)
- News about industries they don't work in
- YouTube trending (not from followed channels)
- Weather for cities they're not visiting
- LinkedIn posts from connections they never interact with

---

## DATA SOURCE MAP

### Communication
| Source | Method | What Axis pulls |
|---|---|---|
| Gmail | OAuth read+send | Inbox, sent history, thread context |
| Google Calendar | OAuth read+write | Events, attendees, conflicts |
| Slack | OAuth | Channels, DMs, mentions |
| Outlook/M365 | Graph API | Email + Teams |
| WhatsApp Business | Business API | Business account messages |
| Apple Mail/Calendar | EventKit (iOS) | iCloud events |

### Content + Entertainment
| Source | Method | What Axis pulls |
|---|---|---|
| YouTube | YouTube Data API v3 | Subscriptions, new videos, metadata + Gemini processes video |
| Spotify | OAuth | Listening history, followed artists, new releases |
| Reddit | OAuth API | Subscribed communities, user engagement history |
| X/Twitter | Grok native | Followed accounts, trending in user's interest graph |
| Hacker News | Free API (no auth) | Top stories, Show HN, Ask HN |
| Product Hunt | PH API | New launches in user's relevant categories |

### Knowledge + Research
| Source | Method | What Axis pulls |
|---|---|---|
| Google News | News API + RSS | Topics, companies, industries in user's context |
| Perplexity | sonar-pro | Real-time web synthesis on demand |
| Wikipedia | API | Background facts, context |
| ArXiv | API | Research papers (Student/Founder modes) |

### Finance + Business
| Source | Method | What Axis pulls |
|---|---|---|
| Stripe | OAuth | Invoices, payment status, cash flow |
| Xero | OAuth | Accounting, invoices, financial overview |
| ASX/Yahoo Finance | Finance API | Stocks, market data (user-specified assets) |
| CoinGecko | Free API | Crypto prices (user-specified assets) |

### Health + Context
| Source | Method | What Axis pulls |
|---|---|---|
| HealthKit | iOS native | Sleep, HRV, steps, active energy |
| CoreLocation | iOS native | GPS, geofencing, arrival detection |
| OpenWeather | API | Weather relevant to calendar location |
| Eventbrite | API | Local events in user's interest categories |

---

## COST STRUCTURE

### Per active Pro user per month (~$9 revenue):

| Task | Model | Frequency | Cost/mo |
|---|---|---|---|
| Morning digest | Claude | Daily | ~$0.45 |
| Email triage | Gemini Flash-Lite | 30×/day | ~$0.03 |
| Email drafts | Claude | 5/day avg | ~$1.20 |
| Research requests | Perplexity | 3/day | ~$0.09 |
| Entertainment brief | Grok | Daily | ~$0.02 |
| YouTube summaries | Gemini | 2/day | ~$0.03 |
| Meeting preps | Claude + Perplexity | 2/day | ~$0.30 |
| Dispatch decisions | Claude | 96×/day | ~$0.25 |
| **Total** | | | **~$2.37/mo** |

**Revenue:** $9/mo Pro
**AI cost:** ~$2.37/mo
**Gross margin:** ~74% at launch, improves as Gemini Flash-Lite handles more triage

### Optimisation levers:
- Increase Gemini Flash-Lite triage aggressiveness → fewer expensive model calls
- Cache frequent research results (Perplexity) for 6 hours
- Batch dispatch runs when context is similar → fewer total calls
- Use DeepSeek for public content triage (non-sensitive) → near-zero cost

---

## LLAMA 4 STRATEGIC POSITION

Llama 4 is not just another model. It represents the privacy-first intelligence layer.

**The unique value proposition:**
- 10M token context = process 5+ years of emails in one call
- Self-hostable = user data never leaves Axis infrastructure
- Fine-tunable = can be trained specifically on one user's patterns
- Free after compute = no per-call cost at scale

**Phase 1 (now): Via Together AI or Replicate API**
Use for non-sensitive large-context tasks. Full email archive analysis for voice model training (safer than Claude for bulk PII).

**Phase 2 (iOS app): Via Core ML on-device**
Health data analysis never leaves the device. On-device user model inference. Privacy-preserving pattern detection. This is the privacy story that differentiates Axis from every other AI product.

**Phase 3 (iOS): Axis as the orchestrator of on-device models**
Llama 4 handles sensitive data on-device. Results (without raw data) sent to backend for orchestration. Claude never sees raw health data — only Claude-processed insights from Llama 4's on-device analysis.

```python
# Future: Privacy-preserving pipeline
# Raw health data → Llama 4 on-device → insights (no raw data)
# Insights → Claude → personalised recommendations

# On device:
sleep_insight = llama4_on_device(raw_health_data)
# → "User had 5.2hrs poor quality sleep. Energy likely below 60%."

# Then to backend (no raw health data):
routing = await claude(context + sleep_insight)
# → Routes only admin tasks today, holds deep work
```

---

## SESSION 6 ADDITIONS TO BUILD

Based on this intelligence architecture, Session 6 builds in priority order:

1. **model_router.py** — routes to Claude/Perplexity/Grok/Gemini based on task type
2. **triage_service.py** — Gemini Flash-Lite pre-filter for all incoming items
3. **signal_filter.py** — 5-filter noise reduction system
4. **youtube_service.py** — YouTube Data API + Gemini video processing
5. **reddit_service.py** — Reddit API with community preference learning
6. **news_service.py** — Google News + RSS aggregation with topic filtering
7. **grok_service.py** — Grok API for social/entertainment tasks
8. **gemini_service.py** — Gemini Flash-Lite for triage + video
9. **perplexity_service.py** — Research tasks

These services plug into the orchestrator. Each skill can specify which data sources to pull and which model to use.

---

## THE ROUTING DECISION TREE

```python
def route_to_model(task_type: str, sensitivity: str, cost_priority: str) -> str:
    # Privacy-sensitive → Llama 4 (on-device, future)
    if sensitivity == "health" or sensitivity == "financial_personal":
        return "llama4_local"  # future
    
    # Research / current events → Perplexity
    if task_type in ["research", "news", "person_lookup", "current_events"]:
        return "perplexity"
    
    # Social / entertainment → Grok
    if task_type in ["entertainment", "social_trends", "sports", "music"]:
        return "grok"
    
    # Video content → Gemini
    if task_type in ["youtube_summary", "image_analysis", "video_processing"]:
        return "gemini_flash"
    
    # Complex reasoning (non-writing) → Gemini Pro
    if task_type in ["complex_reasoning", "mathematical", "logical_analysis"]:
        return "gemini_pro"
    
    # Code execution / data analysis → GPT-5
    if task_type in ["code_execution", "data_analysis", "image_generation"]:
        return "gpt5"
    
    # Bulk non-sensitive public content → DeepSeek (cheapest)
    if task_type == "bulk_triage" and sensitivity == "public":
        return "deepseek"
    
    # Default: Claude for everything requiring nuance + voice matching
    return "claude"
```

---

*This document defines the intelligence architecture. Every AI call in Axis flows through this system.*
*Load alongside AXIS_VISION_v1.md and AXIS_BUILD_FRAMEWORK_v1.md at every session start.*
*Update when new models or sources are added.*

**END OF AXIS INTELLIGENCE ARCHITECTURE v1**
