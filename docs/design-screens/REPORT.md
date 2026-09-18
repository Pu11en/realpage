# CraneSignal redesign: final report

Written 2026-09-15 at the end of the app redesign build. Everything is on this computer only: nothing was pushed or deployed.

## What changed, page by page
- **Every page:** the dark look is gone. Pages now use the same look as the landing page: white background, dark navy text, blueprint blue as the main color, amber for the one main button (the Ask button), thin grey lines. Headings use Plus Jakarta Sans, normal text uses Inter. Both fonts come from this site, not from Google.
- **Left menu:** light grey, CraneSignal name in blue, the open tab has a light blue background and an amber marker.
- **Early Leads:** the table has grey and white rows, blue links, navy State/Region buttons, a score circle in green (high), amber (middle) or muted red (low).
- **Property page:** white cards, blue source links. The colors written straight into the page were moved into the shared style file.
- **Map:** light grey land, states shaded in blue (darker = more tracked buildings), amber dots for the states we have leads in.
- **AI Visibility:** charts in blue, amber and grey that read well on white.
- **Under the Hood, Privacy, Master Table:** same light look. Master Table only sends you to the Map.
- **Chat panel inside the app:** blue header with an amber line, amber buttons.
- **Chat app on its own:** light mode by default, same fonts and colors, amber send button.
- **Landing page:** now uses the same two fonts, so it matches the app. Headlines keep the same size and weight.

## Final pass fixes (this task)
- ✅ **Keyboard focus ring** was amber, which is too faint on white. It is now blue, so people using the Tab key can see where they are.
- ✅ **Small grey text on grey rows** (source tags in Early Leads, "Last updated" at the bottom of the menu, skill names in Under the Hood) was just under the readability bar. It is now a little darker and passes on every page.
- ✅ Checked on a phone-sized screen (390 wide): no page scrolls sideways, including the landing page.
- ✅ Both fonts load on every page, and no page shows an error.
- ✅ Hover states exist for menu links, buttons, table rows, region buttons, Deep dive and the Ask button.
- ✅ The design check passes for all 7 pages.

## Still looks a bit off
- ⚠️ When the chat panel is open, both "Early Leads" and "Chat" show as selected in the left menu. This was already how it worked; the redesign didn't change it.
- ⚠️ On the Map, the state labels ("TX · 628 leads") sit right on dark blue states. They have a white outline so they can be read, but they are a bit busy up close.
- ⚠️ Under the Hood still shows the text "propertystack/runs/*.json". That is existing wording, and this build was not allowed to change wording.
- ⚠️ The full site test (`sweep.py`) takes far too long on this computer: it clicks every one of hundreds of Deep dive buttons and reloads after each one. A shortened run only found one issue: clicking the state button that's already selected (Texas) does nothing. That is expected, not a design problem.

## What Drew should check himself
- ⬜ **The chat app on its own:** open it after restarting the local dev setup (`bash tooling/dev.sh`) so it picks up the new style and fonts. On the local setup the "light by default" setting only applies to the real online build.
- ⬜ **The landing page file** isn't saved in git (that folder is excluded), so the font change there only exists on this computer.
- ⬜ Click through every tab and the Ask button on your phone.

## Screenshots
- Final desktop screenshots of every page, the chat panel and the landing page are in `docs/design-screens/final/`.
