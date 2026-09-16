import { useState } from "react";
import RiskHeatmap from "../components/RiskHeatmap";

function AnomalyAnalysis() {
  const [selectedLots, setSelectedLots] = useState([
  "LOT2026A",
  "LOT2026B",
  "LOT2026C",
  "LOT2026D",
  "LOT2026E",
  "LOT2026G",
]);

  const [selectedRisks, setSelectedRisks] = useState([
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
  ]);
  const dutData = [
  {
    dutId: "IC0060",
    lot: "LOT2026B",
    riskScore: 87.3,
    riskBand: "CRITICAL",
    confidence: 0,
    anomalyScore: 0.7,
    reason: "Predicted value approaching the safety limit",
  },
  {
    dutId: "IC0075",
    lot: "LOT2026B",
    riskScore: 87.2,
    riskBand: "CRITICAL",
    confidence: 0,
    anomalyScore: 0.7,
    reason: "Predicted value approaching the safety limit",
  },
  {
    dutId: "IC0201",
    lot: "LOT2026E",
    riskScore: 82.1,
    riskBand: "CRITICAL",
    confidence: 0,
    anomalyScore: 0.7,
    reason: "Significant deviation from lot population",
  },
  {
    dutId: "IC0211",
    lot: "LOT2026E",
    riskScore: 80.8,
    riskBand: "CRITICAL",
    confidence: 0,
    anomalyScore: 0.7,
    reason: "Predicted value approaching the safety limit",
  },
  {
    dutId: "IC0042",
    lot: "LOT2026A",
    riskScore: 77.7,
    riskBand: "HIGH",
    confidence: 32.5,
    anomalyScore: 0.7,
    reason: "High physics-normalised drift rate",
  },
  {
    dutId: "IC0288",
    lot: "LOT2026G",
    riskScore: 75.0,
    riskBand: "HIGH",
    confidence: 31.1,
    anomalyScore: 0.7,
    reason: "Significant deviation from lot population",
  },
  {
    dutId: "IC0222",
    lot: "LOT2026E",
    riskScore: 74.9,
    riskBand: "HIGH",
    confidence: 1.9,
    anomalyScore: 0.7,
    reason: "Predicted value approaching the safety limit",
  },
  {
    dutId: "IC0177",
    lot: "LOT2026D",
    riskScore: 74.6,
    riskBand: "HIGH",
    confidence: 34.3,
    anomalyScore: 0.7,
    reason: "High physics-normalised drift rate",
  },
  {
    dutId: "IC0033",
    lot: "LOT2026A",
    riskScore: 74.0,
    riskBand: "HIGH",
    confidence: 33.5,
    anomalyScore: 0.7,
    reason: "Significant deviation from lot population",
  },
  {
    dutId: "IC0146",
    lot: "LOT2026D",
    riskScore: 73.8,
    riskBand: "HIGH",
    confidence: 30.6,
    anomalyScore: 0.7,
    reason: "High physics-normalised drift rate",
  },
];
const filteredDutData = dutData.filter(
  (dut) =>
    selectedLots.includes(dut.lot) &&
    selectedRisks.includes(dut.riskBand)
);
  return (
    <div className="analysis-page">

      <div className="analysis-page-header">
        <span className="panel-label">AI ANOMALY DETECTION</span>
        <h1>Anomaly Analysis</h1>
        <p>
          Live component risk assessment and anomaly detection
        </p>
      </div>
      <div className="analysis-controls">

  <div className="control-action">
    <button
  className="regenerate-button"
  onClick={() => window.location.reload()}
>
  ↻ Regenerate data &amp; re-run pipeline
</button>

    <p className="data-disclaimer">
      Synthetic demonstration data only. Never present as real test data.
    </p>
  </div>

  <div className="filter-group">
    <span className="filter-label">Filter by lot</span>

    <div className="filter-options">
  {[
    "LOT2026A",
    "LOT2026B",
    "LOT2026C",
    "LOT2026D",
    "LOT2026E",
    "LOT2026G",
  ].map((lot) => (
    <button
      key={lot}
      className={`filter-chip ${
        selectedLots.includes(lot) ? "active" : ""
      }`}
      onClick={() => {
        setSelectedLots((current) =>
          current.includes(lot)
            ? current.filter((item) => item !== lot)
            : [...current, lot]
        );
      }}
    >
      {lot} ×
    </button>
  ))}
</div>
  </div>

  <div className="filter-group">
    <span className="filter-label">Filter by risk band</span>

    <div className="filter-options">
  {["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((risk) => (
    <button
      key={risk}
      className={`filter-chip ${risk.toLowerCase()} ${
        selectedRisks.includes(risk) ? "active" : ""
      }`}
      onClick={() => {
        setSelectedRisks((current) =>
          current.includes(risk)
            ? current.filter((item) => item !== risk)
            : [...current, risk]
        );
      }}
    >
      {risk} ×
    </button>
  ))}
</div>
  </div>

</div>

      <section className="analysis-section heatmap-section">
        <div className="panel-header">
          <div>
            <span className="panel-label">LIVE MONITORING</span>
            <h2>Live Risk Heatmap</h2>
          </div>
        </div>

        <RiskHeatmap />
      </section>

      <section className="analysis-section">
        <div className="panel-header">
          <div>
            <span className="panel-label">COMPONENT ANALYSIS</span>
            <h2>DUT Table</h2>
            <span className="result-count">
  Showing {filteredDutData.length} components
</span>
          </div>
        </div>

        <div className="dut-table-wrapper">
  <table className="dut-table">
    <thead>
      <tr>
        <th>DUT ID</th>
        <th>Lot</th>
        <th>Risk Score</th>
        <th>Risk Band</th>
        <th>Confidence %</th>
        <th>Anomaly Score</th>
        <th>Why Flagged?</th>
      </tr>
    </thead>

    <tbody>
  {filteredDutData.map((dut) => (
    <tr key={dut.dutId}>
      <td>{dut.dutId}</td>
      <td>{dut.lot}</td>
      <td>{dut.riskScore}</td>

      <td>
        <span className={`risk-${dut.riskBand.toLowerCase()}`}>
          {dut.riskBand}
        </span>
      </td>

      <td>{dut.confidence}%</td>
      <td>{dut.anomalyScore}</td>
      <td>{dut.reason}</td>
    </tr>
  ))}
</tbody>
  </table>
</div>
      </section>

    </div>
  );
}

export default AnomalyAnalysis;