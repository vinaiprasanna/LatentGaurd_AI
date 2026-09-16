import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useState } from "react";

function Explainability() {
  const [expandedDut, setExpandedDut] = useState(null);
    const flaggedComponents = [
  {
    dutId: "IC0060",
    lot: "LOT2026B",
    riskScore: 87.3,
    riskBand: "CRITICAL",
    confidence: 0,
    explanation:
      "Predicted value approaching the safety limit",
      features: [
    { name: "temperature_c", contribution: 0.31 },
    { name: "iddq_uA", contribution: 0.27 },
    { name: "leakage_uA", contribution: 0.19 },
  ],
  },
  {
    dutId: "IC0075",
    lot: "LOT2026B",
    riskScore: 87.2,
    riskBand: "CRITICAL",
    confidence: 0,
    explanation:
      "Predicted value approaching the safety limit",
      features: [
  { name: "temperature_c", contribution: 0.29 },
  { name: "iddq_uA", contribution: 0.25 },
  { name: "leakage_uA", contribution: 0.18 },
],
  },
  {
    dutId: "IC0201",
    lot: "LOT2026E",
    riskScore: 82.1,
    riskBand: "CRITICAL",
    confidence: 0,
    explanation:
      "Significant deviation from lot population",
      features: [
  { name: "iddq_uA", contribution: 0.34 },
  { name: "temperature_c", contribution: 0.28 },
  { name: "delay_ns", contribution: 0.21 },
],
  },
  {
    dutId: "IC0042",
    lot: "LOT2026A",
    riskScore: 77.7,
    riskBand: "HIGH",
    confidence: 32.5,
    explanation:
      "High physics-normalised drift rate",
      features: [
  { name: "temperature_c", contribution: 0.30 },
  { name: "leakage_uA", contribution: 0.26 },
  { name: "iddq_uA", contribution: 0.17 },
],
  },
  {
    dutId: "IC0288",
    lot: "LOT2026G",
    riskScore: 75.0,
    riskBand: "HIGH",
    confidence: 31.1,
    explanation:
      "Significant deviation from lot population",
      features: [
  { name: "temperature_c", contribution: 0.28 },
  { name: "leakage_uA", contribution: 0.24 },
  { name: "iddq_uA", contribution: 0.20 },
],
  },
  
];
const globalFeatureImportance = [
  { feature: "temperature_c", importance: 0.31 },
  { feature: "iddq_uA", importance: 0.27 },
  { feature: "leakage_uA", importance: 0.19 },
  { feature: "delay_ns", importance: 0.14 },
  { feature: "vcc_v", importance: 0.09 },
];
const driftFeatureImportance = [
  { feature: "temperature_c", importance: 0.34 },
  { feature: "iddq_uA", importance: 0.26 },
  { feature: "burn_in_hours", importance: 0.21 },
  { feature: "leakage_uA", importance: 0.12 },
  { feature: "vcc_v", importance: 0.07 },
];
  return (
    <div className="analysis-page">

      <div className="analysis-page-header">
        <span className="panel-label">MODEL INTERPRETABILITY</span>
        <h1>Explainability</h1>
        <p>
          Understand why components were flagged by the anomaly detection system
        </p>
      </div>

      <section className="analysis-section">
        <div className="panel-header">
          <div>
            <span className="panel-label">FLAGGED COMPONENTS</span>
            <h2>Component Explanations</h2>
            <span className="result-count">
  {flaggedComponents.length} flagged components
</span>
          </div>
        </div>

        <div className="explainability-list">

  {flaggedComponents.map((component) => (
    <div
  className={`explainability-item ${
    expandedDut === component.dutId ? "expanded" : ""
  }`}
  key={component.dutId}
  onClick={() =>
    setExpandedDut(
      expandedDut === component.dutId ? null : component.dutId
    )
  }
>

      <div className="explainability-item-header">
        <div>
          <div className="explainability-component-name">
  <strong>{component.dutId}</strong>
  <span>{component.lot}</span>
</div>
        </div>

        <div className="explainability-risk">
          <strong>{component.riskScore}</strong>
          <span className={`risk-${component.riskBand.toLowerCase()}`}>
            {component.riskBand}
          </span>
        </div>
      </div>

      <div
  className={`explainability-details ${
    expandedDut === component.dutId ? "visible" : ""
  }`}
>
  <span>
    Confidence: {component.confidence}%
  </span>

  <span>
    Why flagged: {component.explanation}
  </span>

  <div className="feature-contributions">
    <span className="feature-contributions-title">
      Top contributing features
    </span>

    {component.features.map((feature) => (
      <div
        className="feature-contribution"
        key={feature.name}
      >
        <span>{feature.name}</span>

        <div className="contribution-bar">
          <div
            className="contribution-fill"
            style={{
              width: `${feature.contribution * 100}%`,
            }}
          />
        </div>

        <strong>
          {feature.contribution.toFixed(2)}
        </strong>
      </div>
    ))}
  </div>
</div>

    </div>
  ))}

</div>
      </section>
      <section className="analysis-section explanation-method-section">
  <div className="panel-header">
    <div>
      <span className="panel-label">EXPLANATION METHOD</span>
      <h2>How the Model Explains Risk</h2>
    </div>
  </div>

  <div className="explanation-method-grid">

    <div className="method-step">
      <span className="method-number">01</span>
      <div>
        <strong>Detect</strong>
        <p>
          The anomaly detection system identifies unusual component behaviour.
        </p>
      </div>
    </div>

    <div className="method-step">
      <span className="method-number">02</span>
      <div>
        <strong>Analyse</strong>
        <p>
          Component measurements and physics-informed features are evaluated.
        </p>
      </div>
    </div>

    <div className="method-step">
      <span className="method-number">03</span>
      <div>
        <strong>Explain</strong>
        <p>
          Feature contributions indicate which signals influenced the risk assessment.
        </p>
      </div>
    </div>

  </div>
</section>

      <section className="analysis-section">
        <div className="panel-header">
          <div>
            <span className="panel-label">GLOBAL FEATURE IMPORTANCE</span>
            <h2>What Influences Risk?</h2>
            <p className="section-description">
  Features with higher importance contribute more strongly to the model's
  anomaly-risk assessment.
</p>
          </div>
        </div>

        <div className="feature-importance-chart">
  <ResponsiveContainer width="100%" height={300}>
    <BarChart
      data={globalFeatureImportance}
      layout="vertical"
      margin={{
        top: 5,
        right: 30,
        left: 30,
        bottom: 5,
      }}
    >
      <CartesianGrid
        stroke="rgba(150, 200, 235, 0.08)"
        horizontal={false}
      />

      <XAxis
        type="number"
        domain={[0, 0.35]}
        tick={{ fill: "#718da5", fontSize: 9 }}
        tickLine={false}
        axisLine={{ stroke: "rgba(150, 200, 235, 0.12)" }}
      />

      <YAxis
        type="category"
        dataKey="feature"
        width={100}
        tick={{ fill: "#a9bfd3", fontSize: 10 }}
        tickLine={false}
        axisLine={false}
      />

      <Tooltip
        contentStyle={{
          background: "rgba(4, 14, 25, 0.95)",
          border: "1px solid rgba(66, 184, 255, 0.25)",
          borderRadius: "8px",
          color: "#e8f6ff",
          fontSize: "11px",
        }}
        formatter={(value) => [
          Number(value).toFixed(2),
          "Importance",
        ]}
      />

      <Bar
        dataKey="importance"
        fill="#42b8ff"
        radius={[0, 4, 4, 0]}
        barSize={18}
      />
    </BarChart>
  </ResponsiveContainer>
</div>
      </section>

      <section className="analysis-section">
        <div className="panel-header">
          <div>
            <span className="panel-label">DRIFT MODEL</span>
            <h2>Drift-Model Feature Importance</h2>
            <p className="section-description">
  These features influence the model's estimation of component behaviour
  and drift over the projection horizon.
</p>
          </div>
        </div>

        <div className="feature-importance-chart">
  <ResponsiveContainer width="100%" height={300}>
    <BarChart
      data={driftFeatureImportance}
      layout="vertical"
      margin={{
        top: 5,
        right: 30,
        left: 30,
        bottom: 5,
      }}
    >
      <CartesianGrid
        stroke="rgba(150, 200, 235, 0.08)"
        horizontal={false}
      />

      <XAxis
        type="number"
        domain={[0, 0.40]}
        tick={{ fill: "#718da5", fontSize: 9 }}
        tickLine={false}
        axisLine={{ stroke: "rgba(150, 200, 235, 0.12)" }}
      />

      <YAxis
        type="category"
        dataKey="feature"
        width={110}
        tick={{ fill: "#a9bfd3", fontSize: 10 }}
        tickLine={false}
        axisLine={false}
      />

      <Tooltip
        contentStyle={{
          background: "rgba(4, 14, 25, 0.95)",
          border: "1px solid rgba(66, 184, 255, 0.25)",
          borderRadius: "8px",
          color: "#e8f6ff",
          fontSize: "11px",
        }}
        formatter={(value) => [
          Number(value).toFixed(2),
          "Importance",
        ]}
      />

      <Bar
        dataKey="importance"
        fill="#ff9f43"
        radius={[0, 4, 4, 0]}
        barSize={18}
      />
    </BarChart>
  </ResponsiveContainer>
</div>
      </section>

    </div>
  );
}

export default Explainability;