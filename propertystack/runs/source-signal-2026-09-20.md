# What the under-read alarm says about the four Texas suspects (2026-09-20)

Measured live by running each recipe through `run_area.run_recipe` with stats and passing the
result to `run_area._source_signal`. No files were changed by this check.

| source | endpoint rows | apartment rows | kept | aged out | newest record | flag |
| --- | --- | --- | --- | --- | --- | --- |
| fort-worth | 2,227 | 640 | **1** | 45 | 2026-08-25 (26 days) | **suspect** |
| san-antonio | 156 | 154 | **2** | 0 | 2025-11-24 (300 days) | **suspect** |
| san-marcos | 168 | 168 | **4** | 1 | 2026-06-12 (100 days) | **suspect** |
| austin | 176 | 176 | 47 | 8 | 2026-08-27 (24 days) | clear |
| houston (city permits) | 34 | 18 | 18 | 0 | 2026-07-30 (52 days) | clear |

## What this already proves

- **Fort Worth is the worst of the four.** 640 apartment rows reached the recipe and 45 were
  dropped for age, which leaves roughly 595 rows unaccounted for against a single kept lead. The
  recipe's own note records a live `returnCountOnly` of 2,227 matching rows since 2024-09-01, and
  `endpointRows` now confirms all 2,227 are being fetched -- so the loss is after the fetch, not
  in paging. Recipe notes also record `Full_Street_Address` as null on sampled rows.
- **San Antonio is not only small, it is nearly a year behind.** Its newest permit is 2025-11-24,
  300 days old. Another 65 days and it trips the stale flag as well.
- **San Marcos** keeps 4 of 168 with only 1 row aged out.
- **Austin is genuinely healthy** by this measure and should not have been on the suspect list.
- **Houston's city permit feed is not under-reading** -- it keeps every one of the 18 apartment
  rows its endpoint holds. The feed is simply tiny. That makes the question for it "what does it
  uniquely add over the 383-lead county file", not "what is it dropping".

## The one caveat on the ratio

`merge_records` collapses several rows at the same address into one project, so `kept` is
legitimately lower than `apartmentRows` for any source that lists a building per structure --
San Antonio's Orion Apartments alone is 8 rows for 1 project. The flag is therefore called
**suspect**, not broken. A gap of 154 to 2 or 640 to 1 is far past what merging explains.
