# Open-source pieces we can reuse (researched 2026-09-17)

## 1. Quiet hours / TCPA windows + offline area-code → timezone

| Repo | URL | License | Lift | Verdict |
|---|---|---|---|---|
| python-phonenumbers | https://github.com/daviddrysdale/python-phonenumbers | Apache-2.0, 3.8k stars, pushed 2026-09-10, PyPI 9.0.39 | `phonenumbers.timezone.time_zones_for_number()` — offline area-code→IANA. Tested: 480→`America/Phoenix`, 214→`America/Chicago`, 305→`America/New_York`. Also `geocoder.description_for_number()` gives state name. | **USE** (only if records can lack a timezone; you said records carry IANA tz, so this is a fallback) |
| tcpa-quiet-hours | https://github.com/drewthomas00/tcpa-quiet-hours | MIT, 0 stars, JS, pushed 2026-08-13 | `jurisdiction-data.js`: STATE→IANA table, ZIP3→state, area-code→state, plus the state window table (Fed 8-21; MD 8-20; AL/FL/LA/MS 8-20 + Sunday ban; UT Sunday ban; SD 9-21 + Sunday ban). **Missing Texas** (Bus. & Com. Code 305.053: Mon-Sat 9-21, Sunday 12-21) and OK 8-20. Ship it as a 15-line Python dict, not the JS. | **VENDOR DATA** (copy the table into `quiet_hours.py`, add TX/OK yourself) |
| call-trust-kit | https://github.com/KaiCalls/call-trust-kit | MIT, 0 stars, TS, 2026-06 | 51-state matrix, but Python access is via CLI-as-JSON bridge | SKIP (heavyweight for tonight) |
| Areacodes-States-Timezones | https://github.com/ilanpatao/Areacodes-States-Timezones | no license, 2018 | `data.json` area code→state→"CST" abbreviations (not IANA) | SKIP (phonenumbers does it better, licensed) |

No maintained Python TCPA-window library exists. Write the 11-state dict yourself (~30 lines); the JS repo is your crib sheet.

## 2. Fair housing word lists + offline PII

| Repo | URL | License | Lift | Verdict |
|---|---|---|---|---|
| comehomealabama `scripts/journal/lint-fair-housing.py` | https://github.com/jeremylongshore/comehomealabama/blob/main/scripts/journal/lint-fair-housing.py | (check repo LICENSE; it's a 60-line phrase list, rewrite trivially) | Two Python lists already split HARD ("no kids", "adults only", "safe neighborhood", "christian community", "white neighborhood", "able-bodied"...) vs WARN ("great schools", "family-friendly", "near churches", "quiet neighborhood", "master bedroom", "exclusive"). Exactly your shape. | **VENDOR DATA** (retype as your own `FAIR_HOUSING_HARD / WARN`) |
| v0-Vip-Re-OS-V1 `lib/compliance-rules/fair-housing-patterns.ts` | https://github.com/YHSG-Kling/v0-Vip-Re-OS-V1/blob/main/lib/compliance-rules/fair-housing-patterns.ts | unlicensed | Regex + severity + suggested compliant rewrite + legal cite per phrase (e.g. `/young\s+professional/` → "Urban location with dining", § 3604(c)). The "fix" column is gold for the LLM re-draft prompt. | **VENDOR DATA** (borrow the fix strings and cites) |
| Fair Housing Institute PDF | https://www.fairhousinginstitute.com/wp-content/uploads/2020/06/Fair-Housing-Advertising-Words-Phrases-List-1.pdf | public | The canonical 3-tier list if you want to be exhaustive | reference only |
| Presidio analyzer | https://github.com/microsoft/presidio (redirects to data-privacy-stack/presidio) | MIT, 10.9k, pushed today | Regex+NER; wheel is 266 KB but pulls spaCy + a 500 MB model for NER | SKIP tonight |
| scrubadub | https://github.com/LeapBeyond/scrubadub | Apache-2.0, 432, last push 2023 | Regex detectors for phone/email/SSN/URL; address needs spaCy extra | SKIP (2 yrs stale; stdlib `re` is lighter) |
| CommonRegex | https://github.com/madisonmay/CommonRegex | MIT, 1.6k, last push 2023 | `commonregex.py` is one file: phone/email/SSN/street-address/zip regexes | **VENDOR DATA** (copy the 6 regexes into `pii.py`; don't pip install a 2023 package) |

Lightest for a short message: 6 regexes in 20 lines. Presidio is the right answer for production, wrong for tonight.

## 3. SMS composition

| Repo | URL | License | Lift | Verdict |
|---|---|---|---|---|
| sms-toolkit | https://github.com/chrisconlon-klaviyo/sms-toolkit (PyPI `sms-toolkit` 1.0.9) | MIT, Klaviyo-origin, pure Python, no deps | `sms_toolkit.messages.profiling.profile_message(text)` → `num_segments`, `message_length`, `max_segment_size`. Verified tonight: hyphen version → 160-char GSM-7 budget; em-dash version → 70-char UCS-2 budget. Exactly the em-dash warning you want. Also has GSM-7 extended chars (`[]{}~^|€\`) counted as 2. | **USE** |
| sms-counter (PyPI 0.0.1) | https://pypi.org/project/sms-counter/ | 2024, v0.0.1 | same idea, less tested | SKIP |
| twilio-labs segment calculator | JS only, 404 on the Python fork names | — | — | SKIP |

STOP/HELP conventions: no library; it's a constant. Append `Reply STOP to opt out` (CTIA recommends STOP/HELP in the first message and periodically) and treat inbound `STOP|STOPALL|UNSUBSCRIBE|CANCEL|END|QUIT` (case-insensitive, Twilio's list) as opt-out. Ten lines.

## 4. Rules engines

| Repo | URL | License / activity | Beats plain functions tonight? |
|---|---|---|---|
| venmo/business-rules | https://github.com/venmo/business-rules | MIT, 994, last push 2024-08 | No. Designed for non-coders editing JSON; you'd write variable/action classes for every field. |
| durable-rules (jruizgit/rules) | https://github.com/jruizgit/rules | MIT, 1.3k, last push 2025-07 | No. Forward-chaining, C extension, awkward install; overkill for 11 ordered rules. |
| experta (pyknow successor) | https://github.com/nilp0inter/experta | LGPL-3.0, 196, 2025-02 | No. LGPL, Rete engine, unordered matching fights your explicit ordering. |
| json-logic-py | https://github.com/nadirizr/json-logic-py | MIT, 225, 2023 | No. Only useful if rules must be data; yours are code. |
| zeroSteiner/rule-engine | https://github.com/zeroSteiner/rule-engine | BSD-3, 598, pushed 2026-08 | No, but it's the only healthy one: a safe expression language (`consent.sms and stage == 'lead'`) over dicts. Consider only if you want rules editable in the eval harness. |
| gorules/zen | https://github.com/gorules/zen | MIT, 2k, 2026-08 | No. Rust core + JSON decision tables; slick but heavy for a one-night build. |

Blunt answer: a list of `(name, fn)` tuples where each fn returns `Gate(pass, reason)` or `Shape(patch, reason)` and a 10-line runner that appends to a `rule_trail`. That is your rule trail for free; no engine gives you a better one.

## 5. Reference patterns / structured LLM output

| Repo | URL | License / activity | OpenAI-compatible (DeepSeek)? | Verdict |
|---|---|---|---|---|
| instructor | https://github.com/567-labs/instructor | MIT, 13.9k, pushed yesterday, PyPI 1.17.0 | Yes: `instructor.from_openai(OpenAI(base_url="https://api.deepseek.com"))`, `Mode.JSON` or `MD_JSON` (DeepSeek only supports `json_object`, not `json_schema`). Pydantic model + `max_retries=2` gives you validate-then-regenerate with the validator errors fed back. | **USE** (or replicate: 30 lines with `response_format={"type":"json_object"}` + `pydantic.model_validate_json` + one retry loop; either is fine) |
| outlines | https://github.com/dottxt-ai/outlines | Apache-2.0, 15.8k | Constrained decoding needs local logits; the OpenAI adapter only passes `json_schema` through, which DeepSeek lacks | SKIP |
| guardrails-ai | https://github.com/guardrails-ai/guardrails | Apache-2.0, 7.4k | Works via litellm, but the Hub validator install flow and size are not a one-night thing | SKIP (steal the concept: validate → reask with errors) |
| NeMo Guardrails | https://github.com/NVIDIA/NeMo-Guardrails | Apache-2.0, 7.2k | Yes via LangChain OpenAI, but Colang DSL + LangChain dep | SKIP |
| promptfoo | https://github.com/promptfoo/promptfoo | MIT, 25k, pushed today | Node CLI; `providers: - id: openai:chat:deepseek-chat` with `apiBaseUrl`; `assert: type: javascript/python` for deterministic checks + `llm-rubric` for the judge | **USE** if Node is acceptable; otherwise a 40-line pytest that loops JSONL and calls your pipeline is simpler and has no Node dep |

No open-source "agent decides whether/when/how to contact a customer" reference of your shape surfaced in GitHub search worth copying; the two TCPA repos above are the closest and are JS gates, not decision pipelines.

## 6. Timezone / DST

- `zoneinfo` (stdlib 3.9+) is right. On `python:*-slim` / Alpine there is no `/usr/share/zoneinfo`, so `pip install tzdata` (2026.4 on PyPI) or you get `ZoneInfoNotFoundError`.
- Offsets render correctly with `isoformat()`; verified on this box: Phoenix July → `2026-07-01T10:00:00-07:00`, Chicago July → `-05:00`, Chicago January → `-06:00`. Never call `.astimezone(timezone.utc)` before formatting or you get `+00:00`; Python never emits `Z` from `isoformat()`, so no fix needed there.
- Phoenix gotcha is only that `America/Phoenix` has no DST; `zoneinfo` handles it. Compute send_at by building the local wall-clock time with `datetime(..., tzinfo=ZoneInfo(tz))` (not `replace` on a UTC value), then clamp to the window; `fold=0/1` only matters in the 1 am DST-fallback hour, which is outside 8-21 anyway.
- Validate incoming tz strings with `try: ZoneInfo(tz) except ZoneInfoKeyError` and treat failure as a gate (no message) rather than defaulting.

## What I would actually install tonight

```
pip install openai pydantic instructor        # DeepSeek via base_url; instructor Mode.JSON for validate+retry (or hand-roll 30 lines)
pip install sms-toolkit                       # profile_message() for GSM-7/UCS-2 segment warning
pip install phonenumbers                      # only if a record can lack timezone; area-code -> IANA fallback
pip install tzdata                            # zoneinfo data on slim containers
# write yourself (no dep): quiet_hours.py (11-state dict cribbed from tcpa-quiet-hours/jurisdiction-data.js + TX/OK), fair_housing.py (HARD/WARN lists from lint-fair-housing.py + fix strings from fair-housing-patterns.ts), pii.py (6 regexes from CommonRegex), rules.py ((name, fn) pipeline with rule_trail)
```

Sources: [python-phonenumbers](https://github.com/daviddrysdale/python-phonenumbers), [tcpa-quiet-hours](https://github.com/drewthomas00/tcpa-quiet-hours), [lint-fair-housing.py](https://github.com/jeremylongshore/comehomealabama/blob/main/scripts/journal/lint-fair-housing.py), [fair-housing-patterns.ts](https://github.com/YHSG-Kling/v0-Vip-Re-OS-V1/blob/main/lib/compliance-rules/fair-housing-patterns.ts), [Fair Housing Institute list](https://www.fairhousinginstitute.com/wp-content/uploads/2020/06/Fair-Housing-Advertising-Words-Phrases-List-1.pdf), [sms-toolkit](https://pypi.org/project/sms-toolkit), [instructor DeepSeek guide](https://python.useinstructor.com/integrations/deepseek/), [DeepSeek JSON mode](https://api-docs.deepseek.com/guides/json_mode/), [venmo/business-rules](https://github.com/venmo/business-rules), [durable rules](https://github.com/jruizgit/rules), [rule-engine](https://pypi.org/project/rule-engine/), [Lead Friendly state hours](https://www.leadfriendly.com/guides/tcpa-calling-hours-by-state).
