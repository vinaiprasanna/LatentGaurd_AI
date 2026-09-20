import { useState, useEffect } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { api } from "../api";

function Explainability({ anomalyData: initialAnomalyData }) {
  const [expandedDut, setExpandedDut] = useState(null);
  const [modelMetrics, setModelMetrics] = useState(null);
  const [metricsError, setMetricsError] = useState('');

  useEffect(() => {
    api.getModelMetrics()
      .then(setModelMetrics)
      .catch((error) => setMetricsError(error.message || 'Model metrics unavailable'));
  }, []);

  const globalFeatureImportance = modelMetrics?.anomaly_feature_importance || [];
  const driftFeatureImportance = modelMetrics?.drift_feature_importance?.iddq_uA || [];
  const flaggedComponents = (initialAnomalyData || [])
      .filter((d) => d.anomaly_decision === "ANOMALY" || d.risk_band === "HIGH" || d.risk_band === "CRITICAL")
        .slice(0, 5)
        .map((d) => ({
          dutId: d.dut_id,
          lot: d.lot_id,
          riskScore: d.risk_score,
          riskBand: d.risk_band,
          confidence: d.risk_confidence_pct,
          explanation: d.explanation,
          evidence: d.evidence_chain,
          recommendedTest: d.recommended_confirmation_test,
          counterfactual: d.thermal_counterfactual,
          features: [
            { name: 'Ensemble anomaly', contribution: Number(d._component_anomaly || 0) },
            { name: 'Future safety margin', contribution: Number(d._component_future_margin || 0) },
            { name: 'Lot deviation', contribution: Number(d._component_lot_deviation || 0) },
            { name: 'Drift rate', contribution: Number(d._component_drift_rate || 0) },
          ].sort((a, b) => b.contribution - a.contribution),
        }));
  return (
    <div className="analysis-page">
      <div className="analysis-page-header">
        <span className="panel-label">MODEL INTERPRETABILITY</span>
        <h1>Explainability</h1>
        <p>Understand why components were flagged by the anomaly detection system</p>
      </div>

      <section className="analysis-section model-metrics-section">
        <div className="panel-header">
          <div>
            <span className="panel-label">MODEL EVALUATION</span>
            <h2>Loaded Model Diagnostics</h2>
            <p className="section-description">These are in-sample training diagnostics. The current prediction CSV is inference input, not an independent labeled validation set.</p>
          </div>
        </div>
        {metricsError && <p className="upload-error">{metricsError}</p>}
        {modelMetrics?.metrics_available && (
          <div className="model-metrics-grid">
            <div className="model-info-item"><span>Features Used</span><strong>{modelMetrics.feature_count}</strong></div>
            <div className="model-info-item"><span>Recommended Threshold</span><strong>{modelMetrics.recommended_anomaly_threshold ?? '--'}</strong></div>
            <div className="model-info-item"><span>Training DUTs</span><strong>{modelMetrics.training_duts}</strong></div>
            <div className="model-info-item"><span>Training Accuracy</span><strong>{modelMetrics.anomaly.accuracy != null ? `${(modelMetrics.anomaly.accuracy * 100).toFixed(1)}%` : '--'}</strong></div>
            <div className="model-info-item"><span>Training F1</span><strong>{modelMetrics.anomaly.f1 != null ? `${(modelMetrics.anomaly.f1 * 100).toFixed(1)}%` : '--'}</strong></div>
            <div className="model-info-item"><span>IDDQ Drift R2</span><strong>{modelMetrics.drift.iddq_uA?.r2 ?? '--'}</strong></div>
            <div className="model-info-item"><span>Leakage Drift R2</span><strong>{modelMetrics.drift.leakage_uA?.r2 ?? '--'}</strong></div>
            <div className="model-info-item"><span>Delay Drift R2</span><strong>{modelMetrics.drift.delay_ns?.r2 ?? '--'}</strong></div>
          </div>
        )}
        {modelMetrics?.validation_available && modelMetrics.validation && (
          <div className="model-test-results">
            <p className="section-description">Held-out validation: {modelMetrics.validation.evaluation_scope}. Threshold policy: {modelMetrics.validation.threshold_policy}.</p>
            <div className="model-metrics-grid">
              <div className="model-info-item"><span>Validation Accuracy</span><strong>{(modelMetrics.validation.accuracy * 100).toFixed(1)}%</strong></div>
              <div className="model-info-item"><span>Validation Precision</span><strong>{(modelMetrics.validation.precision * 100).toFixed(1)}%</strong></div>
              <div className="model-info-item"><span>Validation Recall</span><strong>{(modelMetrics.validation.recall * 100).toFixed(1)}%</strong></div>
              <div className="model-info-item"><span>Validation F1</span><strong>{(modelMetrics.validation.f1 * 100).toFixed(1)}%</strong></div>
              <div className="model-info-item"><span>False-Negative Rate</span><strong>{(modelMetrics.validation.false_negative_rate * 100).toFixed(1)}%</strong></div>
            </div>
          </div>
        )}
        {modelMetrics?.drift_validation?.available && (
          <div className="model-test-results">
            <p className="section-description">Held-out drift validation: {modelMetrics.drift_validation.evaluation_scope}. Prediction interval coverage is measured against the actual 168-hour checkpoint.</p>
            <div className="model-metrics-grid">
              {['iddq_uA', 'leakage_uA', 'delay_ns'].map((parameter) => {
                const result = modelMetrics.drift_validation.parameters?.[parameter];
                return <div className="model-info-item" key={parameter}><span>{parameter} Holdout R2 / Coverage</span><strong>{result ? `${result.r2} / ${(result.interval_coverage * 100).toFixed(1)}%` : '--'}</strong></div>;
              })}
            </div>
          </div>
        )}
        {modelMetrics?.prediction_input && <p className="section-description model-evaluation-note">Prediction file: {modelMetrics.prediction_input.dut_count} DUTs, {modelMetrics.prediction_input.overlap_with_training_duts} overlap with training IDs. Validation accuracy is unavailable because the file has no labels.</p>}
        {modelMetrics?.test?.available ? (
          <div className="model-test-results">
            <p className="section-description">Uploaded test evaluation: {modelMetrics.test.test_duts} DUTs. Model weights were not retrained on this file.</p>
            {modelMetrics.test.anomaly_metrics_available && <div className="model-metrics-grid">
              <div className="model-info-item"><span>Test Accuracy</span><strong>{(modelMetrics.test.accuracy * 100).toFixed(1)}%</strong></div>
              <div className="model-info-item"><span>Test Precision</span><strong>{(modelMetrics.test.precision * 100).toFixed(1)}%</strong></div>
              <div className="model-info-item"><span>Test Recall</span><strong>{(modelMetrics.test.recall * 100).toFixed(1)}%</strong></div>
              <div className="model-info-item"><span>Test F1</span><strong>{(modelMetrics.test.f1 * 100).toFixed(1)}%</strong></div>
              <div className="model-info-item"><span>False-Negative Rate</span><strong>{(modelMetrics.test.false_negative_rate * 100).toFixed(1)}%</strong></div>
            </div>}
            {modelMetrics.test.drift_metrics_available && <div className="model-metrics-grid">
              {['iddq_uA', 'leakage_uA', 'delay_ns'].map((parameter) => {
                const result = modelMetrics.test.drift[parameter];
                return <div className="model-info-item" key={parameter}><span>{parameter} Test RMSE</span><strong>{result?.rmse ?? '--'}</strong></div>;
              })}
              {['iddq_uA', 'leakage_uA', 'delay_ns'].map((parameter) => {
                const result = modelMetrics.test.drift[parameter];
                return <div className="model-info-item" key={`${parameter}-coverage`}><span>{parameter} Interval Coverage</span><strong>{result?.interval_coverage != null ? `${(result.interval_coverage * 100).toFixed(1)}%` : '--'}</strong></div>;
              })}
            </div>}
            <p className="section-description model-evaluation-note">Training DUT overlap: {modelMetrics.test.overlap_with_training_duts}. Independent test: {modelMetrics.test.is_independent_test ? 'yes' : 'no'}.</p>
            {!modelMetrics.test.is_independent_test && <p className="section-description model-evaluation-note">Warning: some uploaded DUT IDs overlap with training data, so this is not a fully independent test.</p>}
          </div>
        ) : (
          <p className="section-description model-evaluation-note">Upload a labeled test CSV containing `true_latent_defect` to calculate test accuracy, precision, recall, F1, and false-negative rate. Current uploads are prediction-only.</p>
        )}
      </section>

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
                <div className="evidence-chain-block">
                  <span className="feature-contributions-title">Evidence chain</span>
                  <p>{component.evidence || 'Evidence details unavailable'}</p>
                </div>
                <div className="recommendation-block">
                  <span className="feature-contributions-title">Recommended confirmation test</span>
                  <p>{component.recommendedTest || 'Confirmation test unavailable'}</p>
                </div>
                <div className="counterfactual-block">
                  <span className="feature-contributions-title">Thermal counterfactual</span>
                  <p>{component.counterfactual || 'Thermal projection unavailable'}</p>
                </div>
                <div className="feature-contributions">
                  <span className="feature-contributions-title">Local risk drivers</span>
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
            <p className="section-description">Features with higher importance contribute more strongly to the loaded anomaly ensemble.</p>
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
            <p className="section-description">These are the actual features used by the loaded IDDQ drift predictor.</p>
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
