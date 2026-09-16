function AuditLog() {
  const downloadAuditLog = () => {
    const auditData = [
      ["Timestamp", "DUT ID", "Lot ID", "Risk Band", "Risk Score", "Confidence %", "Explanation", "Model Version"],
      ["2026-09-16 09:42", "IC0060", "LOT2026B", "CRITICAL", "87.3", "0%", "Predicted value approaching safety limit", "BG-AI-2.0"],
      ["2026-09-16 09:38", "IC0075", "LOT2026B", "CRITICAL", "87.2", "0%", "Predicted value approaching safety limit", "BG-AI-2.0"],
      ["2026-09-16 09:34", "IC0201", "LOT2026E", "CRITICAL", "82.1", "0%", "Significant deviation from lot population", "BG-AI-2.0"],
      ["2026-09-16 09:30", "IC0042", "LOT2026A", "HIGH", "77.7", "32.5%", "High physics-normalised drift rate", "BG-AI-2.0"],
    ];

    const csv = auditData
      .map((row) =>
        row.map((value) => `"${value.replace(/"/g, '""')}"`).join(",")
      )
      .join("\n");

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
        <p>
          Immutable record of component risk assessments and model decisions
        </p>
      </div>

      <section className="analysis-section">

        <div className="panel-header">
          <div>
            <span className="panel-label">AUDIT TRAIL</span>
            <h2>Traceability Log</h2>
            <span className="result-count">
              Recent model decisions
            </span>
          </div>

          <button
  className="audit-download-button"
  onClick={downloadAuditLog}
>
  ↓ Download Audit Log
</button>
        </div>

        <div className="audit-table-wrapper">
          <table className="audit-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>DUT ID</th>
                <th>Lot ID</th>
                <th>Risk Band</th>
                <th>Risk Score</th>
                <th>Confidence %</th>
                <th>Explanation</th>
                <th>Model Version</th>
              </tr>
            </thead>

            <tbody>
              <tr>
                <td>2026-09-16 09:42</td>
                <td>IC0060</td>
                <td>LOT2026B</td>
                <td>
                  <span className="risk-critical">CRITICAL</span>
                </td>
                <td>87.3</td>
                <td>0%</td>
                <td>Predicted value approaching safety limit</td>
                <td>BG-AI-2.0</td>
              </tr>

              <tr>
                <td>2026-09-16 09:38</td>
                <td>IC0075</td>
                <td>LOT2026B</td>
                <td>
                  <span className="risk-critical">CRITICAL</span>
                </td>
                <td>87.2</td>
                <td>0%</td>
                <td>Predicted value approaching safety limit</td>
                <td>BG-AI-2.0</td>
              </tr>

              <tr>
                <td>2026-09-16 09:34</td>
                <td>IC0201</td>
                <td>LOT2026E</td>
                <td>
                  <span className="risk-critical">CRITICAL</span>
                </td>
                <td>82.1</td>
                <td>0%</td>
                <td>Significant deviation from lot population</td>
                <td>BG-AI-2.0</td>
              </tr>

              <tr>
                <td>2026-09-16 09:30</td>
                <td>IC0042</td>
                <td>LOT2026A</td>
                <td>
                  <span className="risk-high">HIGH</span>
                </td>
                <td>77.7</td>
                <td>32.5%</td>
                <td>High physics-normalised drift rate</td>
                <td>BG-AI-2.0</td>
              </tr>
            </tbody>
          </table>
        </div>

      </section>

      <section className="analysis-section">

        <div className="panel-header">
          <div>
            <span className="panel-label">AUDIT INTEGRITY</span>
            <h2>Traceability Information</h2>
          </div>
        </div>

        <div className="audit-info-grid">

          <div className="audit-info-card">
            <span>Model Version</span>
            <strong>BG-AI-2.0</strong>
          </div>

          <div className="audit-info-card">
            <span>Data Type</span>
            <strong>Synthetic Demonstration</strong>
          </div>

          <div className="audit-info-card">
            <span>Audit Status</span>
            <strong>Recorded</strong>
          </div>

        </div>

      </section>

    </div>
  );
}

export default AuditLog;
