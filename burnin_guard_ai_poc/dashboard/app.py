"""
BurnInGuard AI 2.0 -- PoC Dashboard (Streamlit)

Run with:
    streamlit run dashboard/app.py

Reads outputs/results.csv and outputs/audit_log.csv, which are produced
by src/pipeline.py. If they don't exist yet, the dashboard offers a
one-click button to generate them.
"""
import os
import sys
import json

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
OUT_DIR = os.path.join(ROOT, "outputs")
sys.path.insert(0, SRC)

st.set_page_config(page_title="BurnInGuard AI 2.0", layout="wide",
                    page_icon="\U0001F6E1\uFE0F")

RISK_COLORS = {"LOW": "#1B7A43", "MEDIUM": "#B8860B", "HIGH": "#D2691E", "CRITICAL": "#B23A48"}
PARAMS = ["iddq_uA", "leakage_uA", "delay_ns"]
STATIC_LIMITS = {"iddq_uA": 50.0, "leakage_uA": 10.0, "delay_ns": 8.0}
CHECKPOINTS_H = [0, 24, 96, 168]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_results():
    path = os.path.join(OUT_DIR, "results.csv")
    if not os.path.exists(path):
        return None
    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def load_raw():
    path = os.path.join(ROOT, "data", "synthetic_burnin_data.csv")
    if not os.path.exists(path):
        return None
    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def load_audit_log():
    path = os.path.join(OUT_DIR, "audit_log.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path)


def run_pipeline_now():
    from pipeline import run_pipeline
    with st.spinner("Running full BurnInGuard AI pipeline (data \u2192 features \u2192 "
                     "ensemble \u2192 drift model \u2192 risk fusion) ..."):
        run_pipeline(verbose=False)
    st.cache_data.clear()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    "<h1 style='margin-bottom:0'>\U0001F6E1\uFE0F BurnInGuard AI 2.0</h1>"
    "<p style='color:#666;margin-top:0'>Physics-informed, explainable, uncertainty-aware "
    "anomaly detection for component burn-in &amp; screening &mdash; SIH 2026 PoC</p>",
    unsafe_allow_html=True,
)

results = load_results()
raw = load_raw()

if results is None:
    st.warning("No results found yet. Click below to run the full pipeline on freshly "
               "generated synthetic burn-in data.")
    if st.button("\u25B6\uFE0F Run BurnInGuard AI pipeline now", type="primary"):
        run_pipeline_now()
        st.rerun()
    st.stop()

with st.sidebar:
    st.header("Controls")
    if st.button("\U0001F504 Regenerate data & re-run pipeline"):
        run_pipeline_now()
        st.rerun()
    st.caption("Synthetic demonstration data only \u2014 never present as real test data.")
    st.divider()
    lot_filter = st.multiselect("Filter by lot", sorted(results["lot_id"].unique()),
                                 default=sorted(results["lot_id"].unique()))
    band_filter = st.multiselect("Filter by risk band", ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                                  default=["LOW", "MEDIUM", "HIGH", "CRITICAL"])

view = results[results["lot_id"].isin(lot_filter) & results["risk_band"].isin(band_filter)]

# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total DUTs", len(results))
k2.metric("Normal (LOW)", int((results["risk_band"] == "LOW").sum()))
k3.metric("Medium", int((results["risk_band"] == "MEDIUM").sum()))
k4.metric("High", int((results["risk_band"] == "HIGH").sum()))
k5.metric("Critical", int((results["risk_band"] == "CRITICAL").sum()),
          delta=None, delta_color="inverse")

st.divider()

tab_heatmap, tab_trend, tab_twin, tab_explain, tab_audit, tab_eval = st.tabs(
    ["\U0001F525 Live Risk Heatmap", "\U0001F4C8 Parameter Trends", "\U0001F9EC Digital Twin",
     "\U0001F4A1 Explainability", "\U0001F4CB Audit Log", "\U0001F4CA Model Evaluation"]
)

# ---------------------------------------------------------------------------
# TAB 1: Risk heatmap
# ---------------------------------------------------------------------------
with tab_heatmap:
    st.subheader("Fleet Risk Heatmap")
    st.caption("Each cell is one DUT under burn-in, colour-coded by fused risk score.")

    n_cols = 20
    grid_df = view.sort_values(["lot_id", "dut_id"]).reset_index(drop=True)
    n = len(grid_df)
    n_rows = int(np.ceil(n / n_cols))

    fig = go.Figure()
    xs, ys, colors, texts = [], [], [], []
    for i, row in grid_df.iterrows():
        xs.append(i % n_cols)
        ys.append(-(i // n_cols))
        colors.append(row["risk_score"])
        texts.append(
            f"{row['dut_id']} ({row['lot_id']})<br>Risk: {row['risk_score']:.1f} "
            f"({row['risk_band']})<br>Confidence: {row['risk_confidence_pct']:.0f}%"
        )
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="markers",
        marker=dict(size=22, color=colors, colorscale=[[0, "#1B7A43"], [0.3, "#B8860B"],
                                                         [0.6, "#D2691E"], [1.0, "#B23A48"]],
                    cmin=0, cmax=100, colorbar=dict(title="Risk"), line=dict(width=1, color="white")),
        text=texts, hoverinfo="text",
    ))
    fig.update_layout(height=max(320, 40 * n_rows), showlegend=False,
                       xaxis=dict(visible=False), yaxis=dict(visible=False),
                       margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("DUT Table")
    show_cols = ["dut_id", "lot_id", "risk_score", "risk_band", "risk_confidence_pct",
                 "anomaly_ensemble_score", "explanation"]
    st.dataframe(
        view[show_cols].sort_values("risk_score", ascending=False).rename(columns={
            "dut_id": "DUT ID", "lot_id": "Lot", "risk_score": "Risk Score",
            "risk_band": "Risk Band", "risk_confidence_pct": "Confidence %",
            "anomaly_ensemble_score": "Anomaly Score", "explanation": "Why flagged?",
        }),
        use_container_width=True, height=380,
    )

# ---------------------------------------------------------------------------
# TAB 2: Parameter trend view
# ---------------------------------------------------------------------------
with tab_trend:
    st.subheader("Parameter vs. Time (with predicted trajectory & confidence interval)")
    dut_choice = st.selectbox("Select DUT", view.sort_values("risk_score", ascending=False)["dut_id"])
    row = results[results["dut_id"] == dut_choice].iloc[0]
    dut_raw = raw[raw["dut_id"] == dut_choice].sort_values("checkpoint_h") if raw is not None else None

    cols = st.columns(3)
    for i, p in enumerate(PARAMS):
        with cols[i]:
            fig = go.Figure()
            if dut_raw is not None:
                fig.add_trace(go.Scatter(x=dut_raw["checkpoint_h"], y=dut_raw[p],
                                          mode="lines+markers", name="Measured",
                                          line=dict(color="#13315C", width=2)))
            pred = row[f"{p}_pred_168h"]
            lo = row[f"{p}_pred_168h_lo"]
            hi = row[f"{p}_pred_168h_hi"]
            fig.add_trace(go.Scatter(x=[168], y=[pred], mode="markers", name="Predicted 168h",
                                      marker=dict(color="#1E88E5", size=10, symbol="diamond")))
            fig.add_trace(go.Scatter(x=[168, 168], y=[lo, hi], mode="lines", name="90% interval",
                                      line=dict(color="#1E88E5", width=6), opacity=0.35))
            fig.add_hline(y=STATIC_LIMITS[p], line_dash="dash", line_color="#B23A48",
                          annotation_text="Static limit")
            fig.update_layout(title=p, height=300, margin=dict(l=10, r=10, t=40, b=10),
                              xaxis_title="Hours", yaxis_title=p, showlegend=(i == 0))
            st.plotly_chart(fig, use_container_width=True)

    st.info(f"**Risk:** {row['risk_band']} ({row['risk_score']:.1f}/100, "
            f"{row['risk_confidence_pct']:.0f}% confidence)  \n**Why:** {row['explanation']}")

# ---------------------------------------------------------------------------
# TAB 3: Digital twin
# ---------------------------------------------------------------------------
with tab_twin:
    st.subheader("Digital Twin \u2014 Projected Behaviour Beyond Burn-In")
    dut_choice2 = st.selectbox("Select DUT for projection", view.sort_values("risk_score", ascending=False)["dut_id"],
                                key="twin_select")
    row2 = results[results["dut_id"] == dut_choice2].iloc[0]

    cols = st.columns(3)
    for i, p in enumerate(PARAMS):
        with cols[i]:
            projected_500h = row2[f"{p}_projected_500h"]
            margin_pct = row2[f"{p}_margin_pct_500h"]
            limit = STATIC_LIMITS[p]
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=projected_500h,
                title={"text": f"{p}<br><span style='font-size:0.7em'>projected @ 500h</span>"},
                gauge={"axis": {"range": [0, limit * 1.5]},
                       "bar": {"color": "#B23A48" if projected_500h > limit else "#1E88E5"},
                       "steps": [{"range": [0, limit], "color": "#EAF2FB"},
                                 {"range": [limit, limit * 1.5], "color": "#FDECEA"}],
                       "threshold": {"line": {"color": "#B23A48", "width": 4},
                                     "thickness": 0.85, "value": limit}},
            ))
            fig.update_layout(height=260, margin=dict(l=10, r=10, t=60, b=10))
            st.plotly_chart(fig, use_container_width=True)
            st.caption(f"Remaining margin vs. static limit at 500h: **{margin_pct:.1f}%** "
                       f"(limit = {limit}).")

    st.caption(
        "Digital twin projection re-applies the DUT's physics-normalised drift rate, scaled "
        "by its Arrhenius temperature-acceleration factor, to estimate behaviour beyond the "
        "end of the burn-in window. This is a simplified analytical PoC projection, not a "
        "full physics simulator."
    )

# ---------------------------------------------------------------------------
# TAB 4: Explainability
# ---------------------------------------------------------------------------
with tab_explain:
    st.subheader("Explainability Panel")
    flagged = view[view["risk_band"].isin(["HIGH", "CRITICAL"])].sort_values("risk_score", ascending=False)
    if flagged.empty:
        st.success("No HIGH / CRITICAL DUTs in the current filter selection.")
    else:
        for _, r in flagged.head(10).iterrows():
            with st.expander(f"{r['dut_id']}  ({r['lot_id']})  \u2014  "
                              f"Risk {r['risk_score']:.1f} [{r['risk_band']}]  "
                              f"\u2014  {r['risk_confidence_pct']:.0f}% confidence"):
                comp_cols = ["_component_anomaly", "_component_lot_deviation",
                             "_component_drift_rate", "_component_future_margin"]
                comp_labels = ["Anomaly Ensemble", "Lot Deviation", "Drift Rate", "Future Margin"]
                comp_vals = [r[c] for c in comp_cols]
                fig = go.Figure(go.Bar(x=comp_vals, y=comp_labels, orientation="h",
                                        marker_color="#1E88E5"))
                fig.update_layout(height=180, margin=dict(l=10, r=10, t=10, b=10),
                                  xaxis=dict(range=[0, 1], title="Contribution (0-1)"))
                st.plotly_chart(fig, use_container_width=True)
                st.write(f"**Explanation:** {r['explanation']}")

    st.divider()
    st.subheader("Global Feature Importance (Drift Models)")
    shap_path = os.path.join(OUT_DIR, "shap_feature_importance.json")
    if os.path.exists(shap_path):
        with open(shap_path) as f:
            shap_report = json.load(f)
        for p, importances in shap_report.items():
            if not importances:
                continue
            imp_df = pd.DataFrame(list(importances.items()), columns=["feature", "importance"])
            imp_df = imp_df.sort_values("importance", ascending=True).tail(8)
            fig = px.bar(imp_df, x="importance", y="feature", orientation="h", title=f"{p} drift model")
            fig.update_layout(height=280, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("Run the pipeline to generate SHAP / feature-importance reports.")

# ---------------------------------------------------------------------------
# TAB 5: Audit log
# ---------------------------------------------------------------------------
with tab_audit:
    st.subheader("Immutable Audit / Traceability Log")
    st.caption("Every HIGH / CRITICAL flag raised by the current pipeline run.")
    audit = load_audit_log()
    if audit.empty:
        st.info("No HIGH / CRITICAL flags recorded in the current run.")
    else:
        st.dataframe(audit, use_container_width=True, height=400)
        st.download_button("Download audit log (CSV)", audit.to_csv(index=False),
                            file_name="burnin_guard_audit_log.csv")

# ---------------------------------------------------------------------------
# TAB 6: Model evaluation
# ---------------------------------------------------------------------------
with tab_eval:
    st.subheader("Offline Evaluation vs. Synthetic Ground Truth")
    st.caption(
        "This tab is only possible because the demo uses synthetic data with known "
        "injected anomalies. A real deployment would not have ground-truth labels at "
        "inference time \u2014 this view exists purely to validate the PoC."
    )
    eval_path = os.path.join(OUT_DIR, "evaluation_report.txt")
    if os.path.exists(eval_path):
        with open(eval_path) as f:
            st.code(f.read())
    if "true_latent_defect" in results.columns:
        fig = px.scatter(results, x="risk_score", y="anomaly_ensemble_score",
                          color=results["true_latent_defect"].map({0: "Normal", 1: "Injected Latent Defect"}),
                          hover_data=["dut_id", "lot_id", "risk_band"],
                          color_discrete_map={"Normal": "#1B7A43", "Injected Latent Defect": "#B23A48"},
                          title="Risk Score vs. Anomaly Ensemble Score, coloured by ground truth")
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)
