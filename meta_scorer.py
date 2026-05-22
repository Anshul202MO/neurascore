from dataclasses import dataclass
from typing import List, Dict
from data_models import ContentInput

@dataclass
class AuditCheck:
    id: str
    category: str
    name: str
    description: str
    status: str        # "pass", "review", "fail"
    score: float       # 0-100
    feedback: str

@dataclass
class MetaAuditResult:
    overall_score: float
    verdict: str
    checks: List[AuditCheck]
    category_scores: Dict[str, float]

def run_meta_audit(content: ContentInput) -> MetaAuditResult:
    text = (content.text or "").lower()
    words = text.split()
    word_count = len(words)

    checks = []

    # ── YOUTUBE ABCD ────────────────────────────────────────────────
    hook_words = ["introducing", "discover", "imagine", "what if", "now", "new", "you", "your", "free", "save"]
    has_hook = any(w in text for w in hook_words)
    checks.append(AuditCheck(
        id="yt_attract", category="YouTube ABCD",
        name="Attract — Immediate Hook",
        description="Does the content open with a hook that grabs attention in the first 5 seconds?",
        status="pass" if has_hook else "review",
        score=85.0 if has_hook else 40.0,
        feedback="Strong opening hook detected." if has_hook else "Consider opening with a question, bold statement, or 'you'-focused line."
    ))

    brand_words = ["brand", "product", "by ", "from ", "official", "™", "®"]
    has_brand_early = any(w in text[:200] for w in brand_words)
    checks.append(AuditCheck(
        id="yt_brand", category="YouTube ABCD",
        name="Brand — Early Brand Presence",
        description="Is the brand/product introduced naturally within the first 5 seconds?",
        status="pass" if has_brand_early else "review",
        score=80.0 if has_brand_early else 45.0,
        feedback="Brand reference found early." if has_brand_early else "Try integrating the brand name or product naturally within the opening."
    ))

    emotion_words = ["love", "feel", "imagine", "dream", "fear", "laugh", "cry", "joy", "hate", "hope", "trust"]
    has_emotion = any(w in text for w in emotion_words)
    checks.append(AuditCheck(
        id="yt_connect", category="YouTube ABCD",
        name="Connect — Emotional Language",
        description="Does the content use emotional or storytelling language to connect with the viewer?",
        status="pass" if has_emotion else "review",
        score=80.0 if has_emotion else 40.0,
        feedback="Emotional language present." if has_emotion else "Add emotional resonance — humor, aspiration, or relatable tension."
    ))

    cta_words = ["click", "shop", "buy", "visit", "sign up", "subscribe", "learn more", "get", "try", "download", "order"]
    has_cta = any(w in text for w in cta_words)
    checks.append(AuditCheck(
        id="yt_direct", category="YouTube ABCD",
        name="Direct — Clear Call to Action",
        description="Is there a clear, direct CTA telling the viewer what to do next?",
        status="pass" if has_cta else "fail",
        score=90.0 if has_cta else 10.0,
        feedback="CTA detected." if has_cta else "Add a specific CTA: 'Shop now', 'Visit our site', 'Subscribe today'."
    ))

    # ── BUMPER ADS ───────────────────────────────────────────────────
    single_focus = word_count <= 30
    checks.append(AuditCheck(
        id="bump_focus", category="Bumper Ads",
        name="Single Focus",
        description="Does the content focus on ONE clear message (ideal for 6-second bumpers)?",
        status="pass" if single_focus else "review",
        score=90.0 if single_focus else 50.0,
        feedback="Concise and focused." if single_focus else "Bumpers work best with a single message. Consider trimming or splitting."
    ))

    striking_words = ["only", "exclusive", "limited", "just", "introducing", "new", "never", "always", "every"]
    has_striking = any(w in text for w in striking_words)
    checks.append(AuditCheck(
        id="bump_establish", category="Bumper Ads",
        name="Establish the Ad Immediately",
        description="Does the opening immediately signal what the ad is about?",
        status="pass" if has_striking else "review",
        score=75.0 if has_striking else 45.0,
        feedback="Strong opening signal found." if has_striking else "Open with a striking visual cue or brand signal — don't bury the lead."
    ))

    memorable_end = any(text.endswith(w) for w in cta_words + ["today", "now", "you", "us"])
    checks.append(AuditCheck(
        id="bump_landing", category="Bumper Ads",
        name="Stick the Landing",
        description="Does the content end memorably with a single clear thought?",
        status="pass" if memorable_end else "review",
        score=80.0 if memorable_end else 45.0,
        feedback="Strong ending detected." if memorable_end else "End on one clear thought — avoid cramming logos, taglines, and offers at the end."
    ))

    # ── PERFORMANCE CREATIVE ─────────────────────────────────────────
    mobile_words = ["mobile", "app", "phone", "screen", "tap", "swipe", "download"]
    has_mobile = any(w in text for w in mobile_words)
    checks.append(AuditCheck(
        id="perf_mobile", category="Performance Creative",
        name="Built for Mobile",
        description="Does the content consider mobile-first viewing (tight framing, large text, snappy pacing)?",
        status="pass" if has_mobile else "review",
        score=75.0 if has_mobile else 50.0,
        feedback="Mobile context referenced." if has_mobile else "Consider mobile viewers — short sentences, punchy language, and visual clarity."
    ))

    audio_words = ["hear", "listen", "sound", "music", "voice", "say", "announcing", "introducing"]
    has_audio = any(w in text for w in audio_words)
    checks.append(AuditCheck(
        id="perf_audio", category="Performance Creative",
        name="Sight + Sound Together",
        description="Does the content leverage both audio and visual elements for stronger brand recall?",
        status="pass" if has_audio else "review",
        score=75.0 if has_audio else 50.0,
        feedback="Audio cues present." if has_audio else "Pair visual messages with audio reinforcement — brand name said aloud lifts recall by ~40%."
    ))

    benefit_words = ["because", "so you", "which means", "giving you", "helps", "makes", "lets you", "allows"]
    has_benefit = any(w in text for w in benefit_words)
    checks.append(AuditCheck(
        id="perf_benefit", category="Performance Creative",
        name="Benefit-Led Messaging",
        description="Does the content lead with a user benefit rather than a product feature?",
        status="pass" if has_benefit else "review",
        score=80.0 if has_benefit else 40.0,
        feedback="Benefit framing detected." if has_benefit else "Lead with what the user gains, not what the product does."
    ))

    # ── SEARCH ADS ───────────────────────────────────────────────────
    specific_cta = any(phrase in text for phrase in ["shop now", "buy now", "sign up", "get started", "learn more", "book now", "try free"])
    checks.append(AuditCheck(
        id="search_cta", category="Search Ads",
        name="Specific Call to Action",
        description="Is the CTA specific and action-oriented rather than generic?",
        status="pass" if specific_cta else "review",
        score=85.0 if specific_cta else 40.0,
        feedback="Specific CTA found." if specific_cta else "Use specific CTAs like 'Shop now', 'Book today' instead of generic 'Click here'."
    ))

    urgency_earned = any(w in text for w in ["today", "limited", "exclusive", "only", "expires", "ends"])
    fake_urgency = any(phrase in text for phrase in ["call us today", "contact us today", "reach out today"])
    checks.append(AuditCheck(
        id="search_urgency", category="Search Ads",
        name="Earned Urgency (No False Urgency)",
        description="Does the copy avoid generic false urgency and instead use earned urgency?",
        status="pass" if (urgency_earned and not fake_urgency) else ("review" if not urgency_earned else "fail"),
        score=85.0 if (urgency_earned and not fake_urgency) else (60.0 if not urgency_earned else 20.0),
        feedback="Urgency feels earned." if (urgency_earned and not fake_urgency) else "Avoid 'call us today' — earn urgency with real deadlines or scarcity."
    ))

    has_value_prop = word_count >= 8 and any(w in text for w in ["best", "top", "leading", "trusted", "proven", "#1", "award"])
    checks.append(AuditCheck(
        id="search_value", category="Search Ads",
        name="Clear Value Proposition",
        description="Does the copy communicate a clear, distinct value proposition?",
        status="pass" if has_value_prop else "review",
        score=80.0 if has_value_prop else 45.0,
        feedback="Value proposition present." if has_value_prop else "State clearly why you're the best choice — what makes you different?"
    ))

    user_focused = text.count("you") + text.count("your") >= 1
    checks.append(AuditCheck(
        id="search_user", category="Search Ads",
        name="User-Focused Language",
        description="Does the copy speak to the user's needs using 'you/your' language?",
        status="pass" if user_focused else "review",
        score=85.0 if user_focused else 40.0,
        feedback="User-focused language detected." if user_focused else "Address the reader directly — use 'you' and 'your' to create relevance."
    ))

    # ── INTERACTIVITY ────────────────────────────────────────────────
    interactive_words = ["poll", "vote", "choose", "pick", "tell us", "which", "would you", "quiz", "challenge"]
    has_interactive = any(w in text for w in interactive_words)
    checks.append(AuditCheck(
        id="inter_engage", category="Interactivity",
        name="Interactive / Engagement Element",
        description="Does the content include an interactive element (poll, question, challenge) to drive engagement?",
        status="pass" if has_interactive else "review",
        score=80.0 if has_interactive else 50.0,
        feedback="Interactive element found." if has_interactive else "Consider adding a poll, question, or challenge to boost engagement and recall."
    ))

    # ── BRANDED CONTENT ──────────────────────────────────────────────
    disclosure_words = ["paid", "sponsored", "partnership", "collab", "ad", "#ad", "#sponsored", "in partnership"]
    has_disclosure = any(w in text for w in disclosure_words)
    checks.append(AuditCheck(
        id="bc_disclosure", category="Branded Content",
        name="Branded Content Disclosure",
        description="If this is influencer/branded content, is the paid partnership disclosed?",
        status="pass" if has_disclosure else "review",
        score=90.0 if has_disclosure else 55.0,
        feedback="Partnership disclosure present." if has_disclosure else "For branded content, ensure 'Paid partnership' or '#ad' disclosure is included."
    ))

    # ── SCORING ──────────────────────────────────────────────────────
    overall = sum(c.score for c in checks) / len(checks)

    categories = {}
    for c in checks:
        categories.setdefault(c.category, []).append(c.score)
    category_scores = {cat: round(sum(v)/len(v), 1) for cat, v in categories.items()}

    if overall >= 75:
        verdict = "Strong creative. Well-structured with clear hooks, branding, and CTAs."
    elif overall >= 55:
        verdict = "Decent creative with room to improve. Focus on CTA clarity and emotional connection."
    else:
        verdict = "Needs significant work. Missing key elements — hook, CTA, or benefit framing."

    return MetaAuditResult(
        overall_score=round(overall, 1),
        verdict=verdict,
        checks=checks,
        category_scores=category_scores
    )
