import sys
sys.path.insert(0, '/content/neurascore')

from data_models import ScoredResult, ComparisonResult


METRIC_INTERPRETATIONS = {
    "attention": {
        "high":   "Strong attention pull — content demands and holds focus.",
        "medium": "Moderate attention — may lose some viewers along the way.",
        "low":    "Attention risk — content struggles to hold focus.",
    },
    "emotion": {
        "high":   "High emotional resonance — content connects on a feeling level.",
        "medium": "Some emotional engagement — could be amplified.",
        "low":    "Emotionally flat — unlikely to create a lasting impression.",
    },
    "memory": {
        "high":   "Strong memory encoding — viewers are likely to recall this.",
        "medium": "Moderate recall potential — key messages may fade.",
        "low":    "Low memorability — content risks being forgotten quickly.",
    },
    "visual_engagement": {
        "high":   "Visually compelling — scenes and imagery are pulling the eye.",
        "medium": "Decent visual interest — some moments stronger than others.",
        "low":    "Weak visual pull — imagery is not doing enough work.",
    },
    "language_clarity": {
        "high":   "Crystal clear messaging — verbal content is processed easily.",
        "medium": "Reasonably clear — some lines may need sharpening.",
        "low":    "Language friction — viewers may struggle to follow the message.",
    },
    "desire": {
        "high":   "Strong intent-to-act signal — content drives want and action.",
        "medium": "Some desire triggered — the call to action could be stronger.",
        "low":    "Low desire signal — content is not moving people to act.",
    },
}


def _interpret(metric, score):
    tier = "high" if score >= 70 else "medium" if score >= 40 else "low"
    return METRIC_INTERPRETATIONS[metric][tier]


def _winner(score_a, score_b, threshold=3.0):
    diff = score_a - score_b
    if abs(diff) < threshold:
        return "tie"
    return "A" if diff > 0 else "B"


def compare(result_a, result_b):
    metrics = [
        "attention",
        "emotion",
        "memory",
        "visual_engagement",
        "language_clarity",
        "desire",
    ]

    comparison = ComparisonResult(result_a=result_a, result_b=result_b)

    for metric in metrics:
        score_a = getattr(result_a, metric)
        score_b = getattr(result_b, metric)
        winner = _winner(score_a, score_b)
        delta = round(score_a - score_b, 1)
        winning_score = score_a if winner == "A" else score_b
        interpretation = _interpret(metric, winning_score)
        setattr(comparison, f"{metric}_winner", winner)
        setattr(comparison, f"{metric}_delta", delta)
        setattr(comparison, f"{metric}_interpretation", interpretation)

    comparison.overall_winner = _winner(
        result_a.overall_score,
        result_b.overall_score
    )
    comparison.overall_delta = round(
        result_a.overall_score - result_b.overall_score, 1
    )

    winner_label = None
    if comparison.overall_winner == "A":
        winner_label = result_a.label or "Version A"
    elif comparison.overall_winner == "B":
        winner_label = result_b.label or "Version B"

    if winner_label:
        margin = abs(comparison.overall_delta)
        strength = "convincingly" if margin > 10 else "narrowly"
        best_metric = max(
            metrics,
            key=lambda m: abs(getattr(result_a, m) - getattr(result_b, m))
        )
        best_gap = max(
            abs(getattr(result_a, m) - getattr(result_b, m)) for m in metrics
        )
        winning_score = result_a.overall_score if comparison.overall_winner == "A" else result_b.overall_score
        comparison.overall_summary = (
            f"{winner_label} wins {strength} with an overall score of "
            f"{winning_score}. Key advantage: {best_metric} "
            f"(gap of {best_gap:.1f} points)."
        )
    else:
        comparison.overall_summary = (
            f"Too close to call. Both versions score similarly. "
            f"Test with a real audience to break the tie."
        )

    return comparison
