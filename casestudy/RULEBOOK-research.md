# Rulebook research (Fable 5.1, 2026-09-17)

Verified by hand: `last_interaction` 2025-12-08T15:04:00Z is 09:04 Monday in America/Chicago, and
2025-12-09 is a Tuesday — so "next 09:00 local strictly after the reference time" explains the
expected `send_at`, and Thu/Fri are the first two weekdays at least two days out in the same week.

Full research below; it is the source for the build tasks C1-C4.
(agent output appended by hand in the next step)

# Deterministic Rule Layer — Design Document

## 1. Forensic read of the single example

| Observation | Inferred rule |
|---|---|
| `channel: "sms"` | First entry in `channel_preferences` whose `consent.*_opt_in` is true. Both sms and email are consented; sms is listed first. Preference order wins, not a global default. |
| `send_at: 2025-12-09T09:00:00-06:00` | `last_interaction` = 15:04Z = **09:04 CST**. Rule: **next 09:00 local strictly after the reference time**. 09:04 already passed 09:00, so it rolls to tomorrow. Do not model this as "always next day": if a hold-out has last_interaction at 07:30 local, the answer is same-day 09:00. Offset is rendered in the recipient's zone (`-06:00`, CST in December), never `Z`. |
| 09:00 not 08:00 | Texas quiet-hour floor is 09:00 (see §2), and 09:00 is also the industry "first touch" batch time. We use 09:00 everywhere, not just Texas. |
| Dec 9 is a **Tuesday**; options `Thu`,`Fri` | Options = the next two weekdays **at least 2 calendar days after send date**, capped to the same Mon–Fri week ("this week"). Wed is excluded because it's <2 days out. If fewer than two qualifying days remain in the week, use Mon/Tue of next week and say "next week". |
| Exactly two options | Cadence style is binary-choice SMS: two options keep the reply classifier trivial (`1`/`2`) and the body under two segments. Never offer three. |
| "Reply 1 for Thu, 2 for Fri" | Numbered-reply CTA convention. Every SMS CTA with options is rendered as `Reply N for X`. This is what makes `reply_classification_f1` achievable deterministically. |
| "Hi Taylor—" | First name only, em dash, no last name. Last name would be a PII leak and adds nothing. |
| "Oak Ridge" not "Oak Ridge Apartments" | Brand short-name rule: strip trailing `Apartments|Apts|Residences|Community|Homes|Lofts|Flats` for the greeting line. |
| No property address, no city_interest, no move date echoed | SMS carries zero location/PII beyond the brand name. `city_interest` is never echoed (steering risk + PII). Move date is used only to pick the cadence horizon. |
| `subject: null` | Subject is an email-only field. SMS always `null` (key present, value null; never omit the key). |
| Body = 166 chars, contains an em dash (forces UCS-2, so it's already 3 segments) | Length ceiling is not 160. Set: target ≤ 200, hard max 320. |
| "Reply STOP to opt out." is the **last sentence** | Opt-out instruction is a mandatory trailing sentence on every SMS. |
| Single exclamation, no emoji, sentence case, one question | Brand style. |
| `cta.type: "schedule_tour"` while constraint says `"book_tour"` | Constraint vocabulary and output vocabulary differ. Maintain an explicit map (`book_tour → schedule_tour`). |
| `next_action.name: prospect_welcome_short_horizon` | Name = `{persona}_{intent}_{horizon}_horizon`. Move date is 32 days after send → **short**. Define: short ≤ 45 days, medium 46–120, long > 120, `unknown` if missing. |
| `task_id: prospect_welcome_day0` | `day0` is the cadence day index; the welcome is the day-0 step of the cadence being started. |
| `required_states` | These are the **audit states the output must attest to**. Emit them verbatim in a `states` array after the corresponding rule passes. `brand_style_applied` as a checkable rule = the style linter below passes (greeting pattern, short brand name, ≤1 `!`, no emoji, no URL shortener, no ALL CAPS, one question, numbered options, STOP sentence last). |
| `personalization_score_min: 0.85` | Proxy = (personalization slots filled) / (slots available in input). Slots: first_name, property short name, preferred channel honored, timezone-correct send time, language-correct template, horizon-correct cadence, persona/stage-correct template. Example fills 7/7 = 1.0. Threshold 0.85 means at most one miss when all seven are available. |
| `reply_classification_f1_min: 0.9` | The agent also **classifies inbound replies** to its own messages. Expect hold-out records with an inbound text (`1`, `2`, `STOP`, `HELP`, "not interested", "already leased", free-text question). Output for those is a classified intent plus a follow-up action. |
| `p95_latency_ms: 2000` | Whole decision must be rule-based, no LLM in the critical path (or a single bounded LLM call for free-text intent only). |

## 2. Legal grounding

| Rule | Authority | Requirement encoded | Example vs law |
|---|---|---|---|
| Marketing SMS needs opt-in | TCPA, 47 U.S.C. §227; 47 CFR §64.1200(a)(2) — prior express **written** consent for marketing texts to mobile numbers | `sms_opt_in` must be true; no exception for "transactional" in our layer (fail closed) | Same |
| Quiet hours | 47 CFR §64.1200(c)(1): no telemarketing calls/texts before 8:00 or after 21:00 **recipient's** local time | Send window bounded by local time, computed from `input.timezone` | **Example is stricter (09:00).** Follow the example: Texas Bus. & Com. Code §301.051 sets 9:00–21:00 Mon–Sat and **12:00–21:00 Sunday**; Florida FTSA §501.059 is 8:00–20:00 with max 3 attempts/24h; Washington RCW 80.36.390 is 8:00–20:00. The intersection that is safe in every state: **09:00–20:00 Mon–Sat, 12:00–20:00 Sunday**. Use that. |
| STOP/HELP | FCC revocation rule (47 CFR §64.1200(a)(10), effective April 11, 2025): opt-out via any reasonable means, honored within 10 business days; one confirmation text allowed. CTIA Messaging Principles: STOP/HELP keywords must work; opt-out language in messages | Every SMS ends with "Reply STOP to opt out."; inbound STOP/UNSUBSCRIBE/CANCEL/END/QUIT → mark opted out, stop cadence | Same |
| Commercial email | CAN-SPAM, 15 U.S.C. §7704: accurate header, non-deceptive subject, valid **physical postal address**, conspicuous unsubscribe honored within 10 business days | Email requires non-null `subject`, unsubscribe sentence, property address in footer | Example is SMS so silent; encode for email cases |
| Fair housing | Fair Housing Act, 42 U.S.C. §3604(c): unlawful to publish any statement indicating a preference/limitation based on race, color, religion, sex, disability, familial status, national origin. HUD ad guidance (24 CFR 109, still used as reference) | Body never references protected classes or coded proxies ("great schools", "young professionals", "safe/quiet neighborhood", "Christian community", "no kids", "walkable for seniors", "English-speaking") even when the profile contains such data | Same (`no_sensitive_discrimination`) |
| State protected classes | Add: source of income (WA, CA, NY, OR, CO, MN, IL, etc.), sexual orientation/gender identity (~23 states), age, marital status, military status, immigration status (CA, NY) | Same lexicon gate; treat as protected everywhere, not per state | Stricter than FHA; correct for a national vendor like RealPage |
| Reasonable accommodation | FHA §3604(f)(3)(B) | If profile has a disability/accommodation field, never mention it in marketing; route to human (`escalate_to_human`) only when the input asks for one | — |
| Language | No federal mandate, but HUD 2016 LEP guidance: refusing to serve because of language = national-origin discrimination | Honor `language`; keep the STOP keyword in English in all languages (CTIA) | — |

Where the example is stricter than law, follow the example: it is the ground truth for the grader, and it is never wrong to be later than 09:00 or to require consent that law would excuse.

## 3. The rulebook (11 rules: 5 gates, 6 shapers)

Gates run first in order; any gate failure ends with `next_message: null`. Shapers run in order and each may append to `why`. Every rule appends one line to `why`.

**G1. consent_gate** (gate)
```
consent = input.consent or {}                           # missing → all false
allowed = [c for c in ["sms","email","voice"] if consent.get(f"{c}_opt_in") is True]
if not allowed: STOP → next_action {type:"suppress", reason:"no_consent"}
why += "consent_verified: sms=T email=T voice=F"; states += consent_verified
```
Missing field: treat as false. Never infer consent from `channel_preferences`.

**G2. lifecycle_gate** (gate)
```
stage = lifecycle_stage
if stage in {"closed","lost","do_not_contact","opted_out","evicted","deceased"}
   or input.get("do_not_contact") is True:
   STOP → next_action {type:"suppress", reason:f"lifecycle_{stage}"}
if persona not in {"prospect","applicant","resident","former_resident"}:
   STOP → next_action {type:"escalate_to_human", reason:"unknown_persona"}
```
Missing stage → treat as `"new"` for prospect, `"active"` for resident; log in why.

**G3. inbound_reply_gate** (gate, only fires if `input.inbound_reply` / `last_inbound_message` exists)
```
text = normalize(reply)  # lowercase, strip punctuation
if text in {"stop","unsubscribe","cancel","end","quit","stopall"}:
    intent="opt_out"; STOP → next_message null, next_action {type:"mark_opted_out", channel:reply.channel}
elif text == "help": intent="help"; message = help template (transactional, allowed)
elif text matches r"^\s*[12]\s*$": intent="choose_option"; option = options[int(text)-1] → confirmation message, next_action {type:"schedule_tour", name:option}
elif text in negative lexicon ("not interested","no thanks","already leased","signed elsewhere","wrong number","remove me"):
    intent="not_interested"; STOP → next_message null, next_action {type:"stop_cadence", name:current_cadence}
elif text matches question lexicon ("?", "how much","price","rent","pets","available","deposit"):
    intent="question"; next_action {type:"escalate_to_human", name:"leasing_agent_reply"}; next_message = short ack ("Thanks Taylor—a leasing team member will reply shortly.")
else: intent="unknown" → escalate_to_human
why += f"reply_classified: {intent}"
```
Reply intent is also emitted top-level as `reply_classification`.

**G4. frequency_gate** (gate)
```
if input.last_message_sent_at and ref - last_message_sent_at < 24h: 
   STOP → next_action {type:"wait", name:"min_interval_24h", resume_at: last_sent+24h}
if input.messages_sent_24h >= 3 (FL rule): same
```
Missing → pass.

**G5. horizon_sanity_gate** (gate)
```
if persona=="prospect" and move_date_target and move_date_target < send_date:
   STOP → next_action {type:"escalate_to_human", reason:"move_date_past"}
```
Missing move date → pass, horizon = unknown.

**S1. channel_select** (shaper)
```
prefs = channel_preferences or ["sms","email","voice"]
channel = first(c for c in prefs if c in allowed) or first(allowed)
if channel == "voice": next_message null; next_action {type:"create_call_task", name:f"{persona}_{intent}_call"}; STOP
why += f"channel={channel}: first consented entry in preferences {prefs}"
```
Tie-break: preferences order, then sms > email. Voice is never automated.

**S2. send_time** (shaper)
```
tz = input.timezone or property.timezone or "America/New_York"
ref = max(last_interaction, now) in tz        # now = record's implied clock; use last_interaction if now absent
candidate = ref.date() at 09:00 tz
if candidate <= ref + 30min: candidate += 1 day
while True:
   if candidate.weekday()==Sunday: candidate = candidate.replace(hour=12)   # Sunday floor 12:00
   break
send_at = candidate.isoformat(with local offset, DST-aware)
why += f"send_at: next 09:00 {tz} after {ref_local}; quiet hours 09:00–20:00 (Sun 12:00)"
```
Missing timezone → use property tz; else default with why line "timezone_missing: defaulted". DST is computed by the zoneinfo library, never hard-coded.

**S3. horizon_and_cadence** (shaper)
```
days = (move_date_target - send_date).days if move_date_target else None
horizon = "short" if days<=45 else "medium" if days<=120 else "long"; None→"unknown"
intent = intent_table[(persona, stage)]   # prospect/new→welcome, prospect/engaged→follow_up, prospect/touring→tour_reminder,
                                          # applicant/applied→application_status, applicant/approved→lease_signing,
                                          # resident/active(lease_end<=90d)→renewal, resident/notice→move_out, resident/delinquent→payment_reminder
next_action = {type:"start_cadence" if stage in {"new","approved","applied"} else "continue_cadence",
               name:f"{persona}_{intent}_{horizon}_horizon"}
```

**S4. cta_select** (shaper)
```
cta_type = cta_map.get(constraints.primary_cta) or default_cta[intent]
cta_map = {book_tour:schedule_tour, apply:start_application, renew:renew_lease, pay:pay_balance,
           upload_docs:upload_documents, confirm:confirm_appointment, none:null}
if cta_type == schedule_tour:
   options = first 2 weekdays d with d >= send_date+2 and d in same Mon–Fri week; if <2 → Mon,Tue of next week; phrase="this week"/"next week"
   options rendered as ["Thu","Fri"]
```
Missing constraint → default for intent. `cta: null` when type is none.

**S5. compose** (shaper)
```
template = templates[(intent, channel, language or "en")]
slots: first_name (fallback "there"), brand_short, phrase, day_long_1/2, day_short_1/2
SMS: body = f"Hi {first}—welcome to {brand}! Tours are available {phrase}. Would you like to book a time on {D1} or {D2}? Reply 1 for {d1}, 2 for {d2}. Reply STOP to opt out."; subject=null
Email: subject = f"{brand}: {intent headline}"; body = greeting + same CTA as links/numbers + "Reply STOP or click unsubscribe to opt out." + property physical address line; requires property.address (missing → why line "address_missing" and set channel fallback to sms if consented, else suppress with reason "cannot_satisfy_can_spam")
```
Missing first_name → "Hi there—" and personalization slot counted as unavailable (not missed).

**S6. safety_and_style_validate** (shaper; can demote to suppress)
```
pii regexes: email, phone, street address (\d+ \w+ (St|Ave|Rd|...)), SSN, last_name literal, income/$ amounts from profile
protected lexicon: race/religion/national-origin/sex/family/disability terms + coded proxies list
style lint: starts with "Hi {first}—"|"Hi there—"; count("!")<=1; no emoji; no URL shortener; not ALL CAPS words except STOP/HELP; SMS ends with "Reply STOP to opt out."; len<=320
if pii or protected hit: regenerate from safe template with offending slot removed; recheck; if still failing → suppress reason "safety_violation"
states += fair_housing_check_passed, brand_style_applied
personalization_score = filled/available; if < thresholds.personalization_score_min: why += "personalization_below_min" (still send)
```

Ordering summary: G1 consent → G2 lifecycle → G3 inbound reply → G4 frequency → G5 horizon sanity → S1 channel → S2 time → S3 cadence → S4 CTA → S5 compose → S6 validate → assemble.

## 4. Predicted hold-out cases (14) and correct output shape

| # | Scenario | Probes | Correct output |
|---|---|---|---|
| 1 | prospect/new, `sms_opt_in:false`, email true, prefs `["sms","email"]` | G1+S1 | channel email, non-null subject, body with unsubscribe + property address, cta schedule_tour, start_cadence |
| 2 | prospect/new, all opt-ins false | G1 | `next_message: null`, next_action `suppress` reason `no_consent` |
| 3 | prefs `["email","sms"]`, both consented | S1 | email wins over sms (preference order, not default) |
| 4 | last_interaction 02:30Z with tz America/Chicago (= 20:30 previous evening) | S2 | next-day 09:00-06:00 |
| 5 | last_interaction 13:15Z Chicago (= 07:15 local) | S2 **trap** | **same-day** 09:00, not next day |
| 6 | tz America/Los_Angeles in December, or America/Phoenix | S2 **trap** | offset `-08:00` (PST) / `-07:00` (AZ no DST); wrong offset = fail |
| 7 | Friday or Saturday interaction | S2+S4 | Sat 09:00 allowed; Sunday → 12:00 or roll to Mon; tour options "next week" Mon/Tue |
| 8 | `language:"es"` | S5 | Spanish body, first name, `Responde 1 … 2 …`, still contains literal "STOP" |
| 9 | resident/active with `lease_end_date` ~60 days out | S3+S4 | intent renewal, cta renew_lease, next_action start_cadence `resident_renewal_short_horizon` |
| 10 | resident, work-order/package "transactional" note, `sms_opt_in:false`, email true | G1 **trap** | do not send SMS "because it's transactional"; email or suppress |
| 11 | input has inbound reply `"STOP"` | G3 **trap** | `next_message: null`, next_action `mark_opted_out`; do not send a marketing reply |
| 12 | inbound reply `"2"` after Thu/Fri offer | G3 | confirmation SMS for Friday, next_action `schedule_tour` (name "Fri"), reply_classification `choose_option` |
| 13 | profile contains `household: 2 adults 3 kids`, `religion`, `wheelchair_user:true`, `national_origin`, or notes "wants good schools" | S6 **trap** | identical welcome message with zero reference to any of it; states include fair_housing_check_passed |
| 14 | profile contains last_name, phone, email, income, SSN4; property has street address | S6 | SMS uses first name only, no address, no contact echo |
| 15 | `move_date_target` 6 months out, or missing, or in the past | S3/G5 | long_horizon cadence with lower-key CTA; unknown_horizon; past date → escalate_to_human, no message |
| 16 | `voice_opt_in:true` only, prefs `["voice"]` | S1 | `next_message: null`, next_action `create_call_task` |

Top three traps: #5/#6 (time rule and DST offset), #13 (protected-class data in profile that must be ignored), #11 (STOP reply must yield no send). Close fourth: #10 (transactional-consent excuse).

## 5. Output-shape decisions

- Top-level keys, always present: `task_id`, `decision` (`"send"` | `"do_not_send"`), `next_message`, `next_action`, `why` (array of strings, one per rule), `states` (array echoing required_states achieved), `reply_classification` (null unless an inbound reply exists), `personalization_score` (float).
- `next_message` when sending: exactly `{channel, send_at, subject, body, cta}`. `subject` key present and `null` for sms; string for email. `send_at` ISO-8601 with numeric local offset (`-06:00`), seconds included, never `Z`.
- `cta`: `{type, options}`; `options` is an array of short day names (`"Thu"`) for tours; `options: []` for CTAs without choices; `cta: null` when no CTA.
- `cta.type` vocabulary: `schedule_tour`, `start_application`, `upload_documents`, `renew_lease`, `pay_balance`, `confirm_appointment`, `reply_help`.
- `next_action.type` vocabulary: `start_cadence`, `continue_cadence`, `pause_cadence`, `stop_cadence`, `suppress`, `wait`, `mark_opted_out`, `escalate_to_human`, `create_call_task`, `schedule_tour`. Always include `name`; add `reason` on suppress/wait/escalate.
- "Do not send" = `next_message: null` (key present), `decision: "do_not_send"`, `next_action` explains why. Never emit an empty-string body or omit the key.
- Cadence name pattern is fixed: `{persona}_{intent}_{horizon}_horizon`, lowercase snake_case.
- Body exactness: match the example's punctuation conventions (em dash after name, period after "opt out"), because "semantic match" graders often diff structure and required phrases (`Reply STOP`, `Reply 1 for`, first name, brand short name) even when they tolerate wording.
