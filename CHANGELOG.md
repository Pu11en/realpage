# Changelog

## v1.0 — 2026-09-17

CraneSignal v1.0 is a production-ready property data assistant. The system includes a website that maps local commercial properties and displays their financials, a chat service that answers questions about specific properties, and backend tools that crawl and normalize RealPage property listings.

**What works:** The website lets users find properties on a map and filter by area. The chat answers questions about property details, company financials, and market comparisons using data from the RealPage knowledge base. Users can sign up, save favorites, and share property links.

**What's included:** A website service (site/) serving the map and property pages on HTTPS, a chat service (chatbot/) running the AI agent with property data, and data tools (tooling/ and propertystack/skills/) that maintain the RealPage library. All code is clean, tested, and documented.

**What's deliberately not built yet:** Account management and payment processing (signup is open to all); social sharing and team collaboration; competitor tracking and lead generation alerts.

**To use it:** Follow the README to start the services locally or deploy using the provided Dockerfiles. All tests pass (253).
