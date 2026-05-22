from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
sys.path.insert(0, "/content/neurascore")

from data_models import ContentInput
from scoring_engine import score_content
from comparison_engine import compare_versions
from meta_scorer import run_meta_audit

app = FastAPI(title="NeuraScore API", version="2.0")

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

@app.get("/")
def health():
    return {"status": "NeuraScore API v2.0 is live", "endpoints": ["/score", "/compare", "/meta-audit"]}

@app.post("/score")
def score(req: ScoreRequest):
    content = ContentInput(text=req.text, content_type=req.content_type)
    result = score_content(content)
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
def compare(req: CompareRequest):
    content_a = ContentInput(text=req.text_a, content_type=req.content_type)
    content_b = ContentInput(text=req.text_b, content_type=req.content_type)
    result_a = score_content(content_a)
    result_b = score_content(content_b)
    comparison = compare_versions(result_a, result_b)
    audit_a = run_meta_audit(content_a)
    audit_b = run_meta_audit(content_b)
    return {
        "comparison": {
            "winner": comparison.winner,
            "verdict": comparison.verdict,
            "score_a": comparison.overall_score_a,
            "score_b": comparison.overall_score_b,
            "metric_winners": comparison.metric_winners,
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
def meta_audit(req: AuditRequest):
    content = ContentInput(text=req.text, content_type=req.content_type)
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
