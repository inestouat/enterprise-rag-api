from typing import List, Dict, Tuple

# Thresholds — tune these based on your eval results later
HIGH_CONFIDENCE = 0.6
LOW_CONFIDENCE = 0.35

def compute_confidence(results: List[Dict]) -> Dict:
    """
    Compute a composite confidence score from reranked results.
    Returns a dict with overall score, tier, and per-dimension breakdown.
    """
    if not results:
        return {
            "score": 0.0,
            "tier": "none",
            "can_answer": False,
            "reason": "No documents retrieved"
        }

    # Top result score (most important signal)
    top_score = results[0].get("rerank_score", 0.0)

    # Score consistency — are top results in agreement?
    if len(results) >= 2:
        scores = [r.get("rerank_score", 0.0) for r in results[:3]]
        avg_score = sum(scores) / len(scores)
        consistency = 1.0 - (max(scores) - min(scores))
    else:
        avg_score = top_score
        consistency = 1.0

    # Composite: weight top score heavily, consistency as modifier
    composite = round((top_score * 0.7) + (avg_score * 0.2) + (consistency * 0.1), 4)
    composite = max(0.0, min(1.0, composite))  # clamp to [0, 1]

    if composite >= HIGH_CONFIDENCE:
        tier = "high"
        can_answer = True
        reason = "Strong match found in documents"
    elif composite >= LOW_CONFIDENCE:
        tier = "medium"
        can_answer = True
        reason = "Partial match — answer may be incomplete"
    else:
        tier = "low"
        can_answer = False
        reason = "No confident match found in indexed documents"

    return {
        "score": composite,
        "tier": tier,
        "can_answer": can_answer,
        "reason": reason,
        "top_result_score": round(top_score, 4),
        "avg_score": round(avg_score, 4),
        "consistency": round(consistency, 4)
    }


def build_idk_response(query: str, results: List[Dict], confidence: Dict) -> str:
    """
    Build a structured 'I don't know' response instead of hallucinating.
    Production systems should fail gracefully and usefully.
    """
    sources_found = list({r["metadata"].get("source", "unknown") for r in results[:3]})

    response = (
        f"⚠️ Low Confidence Response\n\n"
        f"The system could not find a confident answer to: \"{query}\"\n\n"
        f"Confidence score: {confidence['score']:.2f} (threshold: {LOW_CONFIDENCE})\n"
        f"Reason: {confidence['reason']}\n\n"
    )

    if sources_found:
        response += f"Documents searched: {', '.join(sources_found)}\n\n"
        response += (
            "These documents were retrieved but did not contain a strong match. "
            "You may want to check them manually or rephrase your question."
        )
    else:
        response += "No documents are currently indexed. Please upload documents first."

    return response