from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import base64

from data_models import ContentInput, ContentType
from scoring_engine import score
from tribe_model import predict
from comparison_engine import compare
from meta_scorer import run_meta_audit
from groq_analyzer import run_quick_critique, run_deep_analysis
from image_analyzer import analyze_image, analyze_image_from_url
from video_analyzer import analyze_youtube_video, analyze_video_file

app = FastAPI(title="NeuraScore API", version="2.2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# REQUEST / RESPONSE MODELS
# ─────────────────────────────────────────────

class TextRequest(BaseModel):
    text: str
    label: Optional[str] = "Ad Copy"

class CompareRequest(BaseModel):
    text_a: str
    text_b: str
    label_a: Optional[str] = "Version A"
    label_b: Optional[str] = "Version B"

class MetaAuditRequest(BaseModel):
    text: str
    label: Optional[str] = "Ad Copy"

class ImageRequest(BaseModel):
    # Either base64 image data OR a public URL — not both
    image_base64: Optional[str] = None   # base64-encoded image bytes
    image_url: Optional[str] = None      # public image URL
    mime_type: Optional[str] = "image/jpeg"
    label: Optional[str] = "Ad Image"

class VideoRequest(BaseModel):
    # Either a YouTube URL OR base64 video bytes — not both
    youtube_url: Optional[str] = None    # YouTube video URL
    video_base64: Optional[str] = None   # base64-encoded video bytes for uploads
    mime_type: Optional[str] = "video/mp4"
    label: Optional[str] = "Ad Video"

# ─────────────────────────────────────────────
# EXISTING ENDPOINTS — UNCHANGED
# ─────────────────────────────────────────────

@app.get("/")
def health_check():
    return {
        "status": "NeuraScore API v2.2 live",
        "endpoints": ["/score", "/compare", "/meta-audit", "/quick-critique", 
                      "/deep-analysis", "/score-image", "/score-video"]
    }

@app.post("/score")
def score_content(req: TextRequest):
    try:
        content = ContentInput(
            text=req.text,
            content_type=ContentType.TEXT,
            label=req.label
        )
        brain_response = predict(content)
        scored = score(brain_response)
        audit = run_meta_audit(content)
        return {
            "label": req.label,
            "brain_scores": scored.__dict__,
            "meta_audit": audit.__dict__
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/compare")
def compare_content(req: CompareRequest):
    try:
        content_a = ContentInput(text=req.text_a, content_type=ContentType.TEXT, label=req.label_a)
        content_b = ContentInput(text=req.text_b, content_type=ContentType.TEXT, label=req.label_b)
        brain_a = predict(content_a)
        brain_b = predict(content_b)
        scored_a = score(brain_a)
        scored_b = score(brain_b)
        audit_a = run_meta_audit(content_a)
        audit_b = run_meta_audit(content_b)
        comparison = compare(scored_a, scored_b)
        return {
            "version_a": {"label": req.label_a, "brain_scores": scored_a.__dict__, "meta_audit": audit_a.__dict__},
            "version_b": {"label": req.label_b, "brain_scores": scored_b.__dict__, "meta_audit": audit_b.__dict__},
            "comparison": comparison.__dict__
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/meta-audit")
def meta_audit(req: MetaAuditRequest):
    try:
        content = ContentInput(text=req.text, content_type=ContentType.TEXT, label=req.label)
        audit = run_meta_audit(content)
        return {"label": req.label, "meta_audit": audit.__dict__}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/quick-critique")
def quick_critique(req: TextRequest):
    try:
        content = ContentInput(text=req.text, content_type=ContentType.TEXT, label=req.label)
        critique = run_quick_critique(content)
        return {"label": req.label, "critique": critique}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/deep-analysis")
def deep_analysis(req: TextRequest):
    try:
        content = ContentInput(text=req.text, content_type=ContentType.TEXT, label=req.label)
        analysis = run_deep_analysis(content)
        return {"label": req.label, "analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─────────────────────────────────────────────
# NEW ENDPOINT: IMAGE SCORING
# ─────────────────────────────────────────────

@app.post("/score-image")
def score_image(req: ImageRequest):
    """
    Accepts either a base64-encoded image or a public image URL.
    Gemini Flash analyses the visual content, then the existing
    brain scoring + Meta audit pipeline runs on that analysis.
    Returns identical response shape to /score.
    """
    try:
        if req.image_base64:
            # Decode base64 bytes sent from frontend
            image_bytes = base64.b64decode(req.image_base64)
            content_input, gemini_analysis = analyze_image(
                image_bytes, req.mime_type, req.label
            )
        elif req.image_url:
            content_input, gemini_analysis = analyze_image_from_url(
                req.image_url, req.label
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Provide either image_base64 or image_url"
            )

        # Run through existing pipeline — zero changes needed downstream
        brain_response = predict(content_input)
        scored = score(brain_response)
        audit = run_meta_audit(content_input)

        return {
            "label": req.label,
            "content_type": "image",
            # Include Gemini's raw analysis so frontend can show it
            # This tells the user WHAT Gemini saw — transparent and useful
            "gemini_analysis": gemini_analysis,
            "brain_scores": scored.__dict__,
            "meta_audit": audit.__dict__
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─────────────────────────────────────────────
# NEW ENDPOINT: VIDEO SCORING
# ─────────────────────────────────────────────

@app.post("/score-video")
def score_video(req: VideoRequest):
    """
    Accepts either a YouTube URL or a base64-encoded video file.
    Gemini Flash analyses visuals + audio in one call (no separate
    transcription service needed). Same pipeline as /score downstream.
    Returns identical response shape to /score.
    """
    try:
        if req.youtube_url:
            content_input, gemini_analysis = analyze_youtube_video(
                req.youtube_url, req.label
            )
        elif req.video_base64:
            video_bytes = base64.b64decode(req.video_base64)
            content_input, gemini_analysis = analyze_video_file(
                video_bytes, req.mime_type, req.label
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Provide either youtube_url or video_base64"
            )

        # Run through existing pipeline — zero changes needed downstream
        brain_response = predict(content_input)
        scored = score(brain_response)
        audit = run_meta_audit(content_input)

        return {
            "label": req.label,
            "content_type": "video",
            # Gemini's full analysis — hook timing, transcript, pacing etc.
            # Frontend should display this as "What our AI saw" section
            "gemini_analysis": gemini_analysis,
            "brain_scores": scored.__dict__,
            "meta_audit": audit.__dict__
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
