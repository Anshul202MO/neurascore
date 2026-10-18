import os
import re
import google.generativeai as genai
from data_models import ContentInput, ContentType

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

# ─────────────────────────────────────────────
# PROMPT
# Two clearly separated parts:
#   AD CONTENT  -> only what is in the ad (this is what gets SCORED)
#   ANALYSIS    -> the critique (this is what gets DISPLAYED)
# No "You are an expert..." role line, so Gemini has nothing to echo.
# ─────────────────────────────────────────────

VIDEO_PROMPT = """Watch this ad video and write your response in exactly two parts,
using the two marker lines shown below, each on its own line.

===AD CONTENT===
Describe ONLY what is actually in the ad, in chronological order, as plain sentences.
- Begin with exactly what the viewer sees and hears in the first 2 seconds.
- Put every spoken word (voiceover, dialogue, lyrics) and every piece of on-screen
  text in double quotes, word for word, at the point where it occurs.
- Name the brand or product only when it is actually shown or said.
- Do NOT give opinions, ratings or advice. Do NOT use marketing terms such as
  hook, CTA, call-to-action, branding, engagement, storytelling or neuromarketing.
- Do NOT describe yourself or your role. No headings, labels, timestamps or bullets.

===ANALYSIS===
Analyse the ad under these headings. Be specific, concrete and actionable, and
reference actual moments with timestamps where possible.

HOOK (0-5 seconds): What happens in the first 5 seconds? Is there an immediate
visual or audio hook? Would someone stop scrolling?

STORY ARC: How does the narrative unfold? Is it frontloaded or slow-build?

BRANDING: When does the brand first appear? How many times? Is it integrated or forced?

AUDIO: Describe the voiceover tone, music, sound effects. Would this work on mute?

EMOTION: What is the dominant emotional arc? Humour, aspiration, fear, warmth?

PACING: Fast-cut or slow? How many scene changes approximately?

CTA: What is the call-to-action? When does it appear? Specific or vague?

SPOKEN TEXT: Transcribe any voiceover, dialogue or on-screen text word for word.

MOBILE CHECK: Would this work on a 5-inch screen? Is text legible?

WEAKNESSES: What are the 3 biggest creative weaknesses? Be direct and specific.

STRENGTHS: What are the 2 things this ad does genuinely well?

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
    "HOOK", "STORY ARC", "BRANDING", "AUDIO", "EMOTION", "PACING", "CTA",
    "SPOKEN TEXT", "MOBILE CHECK", "WEAKNESSES", "STRENGTHS",
]


def _clean(text: str) -> str:
    """Strip markdown symbols, bullets and any 'As an expert...' opener."""
    text = re.sub(r"[*#_`]+", "", text)
    text = re.sub(r"^\s*[-•]\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s+", " ", text).strip()
    # Remove persona openers even if Gemini adds one anyway (repeat in case of two)
    for _ in range(2):
        text = _PERSONA_RE.sub("", text, count=1).strip()
    return text


def _extract_section(text: str, heading: str) -> str:
    """Pull one heading's body (e.g. SPOKEN TEXT) out of the analysis."""
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
      2. SPOKEN TEXT section of the analysis
      3. Whole reply with any persona opener removed
    """
    parts = _MARKER_RE.split(raw)
    sections = {}
    # parts = [before, NAME, body, NAME, body, ...]
    for i in range(1, len(parts) - 1, 2):
        sections[parts[i].strip().upper()] = parts[i + 1].strip()

    ad_content = _clean(sections.get("AD CONTENT", ""))
    analysis = sections.get("ANALYSIS", "").strip() or raw.strip()

    if len(ad_content) < 20:
        ad_content = _clean(_extract_section(analysis, "SPOKEN TEXT"))
    if len(ad_content) < 20:
        ad_content = _clean(raw)

    return ad_content, analysis


# ─────────────────────────────────────────────
# PUBLIC FUNCTIONS (same names and return shape as before,
# so app.py does not need to change)
# ─────────────────────────────────────────────

def analyze_youtube_video(youtube_url: str, label: str = "Ad Video") -> tuple:
    """
    Kept only so app.py's import still works.
    Gemini cannot fetch YouTube URLs via the API — file upload is the reliable path.
    """
    prompt_with_url = f"""The ad video is at this YouTube link: {youtube_url}

{VIDEO_PROMPT}

If you cannot access the video, say so plainly in the ANALYSIS part and keep the
AD CONTENT part to only what you can actually confirm."""

    response = model.generate_content(prompt_with_url)
    ad_content, analysis_text = _split_response(response.text.strip())

    content_input = ContentInput(
        text=ad_content,
        content_type=ContentType.TEXT,
        label=label,
        content_id=f"video_{hash(youtube_url) % 100000}"
    )
    return content_input, analysis_text


def analyze_video_file(video_bytes: bytes, mime_type: str = "video/mp4", label: str = "Ad Video") -> tuple:
    """
    Accepts raw video file bytes uploaded directly by the user.
    Only the AD CONTENT (what is actually in the ad) is passed on for scoring.
    The ANALYSIS is returned separately for display.
    """
    video_part = {
        "inline_data": {
            "mime_type": mime_type,
            "data": video_bytes
        }
    }

    response = model.generate_content([VIDEO_PROMPT, video_part])
    ad_content, analysis_text = _split_response(response.text.strip())

    content_input = ContentInput(
        text=ad_content,
        content_type=ContentType.TEXT,
        label=label,
        content_id=f"video_file_{hash(video_bytes[:100]) % 100000}"
    )
    return content_input, analysis_text
