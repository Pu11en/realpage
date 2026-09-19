# CraneSignal editions

One product, several versions ("editions"). Only one is live at a time.
Each edition is a git branch in this repo (and the same-named branch in the nested `business/` repo for the landing page).

| Edition | Branch | Who it's for | Front page headline |
|---|---|---|---|
| **Software Sellers** (live on `main`) | `edition/software-sellers` | Companies selling software/services to apartment managers | "New apartment buildings. Before your competitor calls." |
| Investors (saved) | `edition/investor` | Real estate investors, brokers, lenders | "Apartment buildings that just sold. And what's coming next." |

Shared in every edition: open site (no login to see data), chat panel open by default (closable; returns on the next visit), free account needed only to use the chat, New York hidden until it has real data.

Switch: `git checkout main && git reset --hard edition/<name>` in both repos (after saving main to its own edition branch), push `main`, then `cd business/marketing/landing && railway up --service propertystack-landing --ci`.
