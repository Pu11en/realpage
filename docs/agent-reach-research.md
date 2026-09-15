# Agent Reach: what it can do for PropertyStack

## What it is
- A free, open tool (MIT license, anyone can use it) that lets an AI **read and search social sites** from the command line.
- It is really a bundle of other small tools: YouTube reader, web page reader (Jina, which we already use), Reddit reader, X/Twitter reader, and more.
- **No monthly bill.** Everything is free. It runs on your own computer.

## What works with no login ✅
- **YouTube**: search videos and read full transcripts (what people say in the video).
- **Any web page**: through Jina, same as the lead finder already does.
- **News feeds (RSS)** and **public GitHub**.

## What needs a logged-in account ⚠️
- **Reddit, X/Twitter, LinkedIn, Facebook, Instagram** all need the cookies from a browser where you are logged in.
- The tool's own docs warn: **these sites can detect it and ban the account.** They say to use a spare account, never your main one.
- LinkedIn is the strictest about this. Reddit and X are medium risk if we go slow (a few searches a week, not thousands).

## What it means for us
- The **safe, free core** is YouTube + web pages + news. That alone can find reviews, walk-through videos and local news about Texas buildings.
- **Reddit is the big prize** (the AI Visibility report already quotes Reddit threads like "RealPage needs to go", 15.5k upvotes), but it needs a spare Reddit account.
- We'd run it **weekly with the Texas refresh**, save the results as a file, and the site just shows the saved file. No live scraping on the website itself, so nothing breaks in a demo.

## How it could feed AI Visibility
- The AI Visibility to-do list already says "show up where operators talk". This section would **show exactly what they are saying**, with links.
- It can count how often RealPage, Yardi, Entrata and AppFolio come up, and whether people sound happy or angry. That explains *why* AIs recommend Yardi.
