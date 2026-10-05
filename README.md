# KDPEasy Listing Mockup Maker

Bonus tool for the **Crossword Puzzle Creator public launch** (bonus #3).
Streamlit, two steps, pure text templating - no image generation and no API call
inside the tool. Same model as Storybook Prompt Kit and Clipart & Mockup Kit.

## What it does

1. **Step 1 - Scene ideas.** The customer says what the photos are of (for example
   "a large-print crossword puzzle book for seniors, paperback"), picks a number of
   scenes (3-12) and a style (Flatlay / Lifestyle / Clean studio). The tool builds one
   prompt to paste into ChatGPT, which answers with a numbered list of scenes.
2. **Step 2 - Image prompts.** The customer pastes that reply back. Every scene becomes
   its own ready-to-run image prompt, all locked to the same style. In ChatGPT they
   upload their cover (or one inside page) and paste the prompts, one per image.

Each step has a .txt and a PDF download.

## How it differs from Clipart & Mockup Kit

This is a COPY of the "Listing mockup scenes" mode only. Clipart & Mockup Kit stays as it
is - it is the tool anh gives to his list as free gifts, with 9 modes.

Removed here on purpose: the other 8 modes (clipart, digital paper, stickers, classroom
decor, Pinterest pins, coloring pages, planner pages, mascot), the "Sell as a product /
promo bonus" toggle, "Not sure which type to use?" (+ the explain prompt), and Step 3
"Collection cover" (it makes one image of a whole set - that makes no sense for mockup
scenes).

Changed on purpose (labels only):
- The field says "What are you showing in the photos?" with a crossword example.
- Step 1 prompt says `PRODUCT:` where the original said `PRODUCT OR THEME:`.
- The upload line of every Step 2 prompt says "(for a book: your cover image, or a
  picture of an inside page)".
Everything else in both prompts is word-for-word the same as the original
(checked by script).

## Password

`KDPMOCKUP2026` - its own password, NOT the Clipart & Mockup Kit's
(`KDPCLIPART2026`), so list gifts and launch buyers never mix. Change the string in
`PASSWORDS` in `app.py` if you want a different one. Put it on the Crossword launch
thank-you page, next to the app link.

## Deploy (GitHub web editor + Streamlit Cloud, no Git CLI)

1. Create a new GitHub repo, e.g. `kdpeasy-mockup-maker`.
2. "Add file" -> "Upload files": upload `app.py`, `requirements.txt` and the
   `.streamlit/config.toml` file (keep the `.streamlit` folder name).
3. On Streamlit Community Cloud: New app -> that repo -> main file `app.py`.
4. Open the app, log in with the password, run one real example before sharing.

## Known limitation to tell buyers

ChatGPT's image tool does not always keep an uploaded image perfectly untouched - on a
book cover the title lettering is the first thing to check. The "How this works" box says so.
Not yet tried with a real crossword cover in ChatGPT: do one real run before launch.
