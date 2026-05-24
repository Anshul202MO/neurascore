import os
import google.generativeai as genai
from data_models import ContentInput, ContentType

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

VIDEO_PROMPT = """You are an expert advertising analyst and neuromarketing specialist.
Analyse this ad video across the following dimensions.
Be specific, concrete and actionable — reference actual moments with timestamps where possible.

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
"""

def analyze_youtube_video(youtube_url: str, label: str = "Ad Video") -> tuple:
    prompt_with_url = f"""You are analysing this YouTube ad video: {youtube_url}

{VIDEO_PROMPT}

Important: If you cannot directly access the video, analyse based on any
knowledge you have of this video. State clearly what you can and cannot determine.
Structure your response using the exact headings above regardless."""

    response = model.generate_content(prompt_with_url)
    analysis_text = response.text.strip()
    content_input = ContentInput(
        text=analysis_text,
        content_type=ContentType.TEXT,
        label=label,
        content_id=f"video_{hash(youtube_url) % 100000}"
    )
    return content_input, analysis_text


def analyze_video_file(video_bytes: bytes, mime_type: str = "video/mp4", label: str = "Ad Video") -> tuple:
    video_part = {
        "inline_data": {
            "mime_type": mime_type,
            "data": video_bytes
        }
    }
    response = model.generate_content([VIDEO_PROMPT, video_part])
    analysis_text = response.text.strip()
    content_input = ContentInput(
        text=analysis_text,
        content_type=ContentType.TEXT,
        label=label,
        content_id=f"video_file_{hash(video_bytes[:100]) % 100000}"
    )
    return content_input, analysis_text
