import { useState, useEffect } from "react";
import { api } from "../api";

function AuditLog() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAudit = async () => {
      try {
        const data = await api.getAuditLog();
        setEntries(data.entries || []);
      } catch (err) {
        console.error('Failed to fetch audit log:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchAudit();
  }, []);

  const downloadAuditLog = () => {
    const headers = ["Timestamp", "DUT ID", "Lot ID", "Risk Band", "Risk Score", "Confidence %", "Explanation", "Model Version"];
    const rows = entries.length > 0 ? entries : [
      { timestamp: "2026-09-16 09:42", dut_id: "IC0060", lot_id: "LOT2026B", risk_band: "CRITICAL", risk_score: "87.3", confidence_pct: "0", explanation: "Predicted value approaching safety limit", model_version: "BG-AI-2.0" },
      { timestamp: "2026-09-16 09:38", dut_id: "IC0075", lot_id: "LOT2026B", risk_band: "CRITICAL", risk_score: "87.2", confidence_pct: "0", explanation: "Predicted value approaching safety limit", model_version: "BG-AI-2.0" },
    ];
    const escapeCsv = (value) => `"${String(value ?? '').replace(/"/g, '""')}"`;
    const csvRows = rows.map((entry) => [
      entry.timestamp,
      entry.dut_id,
      entry.lot_id,
      entry.risk_band,
      entry.risk_score,
      entry.confidence_pct,
      entry.explanation,
      entry.model_version || 'BG-AI-2.0',
    ].map(escapeCsv).join(','));
    const csv = [headers.map(escapeCsv).join(','), ...csvRows].join("\r\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "burninguard-audit-log.csv";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="analysis-page">
      <div className="analysis-page-header">
        <span className="panel-label">TRACEABILITY & AUDIT</span>
        <h1>Audit Log</h1>
        <p>Immutable record of component risk assessments and model decisions</p>
      </div>

      <section className="analysis-section">
        <div className="panel-header">
          <div>
            <span className="panel-label">AUDIT TRAIL</span>
            <h2>Traceability Log</h2>
            <span className="result-count">Recent model decisions</span>
          </div>
          <button className="audit-download-button" onClick={downloadAuditLog}>↓ Download Audit Log</button>
        </div>
        <div className="audit-table-wrapper">
          <table className="audit-table">
            <thead>
              <tr><th>Timestamp</th><th>DUT ID</th><th>Lot ID</th><th>Risk Band</th><th>Risk Score</th><th>Confidence %</th><th>Explanation</th><th>Model Version</th></tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={8}>Loading audit log...</td></tr>
              ) : entries.length > 0 ? (
                entries.map((entry, i) => (
                  <tr key={i}>
                    <td>{entry.timestamp}</td><td>{entry.dut_id}</td><td>{entry.lot_id}</td>
                    <td><span className={`risk-${(entry.risk_band || '').toLowerCase()}`}>{entry.risk_band}</span></td>
                    <td>{entry.risk_score}</td><td>{entry.confidence_pct}%</td>
                    <td>{entry.explanation}</td><td>{entry.model_version || 'BG-AI-2.0'}</td>
                  </tr>
                ))
              ) : (
                <tr><td colSpan={8}>No audit entries found</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="analysis-section">
        <div className="panel-header">
          <div><span className="panel-label">AUDIT INTEGRITY</span><h2>Traceability Information</h2></div>
        </div>
        <div className="audit-info-grid">
          <div className="audit-info-card"><span>Model Version</span><strong>BG-AI-2.0</strong></div>
          <div className="audit-info-card"><span>Data Type</span><strong>Synthetic Demonstration</strong></div>
          <div className="audit-info-card"><span>Audit Status</span><strong>Recorded</strong></div>
        </div>
      </section>
    </div>
  );
}

export default AuditLog;
