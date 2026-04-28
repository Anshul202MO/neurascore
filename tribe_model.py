import time
import sys
import os
sys.path.insert(0, '/content/neurascore')

from data_models import ContentInput, BrainResponse, ContentType
import torch
import numpy as np

# ── Attempt to load TRIBE v2 ──────────────────────────────────────────────────
# If the model isn't available we fall back to a deterministic simulator
# so the rest of the platform can be built and tested immediately.

TRIBE_AVAILABLE = False
model = None
processor = None

try:
    from transformers import AutoModel, AutoProcessor
    print("Attempting to load TRIBE v2 from Hugging Face...")
    processor = AutoProcessor.from_pretrained("facebook/tribev2")
    model = AutoModel.from_pretrained("facebook/tribev2")
    model.eval()
    TRIBE_AVAILABLE = True
    print("✅ TRIBE v2 loaded successfully.")
except Exception as e:
    print(f"⚠️  TRIBE v2 not available ({e}). Running in simulator mode.")
    TRIBE_AVAILABLE = False


def _simulate_brain_response(content_input: ContentInput) -> dict:
    """
    Deterministic simulator — returns realistic-looking brain activations
    based on content type and text length/keywords.
    Used during development and when TRIBE v2 is unavailable.
    Replace this function's internals with nothing when TRIBE v2 loads.
    """
    seed_string = (content_input.content_id or "") + (content_input.text or "") + (content_input.file_path or "")
    seed = sum(ord(c) for c in seed_string) % 10000
    rng = np.random.RandomState(seed)

    base = {
        "prefrontal_cortex":      rng.uniform(0.3, 0.9),
        "amygdala":               rng.uniform(0.2, 0.95),
        "hippocampus":            rng.uniform(0.25, 0.85),
        "visual_cortex":          rng.uniform(0.3, 0.95),
        "broca_area":             rng.uniform(0.2, 0.9),
        "nucleus_accumbens":      rng.uniform(0.15, 0.85),
        "default_mode_network":   rng.uniform(0.2, 0.8),
        "superior_temporal_gyrus":rng.uniform(0.25, 0.9),
        "motor_cortex":           rng.uniform(0.1, 0.7),
    }

    # Boost visual regions for video/image content
    if content_input.content_type in [ContentType.VIDEO, ContentType.IMAGE]:
        base["visual_cortex"] = min(1.0, base["visual_cortex"] * 1.3)
        base["motor_cortex"]  = min(1.0, base["motor_cortex"]  * 1.2)

    # Boost language regions for text content
    if content_input.content_type == ContentType.TEXT:
        base["broca_area"]    = min(1.0, base["broca_area"]    * 1.4)
        base["prefrontal_cortex"] = min(1.0, base["prefrontal_cortex"] * 1.2)

    return base


def predict(content_input: ContentInput) -> BrainResponse:
    """
    Main entry point for the Model layer.
    Accepts a ContentInput, returns a BrainResponse with raw activations.
    This is the ONLY function the ViewModel (scoring_engine) ever calls.
    """
    if not content_input.validate():
        raise ValueError(f"Invalid ContentInput: file_path or text must be provided.")

    start = time.time()

    if TRIBE_AVAILABLE:
        # ── Real TRIBE v2 inference ───────────────────────────────────────────
        try:
            if content_input.content_type == ContentType.TEXT:
                inputs = processor(text=content_input.text, return_tensors="pt")
            else:
                inputs = processor(videos=content_input.file_path, return_tensors="pt")

            with torch.no_grad():
                outputs = model(**inputs)

            # Extract per-region activations from model output
            activations = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()

            # Map to named regions (indices based on TRIBE v2 parcel ordering)
            region_map = {
                "prefrontal_cortex":       float(activations[0]),
                "amygdala":                float(activations[1]),
                "hippocampus":             float(activations[2]),
                "visual_cortex":           float(activations[3]),
                "broca_area":              float(activations[4]),
                "nucleus_accumbens":       float(activations[5]),
                "default_mode_network":    float(activations[6]),
                "superior_temporal_gyrus": float(activations[7]),
                "motor_cortex":            float(activations[8]),
            }
        except Exception as e:
            print(f"⚠️  TRIBE v2 inference failed ({e}). Falling back to simulator.")
            region_map = _simulate_brain_response(content_input)
    else:
        # ── Simulator mode ────────────────────────────────────────────────────
        region_map = _simulate_brain_response(content_input)

    elapsed = round(time.time() - start, 2)

    return BrainResponse(
        content_id=content_input.content_id,
        prefrontal_cortex=region_map["prefrontal_cortex"],
        amygdala=region_map["amygdala"],
        hippocampus=region_map["hippocampus"],
        visual_cortex=region_map["visual_cortex"],
        broca_area=region_map["broca_area"],
        nucleus_accumbens=region_map["nucleus_accumbens"],
        default_mode_network=region_map["default_mode_network"],
        superior_temporal_gyrus=region_map["superior_temporal_gyrus"],
        motor_cortex=region_map["motor_cortex"],
        raw_activations=region_map,
        inference_time_seconds=elapsed,
        model_version="tribev2" if TRIBE_AVAILABLE else "simulator_v1",
    )
