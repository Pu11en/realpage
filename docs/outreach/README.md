# Outreach packs

A pack is the "few accounts your sales team should look at for free" from
`docs/2026-09-20-maintenance-software-icp.md`, made concrete: a one-page list a vendor can
check in thirty seconds and find true. Short and verifiable beats long and impressive.

## Make one

```bash
python3 tooling/outreach/build_pack.py --list                 # the profiles and their rules
python3 tooling/outreach/build_pack.py --profile opening-soon
python3 tooling/outreach/build_pack.py --profile opening-soon --metro Dallas --for AppWork
```

Writes to `docs/outreach/packs/`. Open it in a browser and print to PDF to attach, or send
the link if the reader is fine with HTML.

## The profiles

**`opening-soon`** — opening in the next 21 months, 100+ units. For vendors who sell before
the building opens: maintenance software, inspections, make-ready, resident tech, suppliers.
**This is the strong one.** 17 buildings match today and every one of them has a published
office phone, against 144 phones across all 1,861 buildings. The slice that matters is the
slice with the best contact data, which is luck worth using.

**`just-sold`** — a recorded sale in the last 12 months, 100+ units. For vendors whose buyer
changes when the building does. 200 match, but **none carry a phone**: sales come from county
appraisal records, which do not publish one. Use it to make the argument, not to hand someone
a call list.

## Who to send to

`docs/2026-09-20-maintenance-software-icp.md` already names the targets with phone numbers and
email addresses found from public sources — AppWork, Leonardo247, Maintenance Care and others,
with a call priority on each. Start at the top of that list.

The pitch is in the same doc and does not need rewriting:

> "We found Texas apartment communities with maintenance pain signals and can give you a few
> accounts your sales team should look at for free."

## What makes a pack work

- **Every row links its public record.** The reader can check any line. A test enforces this.
- **It says "15 of 17"**, not "15" — it is a sample and reads as one.
- **It says what the rule was and why**, so a reader who disagrees can say so. That is a
  conversation, which is the point.
- **Blanks mean the record is silent**, and the pack says so. Nothing is estimated.
- **It is `noindex` and needs no JavaScript**, so it survives being printed and forwarded.

## What not to do

- Do not send the whole database. The pack works because it is short.
- Do not hand-pick the rows. Selection is by rule so the choice is defensible and so the next
  pack is one command.
- Do not promise contact data the record does not have. `just-sold` has no phones; say so.
