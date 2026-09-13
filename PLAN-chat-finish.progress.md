# Progress: PLAN-chat-finish

## T1 Tidy the rulebook — done 2026-09-13
- Rewrote `chatbot/hermes-profile/SOUL.md` (161 → 124 lines; Never-do list kept word for word): one "two fixed layouts" section (deep dive + normal answer) replaces the tables-for-3+, `###` headings, "say how many more exist" and old Bottom line leftovers.
- `check-readable.sh` part 1 now looks for `**Next:**` / `**Sources:**` (it was failing before: SOUL.md no longer said "Bottom line").
- `PLAN-deep-dive.md`: D4 marked dropped (replaced by the 4-line deep dive).
- Checked: `bash tooling/dev.sh` rebuild, then curl'd "Which buildings sold recently?", "Which 3 leads should I call first this week?", "Deep dive on Orchards Market Plaza Senior Apts, Plano" — all ~40 words, bold, correct layout, plain source names, no codes. Check line passes.
- Open: nothing.
