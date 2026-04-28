import sys
sys.path.insert(0, '/content/neurascore')

from data_models import BrainResponse, ScoredResult


# ── Normalisation bounds ───────────────────────────────────────────────────────
# These define what "0" and "100" mean for each brain region.
# Calibrated against simulator range (0.1–1.0) and TRIBE v2 expected output.
# Adjust these once real TRIBE v2 data flows through.

BOUNDS = {
    "prefrontal_cortex":       (0.1, 1.0),
    "amygdala":                (0.1, 1.0),
    "hippocampus":             (0.1, 1.0),
    "visual_cortex":           (0.1, 1.0),
    "broca_area":              (0.1, 1.0),
    "nucleus_accumbens":       (0.1, 1.0),
    "default_mode_network":    (0.1, 1.0),
    "superior_temporal_gyrus": (0.1, 1.0),
    "motor_cortex":            (0.1, 1.0),
}


def _normalise(value: float, region: str) -> float:
    """Scale a raw activation to 0–100 using known bounds."""
    low, high = BOUNDS[region]
    scaled = (value - low) / (high - low)
    return round(max(0.0, min(100.0, scaled * 100)), 1)


# ── Metric weights ─────────────────────────────────────────────────────────────
# Each metric is a weighted blend of brain regions.
# These weights ARE your proprietary scoring rubric.
# Tweak these as you gather real-world validation data.

ATTENTION_WEIGHTS = {
    "prefrontal_cortex": 0.60,
    "default_mode_network": 0.25,   # Low DMN = focused attention
    "superior_temporal_gyrus": 0.15,
}

EMOTION_WEIGHTS = {
    "amygdala": 0.70,
    "default_mode_network": 0.20,   # High DMN = self-relevant emotion
    "motor_cortex": 0.10,           # Embodied emotional response
}

MEMORY_WEIGHTS = {
    "hippocampus": 0.65,
    "amygdala": 0.25,               # Emotional events encode better
    "prefrontal_cortex": 0.10,
}

VISUAL_ENGAGEMENT_WEIGHTS = {
    "visual_cortex": 0.75,
    "motor_cortex": 0.15,           # Action readiness from visual scene
    "superior_temporal_gyrus": 0.10,
}

LANGUAGE_CLARITY_WEIGHTS = {
    "broca_area": 0.70,
    "superior_temporal_gyrus": 0.20,
    "prefrontal_cortex": 0.10,
}

DESIRE_WEIGHTS = {
    "nucleus_accumbens": 0.65,
    "amygdala": 0.20,
    "prefrontal_cortex": 0.15,
}

# Overall score weights — how much each metric contributes to the final number
OVERALL_WEIGHTS = {
    "attention": 0.25,
    "emotion": 0.20,
    "memory": 0.20,
    "visual_engagement": 0.15,
    "language_clarity": 0.10,
    "desire": 0.10,
}


def _weighted_score(brain: BrainResponse, weights: dict) -> float:
    """Compute a weighted blend of normalised brain region scores."""
    total = 0.0
    for region, weight in weights.items():
        raw_value = getattr(brain, region, 0.0)
        normalised = _normalise(raw_value, region)

        # Invert DMN for attention — high DMN means mind-wandering, not focus
        if region == "default_mode_network" and "ATTENTION" in str(weights):
            normalised = 100.0 - normalised

        total += normalised * weight
    return round(total, 1)


def score(brain_response: BrainResponse) -> ScoredResult:
    """
    ViewModel entry point.
    Converts raw BrainResponse into human-readable ScoredResult (0–100).
    This is the ONLY function comparison_engine and app.py ever call.
    Never import tribe_model.py from here — Model and ViewModel stay separate.
    """
    attention         = _weighted_score(brain_response, ATTENTION_WEIGHTS)
    emotion           = _weighted_score(brain_response, EMOTION_WEIGHTS)
    memory            = _weighted_score(brain_response, MEMORY_WEIGHTS)
    visual_engagement = _weighted_score(brain_response, VISUAL_ENGAGEMENT_WEIGHTS)
    language_clarity  = _weighted_score(brain_response, LANGUAGE_CLARITY_WEIGHTS)
    desire            = _weighted_score(brain_response, DESIRE_WEIGHTS)

    overall = round(
        attention         * OVERALL_WEIGHTS["attention"] +
        emotion           * OVERALL_WEIGHTS["emotion"] +
        memory            * OVERALL_WEIGHTS["memory"] +
        visual_engagement * OVERALL_WEIGHTS["visual_engagement"] +
        language_clarity  * OVERALL_WEIGHTS["language_clarity"] +
        desire            * OVERALL_WEIGHTS["desire"],
        1
    )

    # Hook strength — first-impression signal (attention + emotion, front-weighted)
    hook_strength = round((attention * 0.55) + (emotion * 0.45), 1)

    return ScoredResult(
        content_id=brain_response.content_id,
        attention=attention,
        emotion=emotion,
        memory=memory,
        visual_engagement=visual_engagement,
        language_clarity=language_clarity,
        desire=desire,
        overall_score=overall,
        hook_strength=hook_strength,
    )
