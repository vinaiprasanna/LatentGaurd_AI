import { useState, useEffect } from "react";
import { api } from "../api";
import RiskHeatmap from "../components/RiskHeatmap";

function AnomalyAnalysis({ anomalyData: initialAnomalyData }) {
  const [selectedLots, setSelectedLots] = useState([]);
  const [selectedRisks, setSelectedRisks] = useState(["LOW", "MEDIUM", "HIGH", "CRITICAL"]);
  const [dutData, setDutData] = useState(initialAnomalyData || []);


  useEffect(() => {
    let active = true;
    api.getDuts()
      .then((data) => {
        if (active) setDutData(data.duts || []);
      })
      .catch((err) => console.error('Failed to load DUT data:', err));
    return () => { active = false; };
  }, []);

  const filteredDutData = dutData.filter(
    (dut) => (selectedLots.length === 0 || selectedLots.includes(dut.lot_id)) && selectedRisks.includes(dut.risk_band)
  );

  const lotOptions = [...new Set(dutData.map((d) => d.lot_id))];

  return (
    <div className="analysis-page">
      <div className="analysis-page-header">
        <span className="panel-label">AI ANOMALY DETECTION</span>
        <h1>Anomaly Analysis</h1>
        <p>Live component risk assessment and anomaly detection</p>
      </div>
      

      <section className="analysis-section heatmap-section">
        <div className="panel-header">
          <div><span className="panel-label">LIVE MONITORING</span><h2>Live Risk Heatmap</h2></div>
        </div>
        <RiskHeatmap anomalyData={dutData} />
      </section>
<div className="analysis-controls">
        
        <div className="filter-group">
          <span className="filter-label">Filter by lot</span>
          <div className="filter-options">
            {lotOptions.map((lot) => (
              <button key={lot} className={`filter-chip ${selectedLots.length === 0 || selectedLots.includes(lot) ? "active" : ""}`} onClick={() => { setSelectedLots((current) => current.length === 0 ? lotOptions.filter((item) => item !== lot) : current.includes(lot) ? current.filter((item) => item !== lot) : [...current, lot]); }}>{lot} ×</button>
            ))}
          </div>
        </div>
        <div className="filter-group">
          <span className="filter-label">Filter by risk band</span>
          <div className="filter-options">
            {["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((risk) => (
              <button key={risk} className={`filter-chip ${risk.toLowerCase()} ${selectedRisks.includes(risk) ? "active" : ""}`} onClick={() => { setSelectedRisks((current) => current.includes(risk) ? current.filter((item) => item !== risk) : [...current, risk]); }}>{risk} ×</button>
            ))}
          </div>
        </div>
      </div>
      <section className="analysis-section">
        <div className="panel-header">
          <div>
            <span className="panel-label">COMPONENT ANALYSIS</span>
            <h2>DUT Table</h2>
            <span className="result-count">Showing {filteredDutData.length} components</span>
          </div>
        </div>
        <div className="dut-table-wrapper">
          <table className="dut-table">
            <thead>
              <tr><th>DUT ID</th><th>Lot</th><th>Risk Score</th><th>Risk Band</th><th>Confidence %</th><th>Anomaly Score</th><th>Why Flagged?</th></tr>
            </thead>
            <tbody>
              {filteredDutData.map((dut) => (
                <tr key={dut.dut_id}>
                  <td>{dut.dut_id}</td>
                  <td>{dut.lot_id}</td>
                  <td>{dut.risk_score}</td>
                  <td><span className={`risk-${(dut.risk_band || '').toLowerCase()}`}>{dut.risk_band}</span></td>
                  <td>{dut.risk_confidence_pct}%</td>
                  <td>{dut.anomaly_ensemble_score ? dut.anomaly_ensemble_score.toFixed(2) : '--'}</td>
                  <td>{dut.explanation}</td>
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
