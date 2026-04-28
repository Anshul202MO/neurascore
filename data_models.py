from dataclasses import dataclass, field
from typing import Optional, Dict
from enum import Enum
import uuid


class ContentType(Enum):
    VIDEO = "video"
    TEXT = "text"
    AUDIO = "audio"
    IMAGE = "image"


@dataclass
class ContentInput:
    content_type: ContentType
    file_path: Optional[str] = None
    text: Optional[str] = None
    label: Optional[str] = None
    content_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def validate(self) -> bool:
        if self.content_type == ContentType.TEXT:
            return self.text is not None and len(self.text.strip()) > 0
        else:
            return self.file_path is not None


@dataclass
class BrainResponse:
    content_id: str
    prefrontal_cortex: float = 0.0
    amygdala: float = 0.0
    hippocampus: float = 0.0
    visual_cortex: float = 0.0
    broca_area: float = 0.0
    nucleus_accumbens: float = 0.0
    default_mode_network: float = 0.0
    superior_temporal_gyrus: float = 0.0
    motor_cortex: float = 0.0
    raw_activations: Dict[str, float] = field(default_factory=dict)
    inference_time_seconds: float = 0.0
    model_version: str = "tribev2"


@dataclass
class ScoredResult:
    content_id: str
    label: Optional[str] = None
    attention: float = 0.0
    emotion: float = 0.0
    memory: float = 0.0
    visual_engagement: float = 0.0
    language_clarity: float = 0.0
    desire: float = 0.0
    overall_score: float = 0.0
    hook_strength: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {
            "attention": round(self.attention, 1),
            "emotion": round(self.emotion, 1),
            "memory": round(self.memory, 1),
            "visual_engagement": round(self.visual_engagement, 1),
            "language_clarity": round(self.language_clarity, 1),
            "desire": round(self.desire, 1),
            "overall_score": round(self.overall_score, 1),
            "hook_strength": round(self.hook_strength, 1),
        }


@dataclass
class ComparisonResult:
    result_a: ScoredResult
    result_b: ScoredResult
    attention_winner: str = ""
    emotion_winner: str = ""
    memory_winner: str = ""
    visual_engagement_winner: str = ""
    language_clarity_winner: str = ""
    desire_winner: str = ""
    overall_winner: str = ""
    attention_delta: float = 0.0
    emotion_delta: float = 0.0
    memory_delta: float = 0.0
    visual_engagement_delta: float = 0.0
    language_clarity_delta: float = 0.0
    desire_delta: float = 0.0
    overall_delta: float = 0.0
    attention_interpretation: str = ""
    emotion_interpretation: str = ""
    memory_interpretation: str = ""
    visual_engagement_interpretation: str = ""
    language_clarity_interpretation: str = ""
    desire_interpretation: str = ""
    overall_summary: str = ""
