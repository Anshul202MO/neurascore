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


def _first_n_words(text: str, n: int = 8) -> str:
    """Return first n words of text for feedback snippets."""
    words = text.strip().split()
    snippet = " ".join(words[:n])
    return f'"{snippet}..."' if len(words) > n else f'"{snippet}"'


def _find_first_match(text: str, word_list: list) -> str:
    """Return the first matching word/phrase found in text."""
    for w in word_list:
        if w in text:
            return w
    return ""


def run_meta_audit(content: ContentInput) -> MetaAuditResult:
    raw_text = (content.text or "")
    text = raw_text.lower()
    words = text.split()
    word_count = len(words)
    opening = _first_n_words(text, 8)
    label = content.label or "this content"

    checks = []

    # ── YOUTUBE ABCD ────────────────────────────────────────────────

    hook_words = ["introducing", "discover", "imagine", "what if", "now", "new",
                  "you", "your", "free", "save", "why", "how", "stop", "warning",
                  "finally", "announcing", "never", "always", "the truth"]
    matched_hook = _find_first_match(text, hook_words)
    has_hook = bool(matched_hook)
    checks.append(AuditCheck(
        id="yt_attract", category="YouTube ABCD",
        name="Attract — Immediate Hook",
        description="Does the content open with a hook that grabs attention in the first 5 seconds?",
        status="pass" if has_hook else "review",
        score=85.0 if has_hook else 40.0,
        feedback=(
            f'Opens with "{matched_hook}" — good attention signal in the first line.'
            if has_hook else
            f'Opening with {opening} doesn\'t immediately hook the viewer. '
            f'Try leading with a question, a bold claim, or a "you"-focused statement '
            f'to stop the scroll in the first 5 seconds.'
        )
    ))

    brand_words = ["brand", "product", "by ", "from ", "official", "™", "®"]
    opening_200 = text[:200]
    matched_brand = _find_first_match(opening_200, brand_words)
    has_brand_early = bool(matched_brand)
    checks.append(AuditCheck(
        id="yt_brand", category="YouTube ABCD",
        name="Brand — Early Brand Presence",
        description="Is the brand/product introduced naturally within the first 5 seconds?",
        status="pass" if has_brand_early else "review",
        score=80.0 if has_brand_early else 45.0,
        feedback=(
            f'Brand signal ("{matched_brand}") appears early — '
            f'good for recall without feeling forced.'
            if has_brand_early else
            f'No brand signal detected in the opening of {opening}. '
            f'Weave the brand or product name in naturally within the first line — '
            f'early brand presence lifts recall significantly.'
        )
    ))

    emotion_words = ["love", "feel", "imagine", "dream", "fear", "laugh", "cry",
                     "joy", "hate", "hope", "trust", "proud", "excited", "worry",
                     "believe", "inspire", "passion", "together", "real", "honest"]
    matched_emotion = _find_first_match(text, emotion_words)
    has_emotion = bool(matched_emotion)
    checks.append(AuditCheck(
        id="yt_connect", category="YouTube ABCD",
        name="Connect — Emotional Language",
        description="Does the content use emotional or storytelling language to connect with the viewer?",
        status="pass" if has_emotion else "review",
        score=80.0 if has_emotion else 40.0,
        feedback=(
            f'Emotional word "{matched_emotion}" detected — '
            f'creates a human connection beyond just the product message.'
            if has_emotion else
            f'The copy in {opening} reads functionally but lacks emotional pull. '
            f'Add one emotional anchor — aspiration, humour, tension, or a relatable moment — '
            f'to make it feel human rather than transactional.'
        )
    ))

    cta_words = ["click", "shop", "buy", "visit", "sign up", "subscribe",
                 "learn more", "get", "try", "download", "order", "book",
                 "start", "join", "explore", "discover"]
    matched_cta = _find_first_match(text, cta_words)
    has_cta = bool(matched_cta)
    checks.append(AuditCheck(
        id="yt_direct", category="YouTube ABCD",
        name="Direct — Clear Call to Action",
        description="Is there a clear, direct CTA telling the viewer what to do next?",
        status="pass" if has_cta else "fail",
        score=90.0 if has_cta else 10.0,
        feedback=(
            f'CTA found: "{matched_cta}" — gives the viewer a clear next step.'
            if has_cta else
            f'No CTA detected anywhere in {label}. '
            f'Without a direct instruction, viewers disengage after watching. '
            f'Add a specific action: "Shop now", "Visit our site", "Subscribe today".'
        )
    ))

    # ── BUMPER ADS ───────────────────────────────────────────────────

    single_focus = word_count <= 30
    checks.append(AuditCheck(
        id="bump_focus", category="Bumper Ads",
        name="Single Focus",
        description="Does the content focus on ONE clear message (ideal for 6-second bumpers)?",
        status="pass" if single_focus else "review",
        score=90.0 if single_focus else 50.0,
        feedback=(
            f'At {word_count} words, this is tight and focused — '
            f'ideal for bumper format where one message lands harder than three.'
            if single_focus else
            f'At {word_count} words, this copy is trying to do too much for a bumper format. '
            f'Bumpers work best with a single message. '
            f'Pick the ONE thing you want remembered and cut the rest.'
        )
    ))

    striking_words = ["only", "exclusive", "limited", "just", "introducing",
                      "new", "never", "always", "every", "first", "last",
                      "biggest", "smallest", "fastest", "proven"]
    matched_striking = _find_first_match(text, striking_words)
    has_striking = bool(matched_striking)
    checks.append(AuditCheck(
        id="bump_establish", category="Bumper Ads",
        name="Establish the Ad Immediately",
        description="Does the opening immediately signal what the ad is about?",
        status="pass" if has_striking else "review",
        score=75.0 if has_striking else 45.0,
        feedback=(
            f'"{matched_striking}" in the opening establishes the ad space quickly — '
            f'viewers know immediately what they\'re watching.'
            if has_striking else
            f'The opening {opening} doesn\'t immediately signal brand territory. '
            f'In the first 1-2 seconds, viewers are still figuring out what\'s playing — '
            f'use a bold visual cue or a distinctive word to claim your space fast.'
        )
    ))

    end_words = cta_words + ["today", "now", "you", "us", "free", "go", "here"]
    last_word = text.strip().split()[-1] if words else ""
    last_few = " ".join(text.strip().split()[-4:]) if len(words) >= 4 else text
    memorable_end = any(w in last_few for w in end_words)
    checks.append(AuditCheck(
        id="bump_landing", category="Bumper Ads",
        name="Stick the Landing",
        description="Does the content end memorably with a single clear thought?",
        status="pass" if memorable_end else "review",
        score=80.0 if memorable_end else 45.0,
        feedback=(
            f'Ends on "{last_word}" — lands cleanly with a clear final thought.'
            if memorable_end else
            f'Ends on "{last_word}" which doesn\'t leave a strong final impression. '
            f'Your last word is what viewers carry away. '
            f'End on a CTA, your brand name, or one punchy word that sticks.'
        )
    ))

    # ── PERFORMANCE CREATIVE ─────────────────────────────────────────

    mobile_words = ["mobile", "app", "phone", "screen", "tap", "swipe",
                    "download", "device", "on the go", "anywhere", "anytime"]
    matched_mobile = _find_first_match(text, mobile_words)
    has_mobile = bool(matched_mobile)
    avg_sentence_len = word_count / max(text.count(".") + text.count("!") + text.count("?"), 1)
    is_snappy = avg_sentence_len <= 12
    checks.append(AuditCheck(
        id="perf_mobile", category="Performance Creative",
        name="Built for Mobile",
        description="Does the content consider mobile-first viewing — short, punchy, scannable?",
        status="pass" if (has_mobile or is_snappy) else "review",
        score=75.0 if (has_mobile or is_snappy) else 50.0,
        feedback=(
            f'"{matched_mobile}" signals mobile awareness, and sentence length is tight — '
            f'reads well on a small screen.'
            if has_mobile else
            f'Copy reads snappily at ~{round(avg_sentence_len)} words per sentence — '
            f'good pacing for mobile viewers.'
            if is_snappy else
            f'Sentences average ~{round(avg_sentence_len)} words — '
            f'too long for mobile where attention spans are shortest. '
            f'Break it up. Shorter sentences, punchier language, one idea per line.'
        )
    ))

    audio_words = ["hear", "listen", "sound", "music", "voice", "say",
                   "announcing", "introducing", "tune", "beat", "audio", "spoken"]
    matched_audio = _find_first_match(text, audio_words)
    has_audio = bool(matched_audio)
    checks.append(AuditCheck(
        id="perf_audio", category="Performance Creative",
        name="Sight + Sound Together",
        description="Does the content leverage both audio and visual elements for stronger brand recall?",
        status="pass" if has_audio else "review",
        score=75.0 if has_audio else 50.0,
        feedback=(
            f'Audio reference "{matched_audio}" detected — '
            f'pairing visual and audio signals lifts brand recall by ~40%.'
            if has_audio else
            f'No audio cues in {label}. '
            f'If this runs as video, consider scripting the brand name to be spoken aloud — '
            f'supers with matching voiceover lift recall by ~40% vs visuals alone.'
        )
    ))

    benefit_words = ["because", "so you", "which means", "giving you", "helps",
                     "makes", "lets you", "allows", "so that", "meaning",
                     "resulting in", "giving", "saving", "protecting"]
    matched_benefit = _find_first_match(text, benefit_words)
    has_benefit = bool(matched_benefit)
    checks.append(AuditCheck(
        id="perf_benefit", category="Performance Creative",
        name="Benefit-Led Messaging",
        description="Does the content lead with a user benefit rather than a product feature?",
        status="pass" if has_benefit else "review",
        score=80.0 if has_benefit else 40.0,
        feedback=(
            f'Benefit connector "{matched_benefit}" found — '
            f'the copy explains what the user gains, not just what the product does.'
            if has_benefit else
            f'{opening} leads with a feature or claim but doesn\'t connect it to a user benefit. '
            f'Add the "so what" — what does this mean for the person watching? '
            f'Try "...which means you can..." or "...so you never have to..."'
        )
    ))

    # ── SEARCH ADS ───────────────────────────────────────────────────

    specific_ctas = ["shop now", "buy now", "sign up", "get started", "learn more",
                     "book now", "try free", "get free", "start free", "order now",
                     "book today", "try today", "start today"]
    matched_specific_cta = _find_first_match(text, specific_ctas)
    has_specific_cta = bool(matched_specific_cta)
    checks.append(AuditCheck(
        id="search_cta", category="Search Ads",
        name="Specific Call to Action",
        description="Is the CTA specific and action-oriented rather than generic?",
        status="pass" if has_specific_cta else "review",
        score=85.0 if has_specific_cta else 40.0,
        feedback=(
            f'"{matched_specific_cta}" is a strong, specific CTA — '
            f'tells the reader exactly what to do and reduces friction.'
            if has_specific_cta else
            f'No specific CTA found in {label}. '
            f'Generic phrases like "click here" or "contact us" are being tuned out. '
            f'Use action-specific language: "Shop now", "Book your free demo", "Start your trial today".'
        )
    ))

    urgency_words = ["today", "limited", "exclusive", "only", "expires",
                     "ends", "last chance", "hurry", "deadline", "while stocks last",
                     "closing soon", "until", "remaining"]
    fake_urgency_phrases = ["call us today", "contact us today", "reach out today",
                            "don't wait", "act now", "hurry up"]
    matched_urgency = _find_first_match(text, urgency_words)
    matched_fake = _find_first_match(text, fake_urgency_phrases)
    urgency_earned = bool(matched_urgency)
    fake_urgency = bool(matched_fake)
    checks.append(AuditCheck(
        id="search_urgency", category="Search Ads",
        name="Earned Urgency (No False Urgency)",
        description="Does the copy use real urgency rather than generic pressure tactics?",
        status="pass" if (urgency_earned and not fake_urgency) else ("fail" if fake_urgency else "review"),
        score=85.0 if (urgency_earned and not fake_urgency) else (20.0 if fake_urgency else 60.0),
        feedback=(
            f'"{matched_urgency}" creates real, earned urgency — '
            f'specific and believable rather than manufactured pressure.'
            if (urgency_earned and not fake_urgency) else
            f'"{matched_fake}" is a false urgency phrase that audiences have learned to ignore. '
            f'Replace it with a real deadline, a stock count, or a specific offer window.'
            if fake_urgency else
            f'No urgency signals in {label}. '
            f'If there\'s a real deadline, offer window, or limited availability, call it out — '
            f'earned urgency drives action without feeling manipulative.'
        )
    ))

    value_words = ["best", "top", "leading", "trusted", "proven", "#1",
                   "award", "rated", "ranked", "recognised", "certified",
                   "guaranteed", "industry", "market", "unlike", "only we",
                   "no one else", "first to"]
    matched_value = _find_first_match(text, value_words)
    has_value_prop = word_count >= 8 and bool(matched_value)
    checks.append(AuditCheck(
        id="search_value", category="Search Ads",
        name="Clear Value Proposition",
        description="Does the copy communicate a clear, distinct value proposition?",
        status="pass" if has_value_prop else "review",
        score=80.0 if has_value_prop else 45.0,
        feedback=(
            f'"{matched_value}" signals a value claim — '
            f'gives the reader a reason to choose this over alternatives.'
            if has_value_prop else
            f'{opening} doesn\'t yet answer "why you over everyone else". '
            f'Add your differentiator — what makes this the best choice? '
            f'A number, a credential, or a specific claim beats vague positioning every time.'
        )
    ))

    you_count = text.count(" you ") + text.count(" your ") + text.startswith("you")
    user_focused = you_count >= 1
    checks.append(AuditCheck(
        id="search_user", category="Search Ads",
        name="User-Focused Language",
        description="Does the copy speak directly to the user using 'you/your' language?",
        status="pass" if user_focused else "review",
        score=85.0 if user_focused else 40.0,
        feedback=(
            f'"you/your" appears {you_count} time(s) — '
            f'the copy speaks directly to the reader, not about the product.'
            if user_focused else
            f'{opening} talks about the product but not to the person reading it. '
            f'Swap brand-centric language for reader-centric language — '
            f'"our product does X" becomes "you get X".'
        )
    ))

    # ── INTERACTIVITY ────────────────────────────────────────────────

    interactive_words = ["poll", "vote", "choose", "pick", "tell us", "which",
                         "would you", "quiz", "challenge", "comment", "share your",
                         "what do you", "let us know", "tag a", "who would"]
    matched_interactive = _find_first_match(text, interactive_words)
    has_interactive = bool(matched_interactive)
    checks.append(AuditCheck(
        id="inter_engage", category="Interactivity",
        name="Interactive / Engagement Element",
        description="Does the content include an interactive element to drive engagement?",
        status="pass" if has_interactive else "review",
        score=80.0 if has_interactive else 50.0,
        feedback=(
            f'"{matched_interactive}" invites interaction — '
            f'poll and question formats reduce cost-per-view by ~20% and boost recall.'
            if has_interactive else
            f'No interactive elements in {label}. '
            f'Adding a poll, a "which would you choose", or a direct question '
            f'can cut cost-per-view by 20% and lift 3-second views significantly.'
        )
    ))

    # ── BRANDED CONTENT ──────────────────────────────────────────────

    disclosure_words = ["paid", "sponsored", "partnership", "collab", "ad",
                        "#ad", "#sponsored", "in partnership", "gifted",
                        "paid promotion", "brand partner"]
    matched_disclosure = _find_first_match(text, disclosure_words)
    has_disclosure = bool(matched_disclosure)
    checks.append(AuditCheck(
        id="bc_disclosure", category="Branded Content",
        name="Branded Content Disclosure",
        description="If this is branded/influencer content, is the paid partnership disclosed?",
        status="pass" if has_disclosure else "review",
        score=90.0 if has_disclosure else 55.0,
        feedback=(
            f'Disclosure "{matched_disclosure}" found — '
            f'compliant with Meta\'s branded content policy and builds audience trust.'
            if has_disclosure else
            f'No disclosure detected in {label}. '
            f'If this is influencer or branded content, add "Paid partnership with [Brand]" '
            f'or "#ad" — required by Meta policy and increasingly expected by audiences.'
        )
    ))

    # ── SCORING ──────────────────────────────────────────────────────

    overall = sum(c.score for c in checks) / len(checks)

    categories = {}
    for c in checks:
        categories.setdefault(c.category, []).append(c.score)
    category_scores = {cat: round(sum(v) / len(v), 1) for cat, v in categories.items()}

    passes = sum(1 for c in checks if c.status == "pass")
    fails = sum(1 for c in checks if c.status == "fail")

    if overall >= 75:
        verdict = (
            f"Strong creative across {passes}/16 checks. "
            f"Well-structured with clear hooks, branding, and CTAs. "
            f"Minor refinements could push scores further."
        )
    elif overall >= 55:
        verdict = (
            f"Decent foundation — passes {passes}/16 checks. "
            f"Key gaps in "
            + ", ".join(c.name for c in checks if c.status in ("fail", "review"))[:120]
            + ". Address these to unlock stronger performance."
        )
    else:
        verdict = (
            f"Needs significant work — only {passes}/16 checks pass, "
            f"with {fails} outright fail(s). "
            f"Priority fixes: hook strength, CTA clarity, and benefit-led framing."
        )

    return MetaAuditResult(
        overall_score=round(overall, 1),
        verdict=verdict,
        checks=checks,
        category_scores=category_scores
    )
