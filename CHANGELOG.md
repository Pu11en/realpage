# Changelog

## v1.0 — 2026-09-17

CraneSignal v1.0 is a production-ready lead finder for anyone selling to apartment owners.
The system includes a website that maps apartment buildings and flags those most likely to buy soon,
a chat service that answers questions about specific properties with sources, and backend tools that
detect which property-management software every building runs and identify early-stage prospects.

**What works:** The website lets users find apartment buildings on a map, filter by area and software,
and see which recently changed ownership or are under construction. The chat answers questions about
property details, installed software, and market trends using public-source data. All sources link back
to the original web page or document.

**What's included:** A website service (site/) serving the map and property pages on HTTPS, a chat service
(chatbot/) running the AI agent with property data, and data tools (tooling/ and propertystack/skills/) that
detect software and score leads. All code is clean, tested, and documented.

**What's deliberately not built yet:** Account management and payment processing (all data is free);
saved searches; lead alerts; team collaboration and shared notes.

**To use it:** Follow the README to start the services locally or deploy using the provided Dockerfiles. All tests pass (253).
