import os
import json
from groq import Groq
from data_models import ContentInput

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ── OPTION A: QUICK CRITIQUE ─────────────────────────────────────────────────
# Model: llama-3.1-8b-instant (fastest, highest free tier limits)
# Returns: 3-5 specific quoted critiques with rewrites
# Used for: Free trial + Starter tier

QUICK_CRITIQUE_PROMPT = """You are a senior neuromarketing analyst. Your job is to critique advertising copy using neuroscience and persuasion principles.

Analyze the following ad copy and return EXACTLY 3-5 critiques in valid JSON format.

For each critique you MUST:
1. Quote the EXACT phrase from the copy that is weak or strong
2. Give the neurological/psychological reason it works or doesn't
3. Suggest a specific one-line rewrite if it's weak (skip rewrite if it's strong)
4. Label it as "weak" or "strong"

Return ONLY this JSON structure, nothing else:
{
  "overall_verdict": "one sentence summary of the copy's biggest strength and weakness",
  "score_context": "one sentence explaining what the brain scores mean for this specific copy",
  "critiques": [
    {
      "phrase": "exact quoted phrase from the copy",
      "type": "weak" or "strong",
      "reason": "neurological/psychological explanation in plain English",
      "rewrite": "suggested rewrite (only if weak, otherwise null)"
    }
  ]
}

Ad copy to analyze:
"""

def run_quick_critique(content: ContentInput) -> dict:
    text = content.text or ""
    
    if not text.strip():
        return {
            "overall_verdict": "No content provided.",
            "score_context": "",
            "critiques": []
        }
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": QUICK_CRITIQUE_PROMPT + text
                }
            ],
            temperature=0.3,
            max_tokens=800
        )
        
        raw = response.choices[0].message.content.strip()
        
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        
        result = json.loads(raw)
        return result
        
    except json.JSONDecodeError:
        return {
            "overall_verdict": "Analysis complete but could not parse structured response.",
            "score_context": "",
            "critiques": [],
            "raw_response": raw
        }
    except Exception as e:
        return {
            "overall_verdict": f"Analysis failed: {str(e)}",
            "score_context": "",
            "critiques": []
        }


# ── OPTION B: DEEP ANALYSIS ──────────────────────────────────────────────────
# Model: llama-3.3-70b-versatile (best quality on free tier)
# Returns: Full structural breakdown + rewritten copy
# Used for: Growth + Enterprise tier

DEEP_ANALYSIS_PROMPT = """You are the world's leading neuromarketing analyst with deep expertise in cognitive neuroscience, persuasion psychology, and advertising effectiveness.

Analyze the following ad copy with the depth and precision of a $500/hour creative strategist. 

Return ONLY valid JSON in this exact structure, nothing else:
{
  "executive_summary": "2-3 sentence overall assessment",
  "hook_analysis": {
    "verdict": "pass/weak/fail",
    "explanation": "detailed explanation of how the opening lands neurologically",
    "quoted_hook": "the actual opening phrase",
    "improved_hook": "a rewritten opening that would perform better"
  },
  "emotional_arc": {
    "verdict": "strong/moderate/flat",
    "explanation": "how emotion builds or fails to build through the copy",
    "emotional_triggers_found": ["list", "of", "triggers", "detected"],
    "missing_triggers": ["list", "of", "triggers", "that", "would", "help"]
  },
  "memory_encoding": {
    "verdict": "strong/moderate/weak",
    "explanation": "what makes this memorable or forgettable",
    "memorable_phrases": ["phrases that will stick"],
    "forgettable_phrases": ["phrases that won't register"]
  },
  "desire_mechanics": {
    "verdict": "strong/moderate/weak", 
    "explanation": "how well the copy creates want vs just awareness",
    "desire_drivers_found": ["list of desire triggers"],
    "missing_desire_drivers": ["what would create stronger want"]
  },
  "cta_psychology": {
    "verdict": "strong/moderate/weak",
    "explanation": "psychological analysis of the call to action",
    "quoted_cta": "the actual CTA phrase",
    "improved_cta": "a psychologically stronger version"
  },
  "phrase_by_phrase": [
    {
      "phrase": "quoted phrase from copy",
      "verdict": "strong/weak/neutral",
      "neuroscience_note": "brief explanation",
      "rewrite": "improved version or null if strong"
    }
  ],
  "rewritten_copy": "Complete rewritten version of the entire ad copy incorporating all improvements. Must feel natural and human, not like an AI rewrote it.",
  "top_3_actions": [
    "Most important change to make",
    "Second most important change",
    "Third most important change"
  ]
}

Ad copy to analyze:
"""

def run_deep_analysis(content: ContentInput) -> dict:
    text = content.text or ""
    
    if not text.strip():
        return {
            "executive_summary": "No content provided.",
            "critiques": []
        }
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user", 
                    "content": DEEP_ANALYSIS_PROMPT + text
                }
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        raw = response.choices[0].message.content.strip()
        
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        
        result = json.loads(raw)
        return result
        
    except json.JSONDecodeError:
        return {
            "executive_summary": "Analysis complete but could not parse structured response.",
            "raw_response": raw
        }
    except Exception as e:
        return {
            "executive_summary": f"Analysis failed: {str(e)}",
            "critiques": []
        }