import io
import re
from datetime import date
from xml.sax.saxutils import escape

import streamlit as st
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

st.set_page_config(page_title="KDPEasy Listing Mockup Maker", page_icon="\U0001F4F7", layout="centered")

# ----------------------------------------------------------------------------
# Access. One tier. This is the mockup-only sibling of Clipart & Mockup Kit,
# made as a bonus for the Crossword Puzzle Creator public launch - it has its
# OWN password, separate from the Clipart & Mockup Kit's, so the list gift and
# the launch bonus never mix. "expires": None = permanent, or a datetime.date
# for a trial password.
# ----------------------------------------------------------------------------
PASSWORDS = {
    "KDPMOCKUP2026": {"expires": None},
}

CUSTOM_CSS = """
<style>
:root { color-scheme: light; }
.stApp { background: linear-gradient(160deg, #16302a 0%, #1f4a3e 55%, #275c4c 100%); }
.block-container, [data-testid="stMainBlockContainer"] {
    background: #fdfdfb;
    border-radius: 18px;
    padding-left: 3rem; padding-right: 3rem;
    margin-top: 1.5rem; margin-bottom: 3rem;
    box-shadow: 0 14px 44px rgba(10, 30, 24, 0.38);
}
h1, h2, h3 { color: #16302a; }
h1 { border-bottom: 3px solid #2f7d6b; padding-bottom: 0.3rem; }
a, a:visited { color: #1f4a3e; }
.stButton>button, .stDownloadButton>button {
    background-color: #2f7d6b; color: #ffffff; border-radius: 10px; border: none;
    padding: 0.6rem 1.4rem; font-weight: 600;
}
.stButton>button:hover, .stDownloadButton>button:hover { background-color: #1f4a3e; color: #ffffff; }
.kdp-card { display: none; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def check_password() -> bool:
    if st.session_state.get("authed"):
        return True
    st.markdown('<div class="kdp-card">', unsafe_allow_html=True)
    st.title("\U0001F4F7 KDPEasy Listing Mockup Maker")
    pw = st.text_input("Enter access password", type="password")
    if st.button("Unlock"):
        tier = PASSWORDS.get(pw)
        if tier is None:
            st.error("Incorrect password.")
        elif tier["expires"] is not None and date.today() > tier["expires"]:
            st.error("This trial password has expired. Please reach out to get full access.")
        else:
            st.session_state["authed"] = True
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    return False


# Streamlit reruns the whole script on every click, including download
# buttons - without this, a built prompt list disappears the moment someone
# clicks "Download". Stash keyed by the inputs that produced it; it keeps
# showing until an input actually changes.
def _stash(key, sig, value):
    st.session_state[key] = (sig, value)


def _recall(key, sig):
    got = st.session_state.get(key)
    return got[1] if got and got[0] == sig else None


# ----------------------------------------------------------------------------
# All text that ends up in a customer-facing prompt is plain ASCII on purpose -
# it gets pasted into ChatGPT, so no smart quotes / em dashes.
#
# The customer always has a finished cover already, so the tool asks for only
# two things: how many scenes and which style. The cover itself is uploaded in
# ChatGPT, never here.
# ----------------------------------------------------------------------------

MIXED = "Mixed variety"

# name -> description used in the Step 2 prompts ("STYLE: ...") and, for a single
# style, in the Step 1 prompt. Every look keeps the FRONT COVER facing the camera.
MOCKUP_STYLES = {
    MIXED: "natural, realistic product photography; the scene description decides the setting, "
           "the colors and the light",
    "Flatlay": "a bright flatlay scene shot from directly above, the book lying flat with its cover "
               "facing up, soft natural light, a few simple props",
    "Clean studio": "a clean studio product shot, the book standing upright against a plain seamless "
                    "background, soft even lighting, no extra props",
    "Lifestyle": "a lifestyle scene with the book in natural use, soft daylight, an uncluttered background",
    "Cozy reading nook": "a cozy reading nook with an armchair or window seat, a soft blanket, a warm "
                         "cup and warm lamp light",
    "Desk & workspace": "a tidy desk with a notebook, pens and a coffee cup, natural light from a window",
    "Bookshelf & stack": "a bookshelf or a neat stack of books, with this book's front cover turned "
                         "toward the camera",
    "Hands holding": "a close-up of a person's hands holding the book at its edges so the whole front "
                     "cover stays visible, a softly blurred background",
    "Outdoor & garden": "an outdoor scene such as a garden table, a picnic blanket or a park bench, "
                        "with dappled sunlight",
    "Kids' room": "a bright, tidy child's room or playroom with colorful toys and soft pastel colors",
    "Gift & holiday": "a gift-style scene with the book beside ribbon, wrapping paper and a small bow, "
                      "in warm festive colors",
    "Travel & road trip": "a travel scene with the book on a car seat, a train table or a suitcase, "
                          "beside a map or a pair of sunglasses",
    "Bold color pop": "a bold single-color background in a bright color that matches the cover, simple "
                      "soft shadows, a graphic and modern look",
    "Seasonal": "a seasonal scene - autumn leaves, snow, spring flowers or summer sun - chosen to match "
                "the book's theme",
}

COUNT_MIN, COUNT_MAX, COUNT_DEFAULT = 3, 12, 6
MARKER = "SCENE"


def build_shotlist_prompt(count: int, style_name: str, style_desc: str) -> str:
    if style_name == MIXED:
        style_line = ("Make the scenes look clearly different from each other: vary the setting, the "
                      "colors and the light from one scene to the next.\n")
        closing = "Keep descriptions concrete and visual. Avoid near-duplicate scenes."
    else:
        style_line = f"Style for reference (do not repeat this in the list): {style_desc}.\n"
        closing = ("Keep descriptions concrete and visual. No mood, lighting, or rendering language. "
                   "Avoid near-duplicate scenes.")
    return (
        f"You are helping me plan mockup photos for a paperback book. I already have the cover image "
        f"and will add it later, so do not describe the cover.\n\n"
        f"Give me a shot list of {count} different mockup scenes. Each scene should show the book in a "
        f"different setting or from a different angle, not a repeat of the same idea. In every scene "
        f"the front cover must face the camera and stay fully visible.\n\n"
        f"Output format, exactly like this for every item:\n"
        f"=== {MARKER} 01 ===\n"
        f"NAME: short name\n"
        f"DESCRIPTION: one plain sentence describing the setting, props, and camera angle (do not "
        f"describe the book's cover or title)\n"
        f"=== {MARKER} 02 ===\n"
        f"...continue through {MARKER} {count:02d}\n\n"
        f"{style_line}"
        f"{closing}"
    )


def parse_items(raw: str):
    blocks = re.split(rf'=+\s*{MARKER}\s*\d+\s*=+', raw, flags=re.IGNORECASE)
    items = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        name_m = re.search(r'NAME\s*:\s*(.+)', block, re.IGNORECASE)
        desc_m = re.search(r'DESCRIPTION\s*:\s*(.+)', block, re.IGNORECASE)
        if name_m:
            name = name_m.group(1).strip()
            desc = desc_m.group(1).strip().split('\n')[0].strip() if desc_m else ""
            items.append((name, desc))
    return items


def build_item_prompt(name: str, desc: str, style_desc: str) -> str:
    return (
        f"Use the book cover image I uploaded in this chat as a fixed reference. Do not redraw, "
        f"retype, crop or alter anything on it.\n\n"
        f"SCENE: {name} - {desc}\n"
        f"STYLE: {style_desc}.\n\n"
        f"Show a real paperback book with that exact cover as its front cover, facing the camera, in "
        f"this scene, as if photographed for a product listing. Keep the cover artwork and every "
        f"letter of the title exactly as uploaded, and keep the cover's proportions - do not stretch "
        f"it. Only add the book's edges, spine and pages and the scene around it."
    )


BEFORE_YOU_PASTE = ("Before you paste these into ChatGPT: open a new chat and upload your FRONT cover "
                    "image first. Then paste one prompt at a time, in that same chat.")


# ----------------------------------------------------------------------------
# PDF export. Bundles whatever has been built so far into one file, so the
# prompts can be saved or printed without keeping the tool open.
# ----------------------------------------------------------------------------
def _pdf_block(text: str, style):
    """Paragraph wraps long lines (Preformatted does not), which matters since
    some prompt lines run well past a page's width."""
    html = escape(text).replace("\n", "<br/>")
    return Paragraph(html, style)


def build_pdf_bytes(pack_title: str, shotlist_prompt, item_prompts) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=LETTER,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()
    code_style = styles["Code"]
    code_style.fontSize = 8.5
    code_style.leading = 11

    story = [
        Paragraph(escape(pack_title or "Listing Mockup Prompt Pack"), styles["Title"]),
        Paragraph("Book cover mockup scenes", styles["Normal"]),
        Spacer(1, 0.3 * inch),
    ]

    if shotlist_prompt:
        story.append(Paragraph("Paste this into ChatGPT first", styles["Heading2"]))
        story.append(_pdf_block(shotlist_prompt, code_style))
        story.append(Spacer(1, 0.3 * inch))

    if item_prompts:
        story.append(Paragraph(
            "Run each prompt below in ChatGPT, in the same chat so everything matches",
            styles["Heading2"],
        ))
        story.append(Paragraph(escape(BEFORE_YOU_PASTE), styles["Normal"]))
        story.append(Spacer(1, 0.2 * inch))
        for i, (name, prompt) in enumerate(item_prompts):
            story.append(Paragraph(f"{i + 1}. {escape(name)}", styles["Heading3"]))
            story.append(_pdf_block(prompt, code_style))
            story.append(Spacer(1, 0.15 * inch))

    story.append(Spacer(1, 0.4 * inch))
    story.append(Paragraph("KDPEasy Studio - kdpeasy.studio", styles["Normal"]))

    doc.build(story)
    return buf.getvalue()


# ----------------------------------------------------------------------------
# UI
# ----------------------------------------------------------------------------
if not check_password():
    st.stop()

st.title("\U0001F4F7 KDPEasy Listing Mockup Maker")
st.caption(
    "Turn your finished book cover into listing photos. Pick how many scenes and a style, get a "
    "prompt for ChatGPT. Paste its reply back, get one ready-to-run image prompt per scene. Then "
    "upload your cover in ChatGPT and run the prompts."
)

with st.expander("How this works"):
    st.markdown(
        "1. **Step 1** - choose how many scenes and a style, then build the prompt. Paste it into "
        "ChatGPT (no image needed yet). It replies with a numbered list of scene ideas.\n"
        "2. **Step 2** - paste that reply here. Every scene becomes its own image prompt, all in the "
        "style you picked.\n"
        "3. In ChatGPT (the version that makes images), open a **new chat** and upload your front "
        "cover image first. Then paste one Step 2 prompt at a time, in that same chat, so the photos "
        "match.\n\n"
        "**Upload the front cover only** - a flat picture (JPG or PNG) of the front, not the full "
        "wrap-around file with the back and spine.\n\n"
        "**Can't decide on a style?** \"Mixed variety\" gives you a different look in every scene, "
        "which is handy for a set of listing photos.\n\n"
        "**Check every result.** ChatGPT does not always keep your cover perfectly untouched - look "
        "closely at the title lettering, and ask it to try again if a letter changed.\n\n"
        "This tool only writes text. It does not upload your images or call any AI itself."
    )

tab1, tab2 = st.tabs(["Step 1 - Scene ideas", "Step 2 - Image prompts"])

with tab1:
    count = st.number_input("Number of mockup scenes", min_value=COUNT_MIN, max_value=COUNT_MAX,
                            value=COUNT_DEFAULT)
    style_name = st.selectbox("Style", list(MOCKUP_STYLES.keys()))
    style_desc = MOCKUP_STYLES[style_name]
    if style_name == MIXED:
        st.caption("Every scene gets its own look: a different setting, colors and light.")
    else:
        st.caption("Every scene keeps this one look, in a different spot or from a different angle.")

    sig1 = (int(count), style_name)
    if st.button("Build Step 1 prompt"):
        _stash("shotlist_prompt", sig1, build_shotlist_prompt(int(count), style_name, style_desc))

    out1 = _recall("shotlist_prompt", sig1)
    if out1:
        st.code(out1, language=None)
        dl1a, dl1b = st.columns(2)
        with dl1a:
            st.download_button("Download (.txt)", out1, file_name="step1_scene_ideas_prompt.txt")
        with dl1b:
            st.download_button(
                "Download (PDF)",
                build_pdf_bytes("Listing Mockups - Scene Ideas Prompt", out1, []),
                file_name="step1_scene_ideas_prompt.pdf", mime="application/pdf",
            )
    else:
        st.caption("Changed something above? Click \"Build Step 1 prompt\" again.")

with tab2:
    shotlist = st.text_area(
        "Paste ChatGPT's reply here",
        height=220,
        placeholder="=== %s 01 ===\nNAME: ...\nDESCRIPTION: ...\n=== %s 02 ===\n..." % (MARKER, MARKER),
    )

    sig2 = (shotlist, style_name)
    if st.button("Build Step 2 prompts"):
        items = parse_items(shotlist)
        if not items:
            st.warning(
                "Could not find any scenes. Make sure the pasted text still has the "
                f"'=== {MARKER} 0X ===' lines with NAME: and DESCRIPTION: under each."
            )
        else:
            prompts = [build_item_prompt(n, d, style_desc) for n, d in items]
            _stash("item_prompts", sig2, list(zip([n for n, d in items], prompts)))

    built = _recall("item_prompts", sig2)
    if built:
        st.success(f"Built {len(built)} prompt(s).")
        st.info(BEFORE_YOU_PASTE)
        all_text = "\n\n---\n\n".join(f"{i+1}. {name}\n\n{p}" for i, (name, p) in enumerate(built))
        dl2a, dl2b = st.columns(2)
        with dl2a:
            st.download_button("Download all (.txt)", all_text, file_name="step2_image_prompts.txt")
        with dl2b:
            st.download_button(
                "Download all (PDF)",
                build_pdf_bytes("Listing Mockups - Image Prompts", "", built),
                file_name="step2_image_prompts.pdf", mime="application/pdf",
            )
        for i, (name, p) in enumerate(built):
            st.markdown(f"**{i+1}. {name}**")
            st.code(p, language=None)
    else:
        st.caption("Paste ChatGPT's reply above, then click \"Build Step 2 prompts\".")

st.divider()
st.caption("KDPEasy Studio - kdpeasy.studio")
