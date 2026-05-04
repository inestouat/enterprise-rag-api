"""
DocIQ Evaluation Suite
Run with: python tests/eval/evaluator.py
Requires: FastAPI server running on http://localhost:8000
"""

import json
import requests
import time
import os
import re
from typing import List, Dict
from datetime import datetime

API_URL = "http://localhost:8000"
DATASET_PATH = "tests/eval/golden_dataset.json"
REPORTS_DIR = "tests/eval/reports"
OLLAMA_MODEL = "qwen2.5:3b"   # ← change this to match your ollama list output

LOW_CONFIDENCE = 0.20


# ── Helpers ────────────────────────────────────────────────────────────────────

def load_dataset(path: str) -> List[Dict]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset not found at {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def query_api(question: str, top_k: int = 3, mode: str = "hybrid") -> Dict:
    try:
        r = requests.post(
            f"{API_URL}/query",
            json={"query": question, "top_k": top_k, "retrieval_mode": mode},
            timeout=120
        )
        if r.status_code == 200:
            return r.json()
        return {"error": f"HTTP {r.status_code}: {r.text[:200]}"}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to API. Is 'python -m app.main' running?"}
    except requests.exceptions.Timeout:
        return {"error": "Request timed out"}
    except Exception as e:
        return {"error": str(e)}


def string_match_score(golden: str, generated: str) -> int:
    """Keyword + number matching fallback scorer. Returns 0-3."""
    if not generated or len(generated.strip()) < 10:
        return 0

    golden_lower = golden.lower()
    generated_lower = generated.lower()

    golden_numbers = set(re.findall(r'\$?[\d,]+\.?\d*%?', golden_lower))
    golden_numbers = {n for n in golden_numbers if len(n) > 1}

    stop_words = {
        "what", "that", "this", "with", "from", "their", "have", "were",
        "been", "would", "could", "should", "organizations", "enterprise",
        "report", "document", "which", "those", "these", "there", "they",
        "them", "then", "than", "when", "also", "only", "both", "most",
        "more", "some", "such", "each", "many", "into", "will", "does"
    }
    golden_keywords = set(
        w.strip(".,;:()[]") for w in golden_lower.split()
        if len(w) > 5 and w not in stop_words
    )

    if golden_numbers:
        numbers_found = sum(1 for n in golden_numbers if n in generated_lower)
        number_coverage = numbers_found / len(golden_numbers)
    else:
        number_coverage = 0.6

    if golden_keywords:
        sample = list(golden_keywords)[:10]
        kw_found = sum(1 for k in sample if k in generated_lower)
        kw_coverage = kw_found / len(sample)
    else:
        kw_coverage = 0.5

    coverage = (number_coverage * 0.6) + (kw_coverage * 0.4)

    if coverage >= 0.70:
        return 3
    elif coverage >= 0.45:
        return 2
    elif coverage >= 0.20:
        return 1
    else:
        return 0


def score_answer(question: str, golden: str, generated: str) -> Dict:
    """Score the generated answer using LLM judge or string matching fallback."""

    # Rule: unanswerable questions
    if golden == "NOT_IN_DOCUMENT":
        refusal_phrases = [
            "low confidence", "could not find", "don't have enough",
            "not found", "no confident", "⚠️", "cannot find",
            "no documents", "not in", "unable to find",
            "i don't have enough information", "insufficient information"
        ]
        refused = any(p in generated.lower() for p in refusal_phrases)
        return {
            "correctness": 3 if refused else 0,
            "reasoning": (
                "IDK test PASSED: system correctly refused to answer"
                if refused else
                "IDK test FAILED: system hallucinated instead of refusing"
            ),
            "method": "rule"
        }

    # Try LLM judge
    prompt = (
        "You are a strict evaluator. Score this answer and reply with JSON only.\n\n"
        f"Question: {question}\n"
        f"Expected answer: {golden}\n"
        f"Generated answer: {generated[:400]}\n\n"
        "Scoring: 3=correct and complete, 2=mostly correct minor gaps, "
        "1=partially correct significant gaps, 0=wrong or hallucinated\n\n"
        'Reply with this exact format: {"score": 2, "reasoning": "explanation here"}'
    )

    try:
        r = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0, "num_predict": 120}
            },
            timeout=45
        )

        if r.status_code != 200:
            raise ValueError(f"Ollama {r.status_code}")

        raw = r.json().get("response", "").strip()
        parsed = None

        # Strategy 1: direct JSON parse
        try:
            parsed = json.loads(raw)
        except Exception:
            pass

        # Strategy 2: find JSON object with regex
        if not parsed:
            m = re.search(r'\{[^{}]*"score"[^{}]*\}', raw, re.DOTALL)
            if m:
                try:
                    parsed = json.loads(m.group())
                except Exception:
                    pass

        # Strategy 3: extract score number
        if not parsed:
            m = re.search(r'"score"\s*:\s*([0-3])', raw)
            if m:
                parsed = {"score": int(m.group(1)), "reasoning": "score extracted via regex"}

        if parsed and "score" in parsed:
            score = max(0, min(3, int(float(str(parsed["score"])))))
            reasoning = str(parsed.get("reasoning", "")).strip()[:120]
            if not reasoning:
                reasoning = f"LLM score: {score}/3"
            return {"correctness": score, "reasoning": reasoning, "method": "llm"}

        raise ValueError(f"Unparseable response: {raw[:80]}")

    except Exception as e:
        score = string_match_score(golden, generated)
        return {
            "correctness": score,
            "reasoning": f"String match ({str(e)[:50]})",
            "method": "string_match"
        }


def check_faithfulness(answer: str, citations: List[Dict]) -> float:
    """Check if answer uses citation markers [1], [2], etc."""
    if not citations:
        return 0.0
    markers = [f"[{i+1}]" for i in range(len(citations))]
    found = sum(1 for m in markers if m in answer)
    return round(found / len(markers), 2)


def check_retrieval_relevance(citations: List[Dict], question: str) -> float:
    """Keyword overlap between question keywords and retrieved chunk text."""
    if not citations:
        return 0.0

    stop_words = {
        "what", "is", "the", "a", "an", "are", "were", "was", "how", "why",
        "when", "who", "which", "does", "do", "did", "in", "of", "to", "and",
        "or", "for", "with", "that", "this", "it", "its", "be", "been",
        "have", "has", "had", "from", "by", "at", "on", "about", "much",
        "many", "most", "some", "over", "under", "between", "into"
    }
    question_words = {
        w.lower().strip("?.,") for w in question.split()
        if w.lower().strip("?.,") not in stop_words and len(w) > 3
    }

    if not question_words:
        return 0.5

    scores = []
    for c in citations:
        chunk_text = c.get("text", "").lower()
        chunk_words = set(chunk_text.split())
        overlap = len(question_words & chunk_words)
        scores.append(min(overlap / len(question_words), 1.0))

    return round(sum(scores) / len(scores), 2)


def sep(char="─", width=66):
    print(char * width)


# ── Main evaluation ────────────────────────────────────────────────────────────

def run_evaluation(dataset_path: str = DATASET_PATH) -> Dict:

    # Verify API is up
    try:
        r = requests.get(f"{API_URL}/health", timeout=5)
        if r.status_code != 200:
            print(f"❌ API returned {r.status_code}. Start the server first.")
            return {}
        health = r.json()
        gen_ok = health.get("components", {}).get("generation", False)
        docs_resp = requests.get(f"{API_URL}/documents", timeout=5)
        docs_count = len(docs_resp.json()) if docs_resp.status_code == 200 else 0
        print(f"✓ API online | LLM: {'ready' if gen_ok else 'offline'} | "
              f"Indexed documents: {docs_count}")
        if docs_count == 0:
            print("⚠️  No documents indexed! Upload the PDF first.")
            return {}
    except Exception as e:
        print(f"❌ Cannot reach API: {e}")
        return {}

    dataset = load_dataset(dataset_path)
    os.makedirs(REPORTS_DIR, exist_ok=True)

    sep("═")
    print(f"  DocIQ Evaluation Suite — {len(dataset)} questions")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sep("═")
    print()

    results = []
    method_counts = {"llm": 0, "string_match": 0, "rule": 0}

    for i, item in enumerate(dataset):
        q_num   = f"[{i+1:02d}/{len(dataset)}]"
        cat     = item["category"].upper()
        q_short = item["question"][:52] + ("…" if len(item["question"]) > 52 else "")
        print(f"{q_num} {cat}: {q_short}")

        t0 = time.time()
        response = query_api(item["question"], top_k=3)
        latency = round((time.time() - t0) * 1000)

        if "error" in response:
            print(f"       ❌ {response['error']}\n")
            results.append({**item, "error": response["error"], "latency_ms": latency})
            continue

        answer    = response.get("answer", "")
        citations = response.get("citations", [])
        conf      = response.get("confidence", {})

        scored       = score_answer(item["question"], item["golden_answer"], answer)
        faithfulness = check_faithfulness(answer, citations)
        relevance    = check_retrieval_relevance(citations, item["question"])
        conf_score   = conf.get("score", 0.0)
        conf_tier    = conf.get("tier", "?")

        method_counts[scored.get("method", "string_match")] += 1

        result = {
            "id":                  item["id"],
            "category":            item["category"],
            "question":            item["question"],
            "golden_answer":       item["golden_answer"],
            "generated_answer":    answer[:300],
            "correctness":         scored["correctness"],
            "correctness_pct":     round(scored["correctness"] / 3 * 100, 1),
            "faithfulness":        faithfulness,
            "retrieval_relevance": relevance,
            "confidence_score":    conf_score,
            "confidence_tier":     conf_tier,
            "latency_ms":          latency,
            "judge_reasoning":     scored["reasoning"],
            "judge_method":        scored.get("method", "?")
        }
        results.append(result)

        icon   = "✓" if scored["correctness"] >= 2 else ("△" if scored["correctness"] == 1 else "✗")
        method = f"[{scored.get('method','?')[:2].upper()}]"
        print(
            f"       {icon} {method}  correct:{scored['correctness']}/3  "
            f"faith:{faithfulness:.0%}  rel:{relevance:.0%}  "
            f"conf:{conf_tier}({conf_score:.2f})  {latency}ms"
        )
        reasoning = scored.get("reasoning", "")
        if reasoning:
            print(f"         → {reasoning[:85]}")
        print()

    # ── Aggregate ──────────────────────────────────────────────────────────────
    valid = [r for r in results if "error" not in r]
    n = len(valid)

    if n == 0:
        print("❌ No valid results to aggregate.")
        return {}

    avg_correct = sum(r["correctness"] for r in valid) / (n * 3)
    avg_faith   = sum(r["faithfulness"] for r in valid) / n
    avg_rel     = sum(r["retrieval_relevance"] for r in valid) / n
    avg_conf    = sum(r["confidence_score"] for r in valid) / n
    avg_lat     = sum(r["latency_ms"] for r in valid) / n

    cats: Dict[str, List[float]] = {}
    for r in valid:
        cats.setdefault(r["category"], []).append(r["correctness"] / 3)
    cat_scores = {c: round(sum(s) / len(s) * 100, 1) for c, s in cats.items()}

    # ── Print summary ──────────────────────────────────────────────────────────
    sep("═")
    print("  EVALUATION SUMMARY")
    sep("═")
    print(f"  Questions evaluated  : {n}/{len(dataset)}")
    print(f"  Answer Correctness   : {avg_correct:.1%}")
    print(f"  Faithfulness         : {avg_faith:.1%}")
    print(f"  Retrieval Relevance  : {avg_rel:.1%}")
    print(f"  Avg Confidence       : {avg_conf:.3f}")
    print(f"  Avg Latency          : {round(avg_lat)}ms")
    print()
    print("  By Category:")
    for cat, score in sorted(cat_scores.items()):
        bar = "█" * int(score / 5)
        print(f"    {cat:<16} {score:>5.1f}%  {bar}")
    print()
    print("  Judge methods used:")
    for method, count in method_counts.items():
        if count > 0:
            print(f"    {method:<16} {count} questions")
    sep("─")

    # ── Save report ────────────────────────────────────────────────────────────
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_questions": len(dataset),
        "evaluated": n,
        "summary": {
            "answer_correctness_pct":  round(avg_correct * 100, 1),
            "faithfulness_pct":        round(avg_faith * 100, 1),
            "retrieval_relevance_pct": round(avg_rel * 100, 1),
            "avg_confidence":          round(avg_conf, 3),
            "avg_latency_ms":          round(avg_lat)
        },
        "by_category": cat_scores,
        "judge_methods": method_counts,
        "results": results
    }

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(REPORTS_DIR, f"eval_{ts}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n  Report saved → {path}")
    sep("═")
    return report


if __name__ == "__main__":
    run_evaluation()