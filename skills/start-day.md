# Skill: Start the Day

> **What it does:** One phrase — your AI ingests all your email, priority Telegram channels, and calendar; scores every signal; and delivers 4 structured packets (Deals, Day Plan, News, Follow-ups) directly to your Telegram in under 5 minutes.

---

## How to Install

1. Save this file as `.cursor/skills/start-day/SKILL.md` (or `~/.claude/commands/start-day.md`)
2. Configure your sources in the `CONFIG` section below
3. Connect your email and Telegram MCPs (see Requirements)

**Trigger phrases:**
- `"Start the day"`
- `"Morning briefing"`
- `"Старт дня"` *(or any phrase you set)*

---

## Requirements

**MCPs needed (connect at least one email + Telegram):**
- Email: `gmail` MCP, `ms365` MCP, or equivalent
- Telegram: `telegram-mcp` (reads channels, sends to Saved Messages)
- Calendar: `Google Calendar` MCP (optional, for Day Plan)

---

## CONFIG — Personalise Before Use

```yaml
# ── YOUR IDENTITY ──────────────────────────────────
user_name: "<YOUR NAME>"
role: "<YOUR ROLE / WHAT YOU'RE BUILDING>"
language_output: "<en | ru | mixed>"   # language for packet output

# ── EMAIL ACCOUNTS (add as many as you have MCPs for) ──
email_accounts:
  - id: work
    label: "<Work email>"
    mcp: gmail          # or ms365
    query: "newer_than:1d"
    max_results: 30
  - id: personal
    label: "<Personal email>"
    mcp: gmail_personal
    query: "newer_than:1d"
    max_results: 20

# ── TELEGRAM PRIORITY CHANNELS ──────────────────────
# Find channel IDs via @userinfobot or telegram-mcp list_chats
telegram_channels:
  - id: <CHANNEL_ID_1>
    name: "<Channel name>"
    focus: "<what to look for — e.g. 'AI tools, automation'>"
  - id: <CHANNEL_ID_2>
    name: "<Channel name>"
    focus: "<e.g. 'startup news, funding'>"
  # add more...

# ── SCORING WEIGHTS ─────────────────────────────────
# Adjust to your priorities (must sum to 1.0)
scoring_weights:
  importance: 0.30      # Does it relate to your main goal?
  urgency: 0.25         # Deadline words, calendar events
  deal_impact: 0.20     # Contract, invoice, agreement signals
  personal_relevance: 0.15  # Hits on your must-include topics
  source_trust: 0.10    # How much you trust this source

# ── PACKET THRESHOLDS ───────────────────────────────
packets:
  deals:    { threshold: 60, cap: 5 }   # High-stakes opportunities
  day_plan: { threshold: 50, cap: 3 }   # Top priorities + calendar
  news:     { threshold: 80, cap: 5 }   # High-signal content only
  followups:{ threshold: 65, cap: 8 }   # Pending replies

# ── KEYWORDS (tune to your context) ─────────────────
deal_keywords: ["contract", "pilot", "invoice", "proposal", "retainer", "funding", "offer"]
urgency_keywords: ["today", "urgent", "deadline", "asap", "срочно", "сегодня"]
must_include_topics: ["<TOPIC_1>", "<TOPIC_2>"]   # Always surface these
always_exclude_topics: ["<TOPIC_X>"]              # Never surface these
```

---

## Execution Protocol

### Step 0 — Load Config
Read your config + any memory files you've set up. Apply context before scanning.

### Step 1 — Email Ingestion (parallel across all accounts)
For each account, fetch last 18 hours of inbox. Extract: subject, sender, timestamp, preview (250 chars).

Normalise each message to:
```json
{
  "id": "<source>:<hash>",
  "source_type": "email",
  "source_id": "<account_id>",
  "title": "<subject>",
  "body": "<preview>",
  "timestamp": "<ISO>",
  "sender": "<email>"
}
```

### Step 2 — Telegram Ingestion
For each priority channel, fetch last 18 hours:
```
get_messages(chat_id=<ID>, page=1, page_size=10)
```
Normalise to same signal format.

### Step 3 — Score All Signals

```
score = (importance × W1) + (urgency × W2) + (deal_impact × W3)
      + (personal_relevance × W4) + (source_trust × W5)
      × recency_factor × topic_multiplier × repetition_penalty
```

**Scoring guidance:**
- **importance:** Relates to your primary goal? Keywords match? → 35–70 pts
- **urgency:** Deadline words → +20. Calendar event → 90
- **deal_impact:** Deal keywords present → up to 100
- **personal_relevance:** Must-include topics → 15 pts each, max 70
- **source_trust:** Known sender/source → higher weight
- **recency:** Last 6h → ×1.15 | 6–12h → ×1.0 | 12–24h → ×0.85

Hard rules:
- Always-exclude match → score = 0, drop
- Must-include match → score = max(score, 80)

### Step 4 — Assign to Packets
Sort signals into buckets based on score + keyword matching. Apply caps.

### Step 5 — Build 4 Packets

**Packet 1 — Deals & Opportunities**
```
📋 *Deals & Opportunities* — {DD Mon}
────────────────────────────────
*1. {title}*
   `{source}` · {HH:MM} · {score bar}
   {2-sentence summary}
   ⚡ *Why now:* {why this matters today}
   ▶ *Action:* {one concrete next step}
```

**Packet 2 — Day Plan**
```
📅 *Day Plan — {Weekday, DD Mon YYYY}*
────────────────────────────────
*FOCUS:* {primary project} · {primary metric}

*TOP 3 PRIORITIES TODAY:*
1. 💰 *{title}*
   ↳ {next action}
2. ⚙️ *{title}*
   ↳ {next action}
3. 🤝 *{title}*
   ↳ {next action}
💰 MONEY · ⚙️ LEVERAGE · 🤝 NETWORK

*SCHEDULE:* (calendar if connected)
  🕐 {HH:MM} — {event}

*STOP LIST — do not do today:*
  · Tasks scoring none of MONEY / LEVERAGE / NETWORK
```

**Packet 3 — High-Signal News**
```
📡 *High-Signal News* — top {N}
────────────────────────────────
Only signals scoring ≥ 80/100

*1. {title}*
   `{channel}` · {HH:MM} · {score}
   {summary}
   ⚡ *Why today:* {relevance}
   ▶ {action}
```

**Packet 4 — Follow-ups**
```
📨 *Follow-ups & Pending* — {N} threads
────────────────────────────────
*1. {title}*
   `{source}` · {sender} · {HH:MM}
   {summary}
   ▶ *Draft reply:* {suggested action}
```

### Step 6 — Deliver to Telegram Saved Messages
```
send_message(chat_id="me", text="<packet>", parse_mode="markdown")
```
Order: Deals → Day Plan → News → Follow-ups. 1–2 sec between sends.

If a packet has 0 items → send quiet version: `"📋 Deals — no new signals in last 18h"`

### Step 7 — Log the Run
Append to a run log:
```json
{"timestamp":"<ISO>","deals":N,"news":N,"followups":N}
```

---

## Feedback Commands

After the brief is sent, you can tune the system by replying:

| Command | Effect |
|---|---|
| `+relevant <topic>` | Note positive signal, suggest adding to must-include |
| `-relevant <topic>` | Add to less-like-this tracking |
| `more-like-this <topic>` | Boost topic multiplier |
| `less-like-this <topic>` | Lower topic multiplier |
| `mute-source <id>` | Add to low-SNR sources list |

---

## Error Handling

- Email MCP fails → skip that account, note in output, continue
- Telegram channel unavailable → skip, log, continue
- 0 total signals → send "Quiet morning" message
- Always send at least the Day Plan (calendar events don't require MCPs)

---

## Why This Works

Most people start their day by manually checking 5+ apps, losing 20–40 minutes to context-switching before doing any real work. This skill collapses that into one 5-minute automated delivery — scored, prioritised, and ready to act on.

**The insight:** It's not a summary tool. It's a decision tool. Every packet ends with one concrete action, not just information.

**Adapt it:** The scoring formula is the core IP. Tune the weights to match your actual priorities — if revenue matters most, raise `deal_impact`. If learning matters, add a `knowledge_gain` weight.

---

## Setup Checklist

- [ ] MCPs installed: gmail / ms365 / telegram-mcp
- [ ] Telegram channel IDs collected (use `list_chats` in telegram-mcp)
- [ ] CONFIG section filled in above
- [ ] Trigger phrase added to `CLAUDE.md` or Cursor rules
- [ ] Test run: `"Start the day"` → check Telegram Saved Messages
