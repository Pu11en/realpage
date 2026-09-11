# PropertyStack test guide (5 minutes)

Open **http://localhost:8765/master-table.html**

## 1. The Master Table
- Big number up top should say **204** buildings, all Collin County, **42** leads.
- Type `Legacy` in the search box → a handful of Legacy-named buildings show.
- Type `zzzz` → the table goes empty without breaking. Clear it.
- Click the **Units** column header → rows re-sort biggest/smallest.
- Click any row → that building's own page opens.

## 2. A building page
- Name, photo-free basics (units, year, owner), website link and software name all show.
- Click the website link → it opens the real apartment site (not a parked/spam page).
- Click **Back** → you return to the table.

## 3. Software Share page
- Bars for RealPage / Yardi / Entrata etc. move when you click the legend or change any filter.

## 4. Under the Hood page
- Shows the pipeline runs; no red errors, no "undefined" text anywhere.

## 5. The chat (the new stuff)
- On the Master Table, tap the **Ask** button (bottom corner on phone).
- Ask: `Which Richardson buildings use Yardi?` → it answers with a table.
- Follow up: `which of those is biggest?` → it remembers the previous answer.
- Click **New chat** → conversation wipes clean; ask again and it starts fresh.
- On your phone width (shrink the window), nothing should overflow sideways.

## What "pass" means
Everything opens, nothing says `NaN`/`undefined`, no sideways scrolling, chat follows along.
If anything looks off, screenshot it and tell me what you clicked.
