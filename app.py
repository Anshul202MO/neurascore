from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
sys.path.insert(0, "/app")

from data_models import ContentInput, ContentType
from scoring_engine import score
from tribe_model import predict
from comparison_engine import compare
from meta_scorer import run_meta_audit
from groq_analyzer import run_quick_critique, run_deep_analysis

app = FastAPI(title="NeuraScore API", version="2.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScoreRequest(BaseModel):
    text: str
    content_type: Optional[str] = "ad_copy"

class CompareRequest(BaseModel):
    text_a: str
    text_b: str
    content_type: Optional[str] = "ad_copy"

class AuditRequest(BaseModel):
    text: str
    content_type: Optional[str] = "ad_copy"

class QuickCritiqueRequest(BaseModel):
    text: str
    content_type: Optional[str] = "ad_copy"

class DeepAnalysisRequest(BaseModel):
    text: str
    content_type: Optional[str] = "ad_copy"


@app.get("/")
def health():
    return {
        "status": "NeuraScore API v2.1 is live",
        "endpoints": ["/score", "/compare", "/meta-audit", "/quick-critique", "/deep-analysis"]
    }


@app.post("/score")
def score_endpoint(req: ScoreRequest):
    content = ContentInput(text=req.text, content_type=ContentType.TEXT)
    brain_response = predict(content)
    result = score(brain_response)
    audit = run_meta_audit(content)
    return {
        "brain_scores": {
            "overall_score": result.overall_score,
            "hook_strength": result.hook_strength,
            "attention": result.attention,
            "emotion": result.emotion,
            "memory": result.memory,
            "visual_engagement": result.visual_engagement,
            "language_clarity": result.language_clarity,
            "desire": result.desire,
        },
        "meta_audit": {
            "overall_score": audit.overall_score,
            "verdict": audit.verdict,
            "category_scores": audit.category_scores,
            "checks": [
                {
                    "id": c.id,
                    "category": c.category,
                    "name": c.name,
                    "status": c.status,
                    "score": c.score,
                    "feedback": c.feedback
                } for c in audit.checks
            ]
        }
    }


@app.post("/compare")
def compare_endpoint(req: CompareRequest):
    content_a = ContentInput(text=req.text_a, content_type=ContentType.TEXT, label="Version A")
    content_b = ContentInput(text=req.text_b, content_type=ContentType.TEXT, label="Version B")
    result_a = score(predict(content_a))
    result_b = score(predict(content_b))
    comparison = compare(result_a, result_b)
    audit_a = run_meta_audit(content_a)
    audit_b = run_meta_audit(content_b)
    return {
        "comparison": {
            "overall_winner": comparison.overall_winner,
            "overall_delta": comparison.overall_delta,
            "overall_summary": comparison.overall_summary,
            "score_a": result_a.overall_score,
            "score_b": result_b.overall_score,
            "attention_winner": comparison.attention_winner,
            "emotion_winner": comparison.emotion_winner,
            "memory_winner": comparison.memory_winner,
            "visual_engagement_winner": comparison.visual_engagement_winner,
            "language_clarity_winner": comparison.language_clarity_winner,
            "desire_winner": comparison.desire_winner,
        },
        "meta_audit_a": {
            "overall_score": audit_a.overall_score,
            "category_scores": audit_a.category_scores,
            "checks": [{"id": c.id, "category": c.category, "name": c.name, "status": c.status, "score": c.score, "feedback": c.feedback} for c in audit_a.checks]
        },
        "meta_audit_b": {
            "overall_score": audit_b.overall_score,
            "category_scores": audit_b.category_scores,
            "checks": [{"id": c.id, "category": c.category, "name": c.name, "status": c.status, "score": c.score, "feedback": c.feedback} for c in audit_b.checks]
        }
    }


@app.post("/meta-audit")
def meta_audit_endpoint(req: AuditRequest):
    content = ContentInput(text=req.text, content_type=ContentType.TEXT)
    audit = run_meta_audit(content)
    return {
        "overall_score": audit.overall_score,
        "verdict": audit.verdict,
        "category_scores": audit.category_scores,
        "checks": [
            {
                "id": c.id,
                "category": c.category,
                "name": c.name,
                "description": c.description,
                "status": c.status,
                "score": c.score,
                "feedback": c.feedback
            } for c in audit.checks
        ]
    }


@app.post("/quick-critique")
def quick_critique_endpoint(req: QuickCritiqueRequest):
    content = ContentInput(text=req.text, content_type=ContentType.TEXT)
    result = run_quick_critique(content)
    return result


@app.post("/deep-analysis")
def deep_analysis_endpoint(req: DeepAnalysisRequest):
    content = ContentInput(text=req.text, content_type=ContentType.TEXT)
    result = run_deep_analysis(content)
    return result
