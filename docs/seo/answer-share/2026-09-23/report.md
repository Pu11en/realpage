# What the AI engines answer — 2026-09-23

The before-picture, taken while the SEO work sits on a branch and nothing is
deployed. Re-run `tooling/seo/sample.py` in a few weeks and compare.

**These are not the consumer apps.** `claude-web` is `claude -p` on the
subscription with web search; `gemini` is the Gemini API with Google Search
grounding. A person typing into chatgpt.com or the Gemini app may see something
different. Treat this as a directional read, not a transcript.

Engines: claude-web, gemini · Questions answered: 50

## Set A — questions CraneSignal could be cited for

If the SEO work succeeds, CraneSignal starts appearing here. Today it should not.

**CraneSignal named in 0 of 30 Set A answers.**

| Named | Answers | Share |
|---|---|---|
| Yardi | 25 / 30 | 83% |
| CoStar | 19 / 30 | 63% |
| RealPage | 14 / 30 | 47% |
| CBRE | 8 / 30 | 27% |
| Apartments.com | 7 / 30 | 23% |
| Berkadia | 7 / 30 | 23% |
| Zillow | 5 / 30 | 17% |
| AppFolio | 4 / 30 | 13% |
| Buildium | 4 / 30 | 13% |
| Entrata | 4 / 30 | 13% |
| ResMan | 3 / 30 | 10% |
| MRI | 3 / 30 | 10% |
| Rent Manager | 2 / 30 | 7% |

## Set B — what the market is told to buy

We do not expect to appear here. This is the answer-share view.

| Vendor | Answers | Share |
|---|---|---|
| RealPage | 19 / 20 | 95% |
| Yardi | 17 / 20 | 85% |
| AppFolio | 16 / 20 | 80% |
| Entrata | 13 / 20 | 65% |
| Buildium | 12 / 20 | 60% |
| MRI | 7 / 20 | 35% |
| Rent Manager | 6 / 20 | 30% |
| Zillow | 4 / 20 | 20% |
| Apartments.com | 3 / 20 | 15% |
| CoStar | 2 / 20 | 10% |
| ResMan | 1 / 20 | 5% |

## Which sites the engines actually read

Counted across every answer, so this is who the engines currently treat as
authoritative on these questions — and therefore what a new page has to sit
alongside to get cited.

| Site | Answers citing it |
|---|---|
| realpage.com | 17 |
| appfolio.com | 11 |
| mmgrea.com | 9 |
| yardimatrix.com | 8 |
| multihousingnews.com | 6 |
| yardi.com | 6 |
| matthews.com | 6 |
| reddit.com | 6 |
| mrisoftware.com | 6 |
| cushmanwakefield.com | 5 |
| multifamilydive.com | 5 |
| credaily.com | 5 |
| re-leased.com | 5 |
| buildium.com | 5 |
| door.com | 4 |
| capterra.com | 4 |
| g2.com | 4 |
| houstonchronicle.com | 3 |
| northmarq.com | 3 |
| berkadia.com | 3 |

## Question by question

### A. How do I find apartment buildings under construction in Dallas?

- **claude-web** — CoStar (#1), Yardi (#2), RealPage (#3), Apartments.com (#4)
- **gemini** — RealPage (#1)
  - cited: culturemap.com, constructionwire.com, urbanize.city, realpage.com, permitflow.com, capitalconstructiongrp.com
  - **engines disagree on who comes first:** claude-web says CoStar; gemini says RealPage

### A. Where can I find a list of new apartment developments in Houston?

- **claude-web** — Yardi (#1), CoStar (#2), RealPage (#3)
  - cited: houstonchronicle.com, houston.org, mmgrea.com, houstontx.gov, yardimatrix.com, costar.com
- **gemini** — Apartments.com (#1), Yardi (#2)
  - cited: stagecoachmanagement.com, cushmanwakefield.com, matthews.com, tacostreetlocating.com, smartcitylocating.com, umovefree.com
  - **engines disagree on who comes first:** claude-web says Yardi; gemini says Apartments.com

### A. Which apartment complexes in Texas sold in 2025?

- **claude-web** — CoStar (#1), Yardi (#2), RealPage (#3)
  - cited: therealdeal.com, muskin-elam.com, multihousingnews.com, walkerdunlop.com, blog.swbc.com, finance.yahoo.com
- **gemini** — CoStar (#1)
  - cited: matthews.com, multifamilydive.com, multifamilygrp.com, biscred.com, tamu.edu, terrydalecapital.com

### A. How do I find multifamily construction pipeline data for Austin?

- **claude-web** — Yardi (#1), CoStar (#2), RealPage (#3), CBRE (#4), Apartments.com (#5)
  - cited: matthews.com, mmgrea.com, yardimatrix.com, yardi.com, multihousingnews.com, austinapartments.com
- **gemini** — Yardi (#1)
  - cited: mmgrea.com, matthews.com, yardimatrix.com

### A. Is there a free multifamily market report for San Antonio?

- **claude-web** — Yardi (#1), Berkadia (#2), CBRE (#3), RealPage (#4)
  - cited: berkadia.com, colliers.com, yardimatrix.com, institutionalpropertyadvisors.com, marcusmillichap.com, northmarq.com
- **gemini** — Yardi (#1), Berkadia (#2), CBRE (#3)
  - cited: cushmanwakefield.com, yardimatrix.com, berkadia.com, marcusmillichap.com, cbre.com

### A. How can I find out who bought an apartment complex?

- **claude-web** — CoStar (#1), Yardi (#2)
- **gemini** — CoStar (#1), Yardi (#2), Zillow (#3)
  - cited: nextautomation.us, northwestregisteredagent.com, buildout.com, lendingtree.com, proptracer.com, batchdata.io

### A. Where can I get a list of apartment buildings opening in 2027?

- **claude-web** — Yardi (#1), RealPage (#2), CoStar (#3)
- **gemini** — Yardi (#1), CoStar (#2), Apartments.com (#3)
  - cited: rentcafe.com, multifamilydive.com, yardi.com, credaily.com, culturemap.com

### A. How do I find new apartment projects before they open for leasing?

- **claude-web** — Apartments.com (#1), Zillow (#2), Yardi (#3), CoStar (#4), RealPage (#5)
- **gemini** — no tracked names
  - cited: fairfieldresidential.com, buildingradar.com, commloan.com, greystar.com, multihousingnews.com, rentreboot.com

### A. What public data sources show apartment construction permits in Texas?

- **claude-web** — Yardi (#1), CoStar (#2)
  - cited: nahb.org, trerc.tamu.edu, data.austintexas.gov, dallasopendata.com, data.sanantonio.gov, data.texas.gov
- **gemini** — no tracked names
  - cited: indexmundi.com, tamu.edu, nahb.org, stlouisfed.org, mercator.ai

### A. How do I build a lead list of new apartment buildings to sell to?

- **claude-web** — Yardi (#1), CoStar (#2), RealPage (#3), Apartments.com (#4), CBRE (#5), Berkadia (#6)
- **gemini** — CoStar (#1), Apartments.com (#2), Zillow (#3)
  - **engines disagree on who comes first:** claude-web says Yardi; gemini says CoStar

### A. Which property management software does a given apartment building use?

- **claude-web** — AppFolio (#1), Yardi (#2), RealPage (#3), Buildium (#4), Entrata (#5), ResMan (#6)
- **gemini** — RealPage (#1), Yardi (#2), AppFolio (#3), Buildium (#4), MRI (#5), Entrata (#6)
  - **engines disagree on who comes first:** claude-web says AppFolio; gemini says RealPage

### A. How can I tell what property management system a company runs?

- **claude-web** — Yardi (#1), RealPage (#2), AppFolio (#3), Entrata (#4), MRI (#5), Rent Manager (#6), Buildium (#7), ResMan (#8)
- **gemini** — AppFolio (#1), RealPage (#2), Buildium (#3), Yardi (#4), Entrata (#5), MRI (#6), Rent Manager (#7), ResMan (#8)
  - cited: thebusinessresearchcompany.com, researchnester.com, appfolio.com, realpage.com, faroutsolutions.com, nimbio.com
  - **engines disagree on who comes first:** claude-web says Yardi; gemini says AppFolio

### A. Where can I find Phoenix multifamily construction pipeline data?

- **claude-web** — Yardi (#1), RealPage (#2), CoStar (#3), CBRE (#4)
  - cited: azbex.com, kidder.com, azbigmedia.com, mmgrea.com, getmultifamily.com, phoenix.gov
- **gemini** — CoStar (#1), Yardi (#2), Berkadia (#3)
  - cited: kidder.com, matthews.com, mmgrea.com, multihousingnews.com, azbex.com
  - **engines disagree on who comes first:** claude-web says Yardi; gemini says CoStar

### A. What is the best way to find newly sold apartment complexes for sales prospecting?

- **claude-web** — CoStar (#1), Yardi (#2), CBRE (#3), Berkadia (#4)
  - cited: credaily.com, yardimatrix.com, reonomy.com, propertyradar.com, multifamilydive.com
- **gemini** — CoStar (#1), Yardi (#2)
  - cited: reddit.com, forage.ai, batchdata.io, compstak.com, reonomy.com, labusinessjournal.com

### A. Are there free alternatives to CoStar or Yardi Matrix for multifamily pipeline data?

- **claude-web** — CoStar (#1), Yardi (#2), CBRE (#3), Berkadia (#4), Zillow (#5)
  - cited: credaily.com, breakintocre.com, fred.stlouisfed.org, mmgrea.com, softwaresuggest.com
- **gemini** — CoStar (#1), Yardi (#2), CBRE (#3), Berkadia (#4), Zillow (#5)
  - cited: hellodata.ai, apartmentiq.io, reddit.com, multihousingnews.com, compstak.com, biggerpockets.com

### B. What is the best property management software for a multifamily apartment portfolio?

- **claude-web** — Yardi (#1), RealPage (#2), MRI (#3), Entrata (#4), AppFolio (#5), Buildium (#6)
  - cited: realpage.com, re-leased.com, appfolio.com, ustechautomations.com, mrisoftware.checkpointid.com
- **gemini** — Yardi (#1), RealPage (#2), Entrata (#3), AppFolio (#4), MRI (#5), Buildium (#6), Rent Manager (#7)
  - cited: re-leased.com, door.com, realpage.com, fortresstech.io, faroutsolutions.com, gartner.com

### B. What is the best property management system for 200-unit buildings in Texas?

- **claude-web** — Buildium (#1), AppFolio (#2), Yardi (#3), RealPage (#4), Entrata (#5), Rent Manager (#6)
  - cited: credaily.com, realpage.com, rentmanager.com, buildium.com, door.com, appfolio.com
- **gemini** — AppFolio (#1), Buildium (#2), RealPage (#3), Yardi (#4), Entrata (#5)
  - cited: realpage.com, v7labs.com, yardibreeze.com, intellectyx.com, softhealer.com
  - **engines disagree on who comes first:** claude-web says Buildium; gemini says AppFolio

### B. How does RealPage compare to Yardi for multifamily property management?

- **claude-web** — RealPage (#1), Yardi (#2)
  - cited: wsgr.com, justice.gov, duanemorris.com, realpage.com, nextautomation.us, bcsolut.com
- **gemini** — RealPage (#1), Yardi (#2)
  - cited: bcsolut.com, doorloop.com, door.com, realpage.com, cresoftware.tech, yardi.com

### B. Which is better for a small property management company: RealPage or AppFolio?

- **claude-web** — AppFolio (#1), RealPage (#2), Buildium (#3)
  - cited: selecthub.com, realpage.com, themortgagepoint.com, wsgr.com, capterra.com, bbb.org
- **gemini** — RealPage (#1), AppFolio (#2), Buildium (#3)
  - cited: balancedassetsolutions.com, appfolio.com, thecfoclub.com, bizflowkit.in, kelpic.com, realpage.com
  - **engines disagree on who comes first:** claude-web says AppFolio; gemini says RealPage

### B. What property management software do large Texas apartment operators use?

- **claude-web** — Yardi (#1), RealPage (#2), Entrata (#3), MRI (#4)
  - cited: justice.gov, legalclarity.org, multifamilydive.com, sec.gov, realpage.com, multifamilyinsiders.com
- **gemini** — RealPage (#1), Yardi (#2), MRI (#3), Entrata (#4), AppFolio (#5), Rent Manager (#6), Buildium (#7)
  - cited: houstonchronicle.com, miracuves.com, realpage.com, re-leased.com, appfolio.com, yardi.com
  - **engines disagree on who comes first:** claude-web says Yardi; gemini says RealPage

### B. What AI tools can help automate apartment leasing and prospect follow-up?

- **claude-web** — RealPage (#1), Yardi (#2), AppFolio (#3), Entrata (#4)
  - cited: gptbots.ai, vellum.ai, realpage.com, layer3labs.io, funnelleasing.com, realty-ai.com
- **gemini** — Buildium (#1), Yardi (#2), AppFolio (#3), RealPage (#4), Zillow (#5), Apartments.com (#6)
  - cited: buildium.com, mrisoftware.com, apartments247.com, moxiworks.com, funnelleasing.com, getaptly.com
  - **engines disagree on who comes first:** claude-web says RealPage; gemini says Buildium

### B. What tools do property owners use to set optimal rent pricing using market data?

- **claude-web** — RealPage (#1), Yardi (#2), Entrata (#3), Zillow (#4), Apartments.com (#5), CoStar (#6), AppFolio (#7), Buildium (#8)
  - cited: baselane.com, landlordstudio.com, rentana.io, aeve.ai, en.wikipedia.org, multifamilydive.com
- **gemini** — Zillow (#1), CoStar (#2)
  - cited: ifinderoffers.com, iconicpm.com, jakenfinancegroup.com, rentometer.com, housecanary.com, rentcast.io
  - **engines disagree on who comes first:** claude-web says RealPage; gemini says Zillow

### B. What is the best property management software for a 500-unit portfolio?

- **claude-web** — AppFolio (#1), Buildium (#2), RealPage (#3), Rent Manager (#4), Yardi (#5), MRI (#6), Entrata (#7)
  - cited: softwareconnect.com, appfolio.com, v7labs.com, quickbase.com, magicdoor.com, capterra.com
- **gemini** — Yardi (#1), RealPage (#2), AppFolio (#3), MRI (#4), Buildium (#5), Rent Manager (#6)
  - cited: re-leased.com, propertese.com, reddit.com, gatewise.com, raftlabs.com, mrisoftware.com
  - **engines disagree on who comes first:** claude-web says AppFolio; gemini says Yardi

### B. What software solutions handle utility billing and submetering for apartment communities?

- **claude-web** — Yardi (#1), RealPage (#2), Entrata (#3), AppFolio (#4)
  - cited: realpage.com, thinkutilityservices.com, meternetusa.com, oatesenergy.com, synergyutilitybilling.com, amcobi.com
- **gemini** — ResMan (#1), RealPage (#2), MRI (#3), Rent Manager (#4), AppFolio (#5), Yardi (#6), Entrata (#7)
  - cited: phoenixbillingsolutions.com, mrisoftware.com, myresman.com, realpage.com, utilmate.com, leaksense.io
  - **engines disagree on who comes first:** claude-web says Yardi; gemini says ResMan

### B. Which property management platform is best for a new apartment lease-up?

- **claude-web** — AppFolio (#1), Entrata (#2), RealPage (#3), Yardi (#4), Apartments.com (#5), Zillow (#6)
  - cited: realpage.com, appfolio.com, re-leased.com, door.com
- **gemini** — AppFolio (#1), RealPage (#2), Entrata (#3), Yardi (#4), Buildium (#5)
  - cited: mrisoftware.com, lula.life, quickbase.com, amerisave.com, appfolio.com

## How to read this

- Position beats volume: the first name in an answer is the one a reader acts on.
- 'cited' lists the hosts the engine actually read, which says who it treats as
  authoritative on the question. Those are the pages to be published alongside.
- Counts move week to week on their own. Only a repeated, sizeable change means
  anything.
