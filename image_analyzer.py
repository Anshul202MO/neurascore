import os
import re
import google.generativeai as genai
from data_models import ContentInput, ContentType

# Initialize Gemini client
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

# ─────────────────────────────────────────────
# PROMPT
# Two clearly separated parts:
#   AD CONTENT  -> only what is in the ad (this is what gets SCORED)
#   ANALYSIS    -> the critique (this is what gets DISPLAYED)
# No "You are an expert..." role line, so Gemini has nothing to echo.
# ─────────────────────────────────────────────

IMAGE_PROMPT = """Look at this ad image and write your response in exactly two parts,
using the two marker lines shown below, each on its own line.

===AD CONTENT===
Describe ONLY what is actually in the image, as plain sentences.
- Begin with the largest or most prominent text, in double quotes, exactly as written.
- Then give every other piece of visible text in double quotes, word for word,
  in normal reading order (top to bottom, left to right).
- Then plainly describe what is shown: people, product, setting, colours, logo.
- Name the brand or product only when it is actually visible.
- Do NOT give opinions, ratings or advice. Do NOT use marketing terms such as
  hook, CTA, call-to-action, branding, engagement, storytelling or neuromarketing.
- Do NOT describe yourself or your role. No headings, labels or bullets.

===ANALYSIS===
Analyse the ad under these headings. Be specific, concrete and actionable.

HOOK: What is the single most attention-grabbing visual element in this image?
What draws the eye first and why?

PRODUCT: What product or brand is shown? How prominently? Is it shown in use
or just displayed? Is the product the hero or supporting element?

EMOTION: What is the dominant emotional tone? What specific visual choices
(colour, expression, composition, lighting) create that emotion?

TEXT & CTA: List every piece of text visible in the image. What is the
call-to-action? Is it clear and urgent or vague?

VISUAL FOCUS: Is the composition clean or cluttered? What is the focal point?
Would this work on a 5-inch mobile screen or does it require a large display?

BRANDING: Where does the brand appear? Is it integrated naturally or stuck on
as an afterthought? Is it visible without effort?

STORY: What story or message does this image tell in a single glance?
What would someone understand in under 2 seconds?

WEAKNESSES: What are the 2-3 biggest creative weaknesses in this image
from an advertising effectiveness standpoint?

Start your response directly with the line ===AD CONTENT===
"""

# ─────────────────────────────────────────────
# HELPERS — split Gemini's reply into "ad content" and "analysis"
# ─────────────────────────────────────────────

_MARKER_RE = re.compile(
    r"^[\s#*=_>-]*(AD CONTENT|ANALYSIS)[\s#*=_:-]*$",
    re.IGNORECASE | re.MULTILINE,
)

_PERSONA_RE = re.compile(
    r"^\s*(as an?|i am an?|i'm an?)\b[^.\n]*?"
    r"(analyst|specialist|expert|marketer|strategist)s?\b[^.,:\n]*[.,:]\s*",
    re.IGNORECASE,
)

_SECTION_HEADINGS = [
    "HOOK", "PRODUCT", "EMOTION", "TEXT & CTA", "VISUAL FOCUS",
    "BRANDING", "STORY", "WEAKNESSES",
]


def _clean(text: str) -> str:
    """Strip markdown symbols, bullets and any 'As an expert...' opener."""
    text = re.sub(r"[*#_`]+", "", text)
    text = re.sub(r"^\s*[-•]\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s+", " ", text).strip()
    for _ in range(2):
        text = _PERSONA_RE.sub("", text, count=1).strip()
    return text


def _extract_section(text: str, heading: str) -> str:
    """Pull one heading's body (e.g. TEXT & CTA) out of the analysis."""
    others = "|".join(re.escape(h) for h in _SECTION_HEADINGS if h != heading)
    pattern = (
        r"[#*\s]*" + re.escape(heading) + r"[^:\n]*:[*\s]*(.*?)"
        r"(?=\n[#*\s]*(?:" + others + r")\b[^:\n]*:|\Z)"
    )
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _split_response(raw: str) -> tuple:
    """
    Returns (ad_content_for_scoring, analysis_for_display).
    Fallback order if Gemini ignores the format:
      1. AD CONTENT block
      2. TEXT & CTA section of the analysis
      3. Whole reply with any persona opener removed
    """
    parts = _MARKER_RE.split(raw)
    sections = {}
    for i in range(1, len(parts) - 1, 2):
        sections[parts[i].strip().upper()] = parts[i + 1].strip()

    ad_content = _clean(sections.get("AD CONTENT", ""))
    analysis = sections.get("ANALYSIS", "").strip() or raw.strip()

    if len(ad_content) < 20:
        ad_content = _clean(_extract_section(analysis, "TEXT & CTA"))
    if len(ad_content) < 20:
        ad_content = _clean(raw)

    return ad_content, analysis


# ─────────────────────────────────────────────
# PUBLIC FUNCTIONS (same names and return shape as before,
# so app.py does not need to change)
# ─────────────────────────────────────────────

def analyze_image(image_bytes: bytes, mime_type: str = "image/jpeg", label: str = "Ad Image") -> tuple:
    """
    Sends the image to Gemini. Only the AD CONTENT (what is actually in the ad)
    is passed on for scoring. The ANALYSIS is returned separately for display.
    """
    image_part = {
        "mime_type": mime_type,
        "data": image_bytes
    }

    response = model.generate_content([IMAGE_PROMPT, image_part])
    ad_content, analysis_text = _split_response(response.text.strip())

    content_input = ContentInput(
        text=ad_content,
        content_type=ContentType.TEXT,
        label=label,
        content_id=f"image_{hash(image_bytes) % 100000}"
    )

    return content_input, analysis_text


def analyze_image_from_url(image_url: str, label: str = "Ad Image") -> tuple:
    """
    Accepts a public image URL instead of bytes.
    """
    import httpx

    response = httpx.get(image_url, timeout=15)
    response.raise_for_status()

    content_type_header = response.headers.get("content-type", "image/jpeg")
    mime_type = content_type_header.split(";")[0].strip()

    return analyze_image(response.content, mime_type, label)
