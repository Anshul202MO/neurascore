from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import base64

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from data_models import ContentInput, ContentType
from scoring_engine import score
from tribe_model import predict
from comparison_engine import compare
from meta_scorer import run_meta_audit
from groq_analyzer import run_quick_critique, run_deep_analysis
from image_analyzer import analyze_image, analyze_image_from_url
from video_analyzer import analyze_youtube_video, analyze_video_file

# ─────────────────────────────────────────────
# RATE LIMITER SETUP
# ─────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

app = FastAPI(title="NeuraScore API", version="2.3")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
    image_base64: Optional[str] = None
    image_url: Optional[str] = None
    mime_type: Optional[str] = "image/jpeg"
    label: Optional[str] = "Ad Image"

class VideoRequest(BaseModel):
    youtube_url: Optional[str] = None
    video_base64: Optional[str] = None
    mime_type: Optional[str] = "video/mp4"
    label: Optional[str] = "Ad Video"

# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

@app.get("/")
def health_check():
    return {
        "status": "NeuraScore API v2.3 live",
        "endpoints": ["/score", "/compare", "/meta-audit", "/quick-critique",
                      "/deep-analysis", "/score-image", "/score-video"]
    }

@app.post("/score")
@limiter.limit("30/minute")
def score_content(req: TextRequest, request: Request):
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
@limiter.limit("20/minute")
def compare_content(req: CompareRequest, request: Request):
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
@limiter.limit("30/minute")
def meta_audit(req: MetaAuditRequest, request: Request):
    try:
        content = ContentInput(text=req.text, content_type=ContentType.TEXT, label=req.label)
        audit = run_meta_audit(content)
        return {"label": req.label, "meta_audit": audit.__dict__}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/quick-critique")
@limiter.limit("20/minute")
def quick_critique(req: TextRequest, request: Request):
    try:
        content = ContentInput(text=req.text, content_type=ContentType.TEXT, label=req.label)
        critique = run_quick_critique(content)
        return {"label": req.label, "critique": critique}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/deep-analysis")
@limiter.limit("10/minute")
def deep_analysis(req: TextRequest, request: Request):
    try:
        content = ContentInput(text=req.text, content_type=ContentType.TEXT, label=req.label)
        analysis = run_deep_analysis(content)
        return {"label": req.label, "analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/score-image")
@limiter.limit("20/minute")
def score_image(req: ImageRequest, request: Request):
    try:
        if req.image_base64:
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
        brain_response = predict(content_input)
        scored = score(brain_response)
        audit = run_meta_audit(content_input)
        return {
            "label": req.label,
            "content_type": "image",
            "gemini_analysis": gemini_analysis,
            "brain_scores": scored.__dict__,
            "meta_audit": audit.__dict__
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/score-video")
@limiter.limit("10/minute")
def score_video(req: VideoRequest, request: Request):
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
        brain_response = predict(content_input)
        scored = score(brain_response)
        audit = run_meta_audit(content_input)
        return {
            "label": req.label,
            "content_type": "video",
            "gemini_analysis": gemini_analysis,
            "brain_scores": scored.__dict__,
            "meta_audit": audit.__dict__
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
