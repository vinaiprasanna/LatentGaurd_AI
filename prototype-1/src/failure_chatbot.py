"""Fast, deterministic COSMO operator for BurnInGuard AI.

COSMO = Component Observation & Screening Monitoring Operator.
It uses the pipeline's actual results and performs safe, read-only analysis tasks.
No external LLM/API is required.
"""
import math
import re

PARAM_LABELS = {
    "iddq_uA": "IDDQ current",
    "leakage_uA": "leakage current",
    "delay_ns": "propagation delay",
}


def _num(row, key, default=0.0):
    try:
        value = float(row.get(key, default))
        return value if math.isfinite(value) else default
    except (TypeError, ValueError):
        return default


def _pct_change(row, p):
    start = _num(row, f"{p}_0h")
    last = _num(row, f"{p}_last")
    if abs(start) < 1e-12:
        return 0.0
    return (last - start) / abs(start) * 100.0


def _dut_id_from_question(question, results):
    q = question or ""
    ids = [] if results is None else [str(x) for x in results.get("dut_id", [])]
    for dut in ids:
        if re.search(rf"(?<![A-Za-z0-9]){re.escape(dut)}(?![A-Za-z0-9])", q, re.I):
            return dut
    return None


def explain_dut(row):
    band = str(row.get("risk_band", "UNKNOWN"))
    score = _num(row, "risk_score")
    confidence = _num(row, "risk_confidence_pct")
    anomaly = _num(row, "anomaly_ensemble_score")
    changes = {p: _pct_change(row, p) for p in PARAM_LABELS}
    largest_p = max(changes, key=lambda p: abs(changes[p]))
    margin_items = []
    for p, label in PARAM_LABELS.items():
        margin = _num(row, f"{p}_margin_pct_500h", 100.0)
        projected = _num(row, f"{p}_projected_500h")
        margin_items.append((margin, p, label, projected))
    margin_items.sort(key=lambda x: x[0])
    lines = [
        f"**{row.get('dut_id', 'Selected DUT')}** is currently **{band} risk** with a risk score of **{score:.1f}/100** and confidence of **{confidence:.0f}%**.",
        f"The anomaly signal is **{anomaly:.2f}**. The largest relative change is **{PARAM_LABELS[largest_p]}** at **{changes[largest_p]:+.1f}%** from 0h to the latest checkpoint.",
    ]
    worst_margin, _, label, projected = margin_items[0]
    if worst_margin < 0:
        lines.append(f"At 500h, **{label}** is projected to be **{projected:.3g}**, beyond its configured limit.")
    else:
        lines.append(f"The tightest projected 500h margin is **{label}** at **{worst_margin:.1f}%**.")
    explanation = str(row.get("explanation", "")).strip()
    if explanation:
        lines.append(f"Pipeline explanation: {explanation}")
    return "\n\n".join(lines)


def _list_duts(results, bands):
    subset = results[results["risk_band"].isin(bands)].sort_values("risk_score", ascending=False)
    if subset.empty:
        return "No DUTs match that condition."
    lines = [f"### 📋 DUT List ({len(subset)})"]
    for i, (_, item) in enumerate(subset.iterrows(), 1):
        lines.append(f"{i}. **{item['dut_id']}** — **{item['risk_band']}** — Score **{_num(item, 'risk_score'):.1f}/100** — Confidence **{_num(item, 'risk_confidence_pct'):.0f}%**")
    return "\n".join(lines)


def fleet_summary(results):
    total = len(results)
    counts = results["risk_band"].value_counts()
    low, medium = int(counts.get("LOW", 0)), int(counts.get("MEDIUM", 0))
    high, critical = int(counts.get("HIGH", 0)), int(counts.get("CRITICAL", 0))
    risky = high + critical
    pct = risky / total * 100 if total else 0
    return (f"### 🏭 Fleet Summary\n\n**{total} DUTs** total.\n\n"
            f"- 🟢 LOW: **{low}**\n- 🟡 MEDIUM: **{medium}**\n- 🟠 HIGH: **{high}**\n- 🔴 CRITICAL: **{critical}**\n\n"
            f"**Risky (HIGH + CRITICAL): {risky} ({pct:.1f}%)**")


def _compare_duts(results, ids):
    if len(ids) < 2:
        return "Please provide two DUT IDs, for example: **Compare IC0001 and IC0010**."
    rows = results[results["dut_id"].astype(str).isin(ids)].copy()
    if len(rows) < 2:
        return "I could not find both DUTs in the current results."
    rows = rows.sort_values("risk_score", ascending=False)
    lines = ["### 🔬 DUT Comparison"]
    for _, r in rows.iterrows():
        lines.append(f"- **{r['dut_id']}** — {r['risk_band']} risk, score **{_num(r, 'risk_score'):.1f}**, confidence **{_num(r, 'risk_confidence_pct'):.0f}%**, lot **{r['lot_id']}**")
    winner = rows.iloc[0]
    lines.append(f"\n**Highest risk:** {winner['dut_id']} ({winner['risk_band']}, {_num(winner, 'risk_score'):.1f}/100).")
    return "\n".join(lines)


def _lot_analysis(results):
    g = results.groupby("lot_id").agg(
        DUTs=("dut_id", "count"),
        Avg_Risk=("risk_score", "mean"),
        Critical=("risk_band", lambda s: int((s == "CRITICAL").sum())),
        High=("risk_band", lambda s: int((s == "HIGH").sum())),
    ).reset_index()
    g["Risky"] = g["Critical"] + g["High"]
    g = g.sort_values(["Risky", "Avg_Risk"], ascending=False)
    lines = ["### 🏭 Lot Risk Analysis"]
    for _, r in g.iterrows():
        lines.append(f"- **{r['lot_id']}** — {int(r['DUTs'])} DUTs, **{int(r['Risky'])} risky**, average risk **{r['Avg_Risk']:.1f}**")
    return "\n".join(lines)


def _short_explanation(row):
    band = str(row.get("risk_band", "UNKNOWN"))
    score = _num(row, "risk_score")
    changes = {p: _pct_change(row, p) for p in PARAM_LABELS}
    p = max(changes, key=lambda x: abs(changes[x]))
    return (f"**{row.get('dut_id', 'Selected DUT')}** is **{band} risk** with a score of **{score:.1f}/100**.\n\n"
            f"The strongest monitored change is **{PARAM_LABELS[p]}** at **{changes[p]:+.1f}%**.")


def answer_question(question, row, results=None, chat_history=None):
    q = (question or "").lower().strip()

    greetings = {"hi", "hello", "hey", "hii", "helo", "good morning", "good afternoon", "good evening"}
    if q in greetings or q in {"hi cosmo", "hello cosmo", "hey cosmo"}:
        return "Hello! I’m **COSMO**, your BurnInGuard AI assistant.\n\nI can analyze DUTs, compare components, find risky devices, check 500h projections, summarize lots, and generate reports."

    if not q:
        return "Ask COSMO to **analyze a DUT**, **compare DUTs**, **find risky DUTs**, **check 500h**, or **summarize the fleet**."

    # Explicit task commands.
    if results is not None:
        if any(x in q for x in ["fleet summary", "fleet status", "summary of fleet", "whole fleet", "entire fleet"]):
            return fleet_summary(results)
        if any(x in q for x in ["which lot", "lot has", "lot analysis", "lot risk", "worst lot"]):
            return _lot_analysis(results)
        if any(x in q for x in ["highest risk", "worst dut", "most risky dut", "top risky dut"]):
            r = results.sort_values("risk_score", ascending=False).iloc[0]
            return f"### 🚨 Highest-Risk DUT\n\n**{r['dut_id']}** is **{r['risk_band']}** with a score of **{_num(r, 'risk_score'):.1f}/100** and confidence **{_num(r, 'risk_confidence_pct'):.0f}%**."
        if "compare" in q:
            ids = re.findall(r"\b[A-Za-z]+\d+\b", question or "")
            return _compare_duts(results, list(dict.fromkeys(ids))[:2])

        total = len(results)
        counts = results["risk_band"].value_counts()
        low, medium = int(counts.get("LOW", 0)), int(counts.get("MEDIUM", 0))
        high, critical = int(counts.get("HIGH", 0)), int(counts.get("CRITICAL", 0))
        risky = high + critical
        if any(x in q for x in ["list", "show", "which dut", "which duts", "give me the duts", "names of", "them", "those"]):
            previous_question = ""
            if chat_history:
                for previous in reversed(chat_history):
                    if isinstance(previous, dict):
                        previous_question = str(previous.get("user", "")).lower()
                    elif isinstance(previous, (tuple, list)) and previous:
                        previous_question = str(previous[0]).lower()
                    if previous_question:
                        break
            combined = q + " " + previous_question
            if "critical" in combined: return _list_duts(results, ["CRITICAL"])
            if "high" in combined and "risky" not in combined: return _list_duts(results, ["HIGH"])
            if "medium" in combined: return _list_duts(results, ["MEDIUM"])
            if "low" in combined or "good" in combined or "normal" in combined: return _list_duts(results, ["LOW"])
            if any(x in combined for x in ["risky", "risk", "defect", "failure"]): return _list_duts(results, ["HIGH", "CRITICAL"])
        if any(x in q for x in ["how many", "number of", "count", "total"]):
            if "critical" in q: return f"There are **{critical} CRITICAL-risk DUTs** out of **{total} total DUTs**."
            if "high" in q: return f"There are **{high} HIGH-risk DUTs** out of **{total} total DUTs**."
            if "medium" in q: return f"There are **{medium} MEDIUM-risk DUTs** out of **{total} total DUTs**."
            if "normal" in q or "good" in q: return f"There are **{low} LOW-risk (normal) DUTs** out of **{total} total DUTs**."
            return f"There are **{risky} HIGH/CRITICAL-risk DUTs** out of **{total} total DUTs** ({risky / total * 100:.1f}%)."

    # If the user names a DUT, use it for the task where possible.
    named = _dut_id_from_question(question, results)
    if named and results is not None:
        row = results[results["dut_id"].astype(str) == named].iloc[0]

    brief = any(term in q for term in ["2 lines", "two lines", "2 line", "three lines", "3 lines", "brief", "short explanation", "in short"])
    if brief and any(word in q for word in ["explain", "why", "reason", "risk"]):
        return _short_explanation(row)

    if any(word in q for word in ["500", "future", "projection", "predict", "forecast"]):
        parts = []
        for p, label in PARAM_LABELS.items():
            value = _num(row, f"{p}_projected_500h")
            margin = _num(row, f"{p}_margin_pct_500h")
            parts.append(f"**{label}**: projected {value:.3g}, remaining margin {margin:.1f}%")
        return "At the **500h digital-twin projection**:\n\n" + "\n\n".join(parts)

    if any(word in q for word in ["parameter", "iddq", "leakage", "delay", "which parameter"]):
        changes = {p: _pct_change(row, p) for p in PARAM_LABELS}
        p = max(changes, key=lambda x: abs(changes[x]))
        return (f"The strongest parameter change is **{PARAM_LABELS[p]}**: {changes[p]:+.1f}% from 0h to the latest checkpoint.\n\n"
                f"IDDQ: {changes['iddq_uA']:+.1f}%\nLeakage: {changes['leakage_uA']:+.1f}%\nDelay: {changes['delay_ns']:+.1f}%")

    if any(word in q for word in ["score", "confidence", "model", "algorithm"]):
        return (f"Risk score: **{_num(row, 'risk_score'):.1f}/100**\n\nRisk band: **{row.get('risk_band', 'UNKNOWN')}**\n\n"
                f"Confidence: **{_num(row, 'risk_confidence_pct'):.0f}%**\n\nAnomaly score: **{_num(row, 'anomaly_ensemble_score'):.2f}**")

    if any(word in q for word in ["why", "reason", "cause", "risk", "flag", "defect"]):
        return explain_dut(row)

    return ("I can perform these tasks: **analyze a DUT**, **compare two DUTs**, **find the highest-risk DUT**, "
            "**list risky DUTs**, **analyze lots**, **summarize the fleet**, or **check 500h projections**.")
