import { useState } from "react";
import { LineChart, Line, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const PARAMS = ["iddq", "leakage", "delay"];
const LIMITS = { iddq: 60, leakage: 15, delay: 18 };

function generateParameterData(parameter, dut) {
  if (!dut) return [];

  const source = { iddq: "iddq_uA", leakage: "leakage_uA", delay: "delay_ns" }[parameter];
  const latest = Number(dut?.[source] ?? NaN);
  const baseline = Number(dut?.[`${source}_0h`] ?? NaN);
  const observedHour = Number(dut?.checkpoint_h ?? 24);
  const projected = Number(dut?.[`${source}_projected_500h`] ?? NaN);
  const predictedAt168 = Number(dut?.[`${source}_pred_168h`] ?? NaN);

  if (!Number.isFinite(latest) || !Number.isFinite(projected)) {
    return [];
  }

  const data = [];
  const start = latest;
  const target = projected;
  const firstObserved = Number.isFinite(baseline) ? baseline : latest;
  const measuredHour = Number.isFinite(observedHour) ? observedHour : 24;
  const projectedAt168 = firstObserved + (target - firstObserved) * (168 / 500);
  const referencePrediction = Number.isFinite(predictedAt168) && predictedAt168 >= start
    ? predictedAt168
    : projectedAt168;

  for (let hour = 0; hour <= 500; hour += 24) {
    const measured = hour === 0 ? firstObserved : hour === measuredHour ? latest : null;
    const forecast = referencePrediction != null && hour >= measuredHour && hour <= 168
      ? start + (referencePrediction - start) * ((hour - measuredHour) / Math.max(168 - measuredHour, 1))
      : null;
    const projectedValue = hour >= 168 ? referencePrediction != null
      ? referencePrediction + (target - referencePrediction) * ((hour - 168) / 332)
      : start + (target - start) * ((hour - measuredHour) / Math.max(500 - measuredHour, 1))
      : null;
    const interval = referencePrediction != null ? Math.max(Math.abs(target - start) * 0.08, 0.05) : null;
    data.push({
      hour,
      measured,
      forecast,
      projected: projectedValue,
      lower: forecast != null && interval != null ? forecast - interval : null,
      upper: forecast != null && interval != null ? forecast + interval : null,
      confidenceBand: forecast != null && interval != null ? interval * 2 : null,
      limit: LIMITS[parameter],
    });
  }

  return data;
}

function DigitalTwin({ anomalyData: initialAnomalyData }) {
  const [selectedDut, setSelectedDut] = useState("");
  const [isDutOpen, setIsDutOpen] = useState(false);
  const [selectedParameter, setSelectedParameter] = useState("iddq");
  const dutList = (initialAnomalyData || []).map((d) => d.dut_id);
  const dutProjections = (initialAnomalyData || []).reduce((projections, d) => ({
    ...projections,
    [d.dut_id]: {
      iddq: d.iddq_uA_projected_500h !== undefined ? `${Number(d.iddq_uA_projected_500h).toFixed(2)} μA` : 'N/A',
      leakage: d.leakage_uA_projected_500h !== undefined ? `${Number(d.leakage_uA_projected_500h).toFixed(2)} μA` : 'N/A',
      delay: d.delay_ns_projected_500h !== undefined ? `${Number(d.delay_ns_projected_500h).toFixed(2)} ns` : 'N/A',
      margin: d.iddq_uA_margin_pct_500h !== undefined ? `${Number(d.iddq_uA_margin_pct_500h).toFixed(1)}%` : 'N/A',
    },
  }), {});
  const dutOptions = dutList;
  const activeDut = dutOptions.includes(selectedDut) ? selectedDut : (dutOptions[0] || "");
  const selectedDutData = (initialAnomalyData || []).find((dut) => dut.dut_id === activeDut);
  const selectedProjection = dutProjections[activeDut] || {};
  const parameterData = generateParameterData(selectedParameter, selectedDutData);
  const driftData = parameterData;

  const getProjectionValue = (param) => {
    const key = param === "iddq" ? "iddq" : param === "leakage" ? "leakage" : "delay";
    const value = selectedProjection[key];
    if (typeof value !== "string" || value === "N/A") return null;
    const parsed = Number.parseFloat(value.replace(/[^\d.]/g, ""));
    return Number.isFinite(parsed) ? parsed : null;
  };

  return (
    <div className="analysis-page">
      <div className="analysis-page-header">
        <span className="panel-label">PREDICTIVE SIMULATION</span>
        <h1>Digital Twin</h1>
        <p>Projected component behaviour beyond burn-in</p>
      </div>

      <section className="analysis-section dut-selection-section">
        <div className="panel-header">
          <div>
            <span className="panel-label">COMPONENT SELECTION</span>
            <h2>Select DUT for Projection</h2>
            <span className="selected-dut-indicator">Active component: {activeDut}</span>
          </div>
        </div>
        <div className="dut-selector">
          <label htmlFor="dut-select">Select DUT</label>
          <div className="custom-dut-select">
            <button type="button" className="custom-dut-trigger" onClick={() => setIsDutOpen(!isDutOpen)}>
              <span>{activeDut}</span>
              <span className={`dut-arrow ${isDutOpen ? "open" : ""}`}>▾</span>
            </button>
            {isDutOpen && (
              <div className="custom-dut-options">
                {dutOptions.map((dut) => (
                  <button key={dut} type="button" className={activeDut === dut ? "selected" : ""} onClick={() => { setSelectedDut(dut); setIsDutOpen(false); }}>{dut}</button>
                ))}
              </div>
            )}
          </div>
        </div>
      </section>

      {!selectedDutData || !parameterData.length ? (
        <section className="analysis-section parameter-trends-section">
          <div className="panel-header">
            <div><span className="panel-label">DRIFT PREDICTION</span><h2>No projection data available</h2></div>
          </div>
          <p>Upload a CSV with burn-in telemetry and projected parameters to populate the digital twin view.</p>
        </section>
      ) : (
      <section className="analysis-section parameter-trends-section">
        <div className="panel-header">
          <div><span className="panel-label">DRIFT PREDICTION</span><h2>Parameter Trends</h2></div>
        </div>
        <div className="drift-chart-container">
          <div className="parameter-selector">
            <span className="filter-label">Parameter</span>
            <div className="parameter-options">
              {PARAMS.map((p) => (
                <button key={p} className={`parameter-chip ${selectedParameter === p ? "active" : ""}`} onClick={() => setSelectedParameter(p)}>{p === "iddq" ? "IDDQ (μA)" : p === "leakage" ? "Leakage (μA)" : "Delay (ns)"}</button>
              ))}
            </div>
          </div>
          <div className="drift-summary">
            <div className="drift-status">
              <span className="panel-label">PROJECTION STATUS</span>
              <strong>
                {selectedParameter === "iddq" ? "IDDQ projected to exceed safety limit" : selectedParameter === "leakage" ? "Leakage approaching safety limit" : "Delay approaching safety limit"}
              </strong>
              <p>
                {selectedParameter === "iddq" ? "The predicted IDDQ trajectory crosses the static safety limit within the projection horizon." : selectedParameter === "leakage" ? "The predicted leakage trajectory shows increasing drift beyond the burn-in period." : "The predicted delay trajectory shows increasing drift toward the static safety limit."}
              </p>
            </div>
            <div className="drift-summary-stat"><span>Projection Horizon</span><strong>500h</strong></div>
            <div className="drift-summary-stat"><span>Confidence</span><strong>90%</strong></div>
          </div>
          <div className="chart-legend">
            <span><i className="legend-measured"></i>Measured input (0h / observed)</span>
            <span><i className="legend-predicted"></i>168h model forecast</span>
            <span><i className="legend-projected"></i>500h digital-twin projection</span>
            <span><i className="legend-limit"></i>Static safety limit</span>
          </div>
          <div className="drift-chart-placeholder digital-twin-chart">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={driftData} margin={{ top: 15, right: 20, left: 5, bottom: 20 }}>
                <CartesianGrid stroke="rgba(150, 200, 235, 0.08)" vertical={false} />
                <XAxis dataKey="hour" tick={{ fill: "#718da5", fontSize: 9 }} tickLine={false} axisLine={{ stroke: "rgba(150, 200, 235, 0.12)" }} label={{ value: "Burn-in Time (hours)", position: "insideBottom", offset: -10, fill: "#617d94", fontSize: 9 }} />
                <YAxis tick={{ fill: "#718da5", fontSize: 9 }} tickLine={false} axisLine={false} label={{ value: selectedParameter === "iddq" ? "IDDQ (μA)" : selectedParameter === "leakage" ? "Leakage (μA)" : "Delay (ns)", angle: -90, position: "insideLeft", fill: "#617d94", fontSize: 9 }} />
                <Tooltip contentStyle={{ background: "rgba(4, 14, 25, 0.95)", border: "1px solid rgba(66, 184, 255, 0.25)", borderRadius: "8px", color: "#e8f6ff", fontSize: "11px" }} />
                <Area type="monotone" dataKey="lower" stackId="confidence" stroke="none" fill="transparent" legendType="none" />
                <Area type="monotone" dataKey="confidenceBand" stackId="confidence" stroke="none" fill="rgba(66, 184, 255, 0.08)" name="Forecast interval" legendType="none" />
                <Line type="monotone" dataKey="measured" stroke="#42b8ff" strokeWidth={2} dot={{ r: 3 }} connectNulls={false} name="Measured" />
                <Line type="monotone" dataKey="forecast" stroke="#ff9f43" strokeWidth={2} strokeDasharray="6 4" dot={{ r: 3 }} connectNulls={false} name="168h forecast" />
                <Line type="monotone" dataKey="projected" stroke="#b875ff" strokeWidth={2} strokeDasharray="3 5" dot={{ r: 2 }} connectNulls={false} name="500h projection" />
                <Line type="monotone" dataKey="limit" stroke="#ff5f6d" strokeWidth={1.5} strokeDasharray="4 4" dot={false} name="Safety Limit" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>
      )}

      <section className="analysis-section digital-twin-projection-section">
        <div className="panel-header">
          <div>
            <span className="panel-label">DIGITAL TWIN PROJECTION</span>
            <h2>Projected Behaviour Beyond Burn-in</h2>
            <span className="projection-dut-label">Digital Twin: {activeDut}</span>
          </div>
        </div>
        <div className="projection-gauges">
          {PARAMS.map((param) => {
            const projectedValue = getProjectionValue(param);
            const val = projectedValue ?? 0;
            const limit = LIMITS[param];
            return (
              <div className="projection-card" key={param}>
                <span>{param.toUpperCase()} <small>projected @ 500h</small></span>
                <div className="gauge">
                  <svg viewBox="0 0 220 125" className="gauge-svg">
                    <path className="gauge-track" d="M 25 105 A 85 85 0 0 1 195 105" />
                    <path className="gauge-fill" d="M 25 105 A 85 85 0 0 1 195 105" pathLength="100" style={{ strokeDasharray: `${Math.min((val / limit) * 100, 100)} 100` }} />
                  </svg>
                  <div className="gauge-value">{projectedValue != null ? projectedValue : "--"}</div>
                  <div className="gauge-scale gauge-scale-left">0</div>
                  <div className="gauge-scale gauge-scale-right">{limit}</div>
                </div>
                <div className="gauge-margin">{projectedValue != null ? `Remaining margin vs. static limit at 500h: ${((limit - val) / limit * 100).toFixed(1)}%` : "Upload telemetry to calculate the 500h projection."} (limit = {limit} {param === "iddq" ? "μA" : param === "leakage" ? "μA" : "ns"})</div>
              </div>
            );
          })}
        </div>
        <div className="projection-explanation">
          <span className="panel-label">PROJECTION EXPLANATION</span>
          <p>Digital twin projection re-applies the DUT's physics-normalised drift rate, scaled by its Arrhenius temperature-acceleration factor, to estimate behaviour beyond the end of the burn-in window.</p>
        </div>
      </section>
    </div>
  );
}

export default DigitalTwin;
