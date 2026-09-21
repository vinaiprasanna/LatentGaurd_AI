import { useState, useEffect } from "react";
import { api } from "../api";

function AuditLog() {
  const [entries, setEntries] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [reviewActions, setReviewActions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAudit = async () => {
      try {
        const [auditData, jobData, actionData] = await Promise.all([
          api.getAuditLog(),
          api.getAuditJobs(),
          api.getReviewActions(),
        ]);
        setEntries(auditData.entries || []);
        setJobs(jobData.jobs || []);
        setReviewActions(actionData.actions || []);
      } catch (err) {
        console.error('Failed to fetch audit log:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchAudit();
  }, []);

  const downloadAuditLog = async () => {
    try {
      const payload = await api.getAuditLogExport();
      const rows = payload.rows || [];
      if (!rows.length) return;
      const headers = Object.keys(rows[0]);
    const escapeCsv = (value) => `"${String(value ?? '').replace(/"/g, '""')}"`;
      const csv = [headers.map(escapeCsv).join(','), ...rows.map((row) => headers.map((header) => escapeCsv(row[header])).join(','))].join("\r\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "burninguard-audit-log.csv";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download complete audit log:', err);
    }
  };

  const downloadJobSnapshot = async (jobId) => {
    try {
      const payload = await api.getAuditJobResults(jobId);
      const rows = payload.results || [];
      if (!rows.length) return;
      const headers = Object.keys(rows[0]);
      const escapeCsv = (value) => `"${String(value ?? '').replace(/"/g, '""')}"`;
      const csv = [
        headers.map(escapeCsv).join(','),
        ...rows.map((row) => headers.map((header) => escapeCsv(row[header])).join(',')),
      ].join('\r\n');
      const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8;' }));
      const link = document.createElement('a');
      link.href = url;
      link.download = `${jobId}-prediction-results.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download prediction snapshot:', err);
    }
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
              <tr><th>Timestamp</th><th>DUT ID</th><th>Lot ID</th><th>Risk Band</th><th>Anomaly Decision</th><th>Risk Score</th><th>Confidence %</th><th>Explanation</th><th>Model Version</th></tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={9}>Loading audit log...</td></tr>
              ) : entries.length > 0 ? (
                entries.map((entry, i) => (
                  <tr key={i}>
                    <td>{entry.timestamp}</td><td>{entry.dut_id}</td><td>{entry.lot_id}</td>
                    <td><span className={`risk-${(entry.risk_band || '').toLowerCase()}`}>{entry.risk_band}</span></td>
                    <td><span className={`anomaly-decision ${(entry.anomaly_decision || 'NORMAL').toLowerCase()}`}>{entry.anomaly_decision || 'NORMAL'}</span></td>
                    <td>{entry.risk_score}</td><td>{entry.confidence_pct}%</td>
                    <td>{entry.explanation}</td><td>{entry.model_version || 'BG-AI-2.0'}</td>
                  </tr>
                ))
              ) : (
                <tr><td colSpan={9}>No audit entries found</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="analysis-section">
        <div className="panel-header">
          <div>
            <span className="panel-label">REVIEW HISTORY</span>
            <h2>Reviewer Actions</h2>
            <span className="result-count">Durable decision follow-up</span>
          </div>
        </div>
        <div className="audit-table-wrapper">
          <table className="audit-table">
            <thead>
              <tr><th>Created</th><th>DUT ID</th><th>Lot ID</th><th>Action</th><th>Status</th><th>Job ID</th></tr>
            </thead>
            <tbody>
              {reviewActions.length > 0 ? reviewActions.map((action) => (
                <tr key={action.action_id}>
                  <td>{new Date(action.created_at).toLocaleString()}</td>
                  <td>{action.dut_id}</td>
                  <td>{action.lot_id}</td>
                  <td>{action.action}</td>
                  <td><span className="review-status">{action.status}</span></td>
                  <td>{action.job_id || '--'}</td>
                </tr>
              )) : (
                <tr><td colSpan={6}>No reviewer actions recorded</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="analysis-section">
        <div className="panel-header">
          <div>
            <span className="panel-label">UPLOAD PROVENANCE</span>
            <h2>Prediction Jobs</h2>
            <span className="result-count">Durable input and model metadata</span>
          </div>
        </div>
        <div className="audit-table-wrapper">
          <table className="audit-table audit-job-table">
            <thead>
              <tr><th>Created</th><th>Job ID</th><th>Source</th><th>DUTs</th><th>Lots</th><th>Stage A Flags</th><th>Schema</th><th>Input SHA-256</th><th>Snapshot</th></tr>
            </thead>
            <tbody>
              {jobs.length > 0 ? jobs.map((job) => (
                <tr key={job.job_id}>
                  <td>{new Date(job.created_at).toLocaleString()}</td>
                  <td>{job.job_id}</td>
                  <td>{job.source_filename}</td>
                  <td>{job.dut_count}</td>
                  <td>{job.lot_count}</td>
                  <td>{job.stage_a_flagged}</td>
                  <td>{job.feature_schema_version}</td>
                  <td title={job.input_sha256}>{job.input_sha256?.slice(0, 16)}...</td>
                  <td><button className="audit-download-button" onClick={() => downloadJobSnapshot(job.job_id)}>Download</button></td>
                </tr>
              )) : (
                <tr><td colSpan={9}>No prediction jobs recorded</td></tr>
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
          <div className="audit-info-card"><span>Recorded Jobs</span><strong>{jobs.length}</strong></div>
          <div className="audit-info-card"><span>Audit Status</span><strong>{jobs.length ? 'Persisted' : 'Awaiting upload'}</strong></div>
        </div>
      </section>
    </div>
  );
}

export default AuditLog;
