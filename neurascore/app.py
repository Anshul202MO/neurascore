import sys
sys.path.insert(0, '/content/neurascore')

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from data_models import ContentInput, ContentType
from tribe_model import predict
from scoring_engine import score
from comparison_engine import compare

app = FastAPI(title="NeuraScore API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextRequest(BaseModel):
    text: str
    label: Optional[str] = "Content"

class CompareRequest(BaseModel):
    text_a: str
    label_a: Optional[str] = "Version A"
    text_b: str
    label_b: Optional[str] = "Version B"

@app.get("/")
def root():
    return {"status": "NeuraScore API is live"}

@app.post("/score")
def score_content(req: TextRequest):
    try:
        content = ContentInput(
            content_type=ContentType.TEXT,
            text=req.text,
            label=req.label
        )
        brain = predict(content)
        result = score(brain)
        result.label = req.label
        return {
            "label": result.label,
            "scores": result.to_dict(),
            "model_version": brain.model_version,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/compare")
def compare_content(req: CompareRequest):
    try:
        content_a = ContentInput(
            content_type=ContentType.TEXT,
            text=req.text_a,
            label=req.label_a
        )
        content_b = ContentInput(
            content_type=ContentType.TEXT,
            text=req.text_b,
            label=req.label_b
        )
        brain_a = predict(content_a)
        brain_b = predict(content_b)
        result_a = score(brain_a)
        result_b = score(brain_b)
        result_a.label = req.label_a
        result_b.label = req.label_b
        result = compare(result_a, result_b)
        return {
            "version_a": {
                "label": result_a.label,
                "scores": result_a.to_dict()
            },
            "version_b": {
                "label": result_b.label,
                "scores": result_b.to_dict()
            },
            "winners": {
                "attention": result.attention_winner,
                "emotion": result.emotion_winner,
                "memory": result.memory_winner,
                "visual_engagement": result.visual_engagement_winner,
                "language_clarity": result.language_clarity_winner,
                "desire": result.desire_winner,
                "overall": result.overall_winner,
            },
            "deltas": {
                "attention": result.attention_delta,
                "emotion": result.emotion_delta,
                "memory": result.memory_delta,
                "visual_engagement": result.visual_engagement_delta,
                "language_clarity": result.language_clarity_delta,
                "desire": result.desire_delta,
                "overall": result.overall_delta,
            },
            "interpretations": {
                "attention": result.attention_interpretation,
                "emotion": result.emotion_interpretation,
                "memory": result.memory_interpretation,
                "visual_engagement": result.visual_engagement_interpretation,
                "language_clarity": result.language_clarity_interpretation,
                "desire": result.desire_interpretation,
            },
            "verdict": result.overall_summary,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
