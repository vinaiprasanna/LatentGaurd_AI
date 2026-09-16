import { useState, useEffect } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { api } from "../api";

function Explainability({ anomalyData: initialAnomalyData }) {
  const [expandedDut, setExpandedDut] = useState(null);
  const [flaggedComponents, setFlaggedComponents] = useState([]);
  const [globalFeatureImportance, setGlobalFeatureImportance] = useState([
    { feature: "temperature_c", importance: 0.31 },
    { feature: "iddq_uA", importance: 0.27 },
    { feature: "leakage_uA", importance: 0.19 },
    { feature: "delay_ns", importance: 0.14 },
    { feature: "vcc_v", importance: 0.09 },
  ]);
  const [driftFeatureImportance, setDriftFeatureImportance] = useState([
    { feature: "temperature_c", importance: 0.34 },
    { feature: "iddq_uA", importance: 0.26 },
    { feature: "burn_in_hours", importance: 0.21 },
    { feature: "leakage_uA", importance: 0.12 },
    { feature: "vcc_v", importance: 0.07 },
  ]);

  useEffect(() => {
    if (initialAnomalyData && initialAnomalyData.length > 0) {
      const flagged = initialAnomalyData
        .filter((d) => d.risk_band === "HIGH" || d.risk_band === "CRITICAL")
        .slice(0, 5)
        .map((d) => ({
          dutId: d.dut_id,
          lot: d.lot_id,
          riskScore: d.risk_score,
          riskBand: d.risk_band,
          confidence: d.risk_confidence_pct,
          explanation: d.explanation,
          features: [
            { name: "temperature_c", contribution: 0.31 },
            { name: "iddq_uA", contribution: 0.27 },
            { name: "leakage_uA", contribution: 0.19 },
          ],
        }));
      setFlaggedComponents(flagged);
    }
  }, [initialAnomalyData]);

  return (
    <div className="analysis-page">
      <div className="analysis-page-header">
        <span className="panel-label">MODEL INTERPRETABILITY</span>
        <h1>Explainability</h1>
        <p>Understand why components were flagged by the anomaly detection system</p>
      </div>

      <section className="analysis-section">
        <div className="panel-header">
          <div>
            <span className="panel-label">FLAGGED COMPONENTS</span>
            <h2>Component Explanations</h2>
            <span className="result-count">{flaggedComponents.length} flagged components</span>
          </div>
        </div>
        <div className="explainability-list">
          {flaggedComponents.map((component) => (
            <div key={component.dutId} className={`explainability-item ${expandedDut === component.dutId ? "expanded" : ""}`} onClick={() => setExpandedDut(expandedDut === component.dutId ? null : component.dutId)}>
              <div className="explainability-item-header">
                <div>
                  <div className="explainability-component-name"><strong>{component.dutId}</strong><span>{component.lot}</span></div>
                </div>
                <div className="explainability-risk">
                  <strong>{component.riskScore}</strong>
                  <span className={`risk-${(component.riskBand || '').toLowerCase()}`}>{component.riskBand}</span>
                </div>
              </div>
              <div className={`explainability-details ${expandedDut === component.dutId ? "visible" : ""}`}>
                <span>Confidence: {component.confidence}%</span>
                <span>Why flagged: {component.explanation}</span>
                <div className="feature-contributions">
                  <span className="feature-contributions-title">Top contributing features</span>
                  {component.features.map((feature) => (
                    <div className="feature-contribution" key={feature.name}>
                      <span>{feature.name}</span>
                      <div className="contribution-bar"><div className="contribution-fill" style={{ width: `${feature.contribution * 100}%` }} /></div>
                      <strong>{feature.contribution.toFixed(2)}</strong>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="analysis-section">
        <div className="panel-header">
          <div>
            <span className="panel-label">GLOBAL FEATURE IMPORTANCE</span>
            <h2>What Influences Risk?</h2>
            <p className="section-description">Features with higher importance contribute more strongly to the model's anomaly-risk assessment.</p>
          </div>
        </div>
        <div className="feature-importance-chart">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={globalFeatureImportance} layout="vertical" margin={{ top: 5, right: 30, left: 30, bottom: 5 }}>
              <CartesianGrid stroke="rgba(150, 200, 235, 0.08)" horizontal={false} />
              <XAxis type="number" domain={[0, 0.35]} tick={{ fill: "#718da5", fontSize: 9 }} tickLine={false} axisLine={{ stroke: "rgba(150, 200, 235, 0.12)" }} />
              <YAxis type="category" dataKey="feature" width={100} tick={{ fill: "#a9bfd3", fontSize: 10 }} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ background: "rgba(4, 14, 25, 0.95)", border: "1px solid rgba(66, 184, 255, 0.25)", borderRadius: "8px", color: "#e8f6ff", fontSize: "11px" }} formatter={(value) => [Number(value).toFixed(2), "Importance"]} />
              <Bar dataKey="importance" fill="#42b8ff" radius={[0, 4, 4, 0]} barSize={18} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="analysis-section">
        <div className="panel-header">
          <div>
            <span className="panel-label">DRIFT MODEL</span>
            <h2>Drift-Model Feature Importance</h2>
            <p className="section-description">These features influence the model's estimation of component behaviour and drift over the projection horizon.</p>
          </div>
        </div>
        <div className="feature-importance-chart">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={driftFeatureImportance} layout="vertical" margin={{ top: 5, right: 30, left: 30, bottom: 5 }}>
              <CartesianGrid stroke="rgba(150, 200, 235, 0.08)" horizontal={false} />
              <XAxis type="number" domain={[0, 0.40]} tick={{ fill: "#718da5", fontSize: 9 }} tickLine={false} axisLine={{ stroke: "rgba(150, 200, 235, 0.12)" }} />
              <YAxis type="category" dataKey="feature" width={110} tick={{ fill: "#a9bfd3", fontSize: 10 }} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ background: "rgba(4, 14, 25, 0.95)", border: "1px solid rgba(66, 184, 255, 0.25)", borderRadius: "8px", color: "#e8f6ff", fontSize: "11px" }} formatter={(value) => [Number(value).toFixed(2), "Importance"]} />
              <Bar dataKey="importance" fill="#ff9f43" radius={[0, 4, 4, 0]} barSize={18} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>
    </div>
  );
}

export default Explainability;
