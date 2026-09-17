import { useState } from "react";
import { LineChart, Line, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const PARAMS = ["iddq", "leakage", "delay"];
const LIMITS = { iddq: 60, leakage: 15, delay: 18 };

const defaultProjections = {
  IC0060: { iddq: "42.8 μA", leakage: "8.6 μA", delay: "12.4 ns", margin: "18.4%" },
  IC0075: { iddq: "45.2 μA", leakage: "9.1 μA", delay: "12.9 ns", margin: "15.8%" },
  IC0201: { iddq: "51.6 μA", leakage: "10.4 μA", delay: "13.7 ns", margin: "11.2%" },
  IC0211: { iddq: "48.9 μA", leakage: "10.1 μA", delay: "13.4 ns", margin: "12.6%" },
  IC0042: { iddq: "39.7 μA", leakage: "7.8 μA", delay: "11.9 ns", margin: "21.3%" },
  IC0288: { iddq: "43.5 μA", leakage: "8.9 μA", delay: "12.7 ns", margin: "16.7%" },
};

function generateParameterData(parameter, dut) {
  const data = [];
  const limits = { iddq: 60, leakage: 15, delay: 18 };
  const source = { iddq: "iddq_uA", leakage: "leakage_uA", delay: "delay_ns" }[parameter];
  const start = Number(dut?.[source] || { iddq: 30, leakage: 4, delay: 9.5 }[parameter]);
  const target = Number(dut?.[`${source}_projected_500h`] || start);
  const predictedAt168 = Number(dut?.[`${source}_pred_168h`] || start + (target - start) * 0.336);
  for (let h = 0; h <= 500; h += 24) {
    const measured = h <= 168 ? start + (predictedAt168 - start) * (h / 168) : null;
    const predicted = start + (target - start) * (h / 500);
    const interval = Math.max(Math.abs(target - start) * 0.08, 0.05);
    const upper = predicted + interval;
    const lower = predicted - interval;
    data.push({ hour: h, measured, predicted, lower, upper, limit: limits[parameter] });
  }
  return data;
}

function DigitalTwin({ anomalyData: initialAnomalyData }) {
  const [selectedDut, setSelectedDut] = useState("IC0060");
  const [isDutOpen, setIsDutOpen] = useState(false);
  const [selectedParameter, setSelectedParameter] = useState("iddq");
  const dutList = (initialAnomalyData || []).map((d) => d.dut_id);
  const dutProjections = (initialAnomalyData || []).reduce((projections, d) => ({
    ...projections,
    [d.dut_id]: {
      iddq: d.iddq_uA_projected_500h ? `${Number(d.iddq_uA_projected_500h).toFixed(2)} μA` : '42.8 μA',
      leakage: d.leakage_uA_projected_500h ? `${Number(d.leakage_uA_projected_500h).toFixed(2)} μA` : '8.6 μA',
      delay: d.delay_ns_projected_500h ? `${Number(d.delay_ns_projected_500h).toFixed(2)} ns` : '12.4 ns',
      margin: d.iddq_uA_margin_pct_500h ? `${Number(d.iddq_uA_margin_pct_500h).toFixed(1)}%` : '18.4%',
    },
  }), {});
  const dutOptions = dutList.length > 0 ? dutList : Object.keys(defaultProjections);
  const activeDut = dutOptions.includes(selectedDut) ? selectedDut : dutOptions[0];
  const selectedDutData = (initialAnomalyData || []).find((dut) => dut.dut_id === activeDut);
  const selectedProjection = dutProjections[activeDut] || defaultProjections[activeDut];
  const parameterData = generateParameterData(selectedParameter, selectedDutData);
  const driftData = parameterData.map((point) => ({ ...point, confidenceBand: point.upper - point.lower }));

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
            <span><i className="legend-measured"></i>Measured trajectory</span>
            <span><i className="legend-predicted"></i>Predicted trajectory</span>
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
                <Area type="monotone" dataKey="confidenceBand" stackId="confidence" stroke="none" fill="rgba(66, 184, 255, 0.08)" name="90% Confidence" legendType="none" />
                <Line type="monotone" dataKey="measured" stroke="#42b8ff" strokeWidth={2} dot={{ r: 3 }} connectNulls={false} name="Measured" />
                <Line type="monotone" dataKey="predicted" stroke="#ff9f43" strokeWidth={2} strokeDasharray="6 4" dot={{ r: 3 }} name="Predicted" />
                <Line type="monotone" dataKey="limit" stroke="#ff5f6d" strokeWidth={1.5} strokeDasharray="4 4" dot={false} name="Safety Limit" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

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
            const val = parseFloat(selectedProjection[param === "iddq" ? "iddq" : param === "leakage" ? "leakage" : "delay"].replace(/[^\d.]/g, ""));
            const limit = LIMITS[param];
            return (
              <div className="projection-card" key={param}>
                <span>{param.toUpperCase()} <small>projected @ 500h</small></span>
                <div className="gauge">
                  <svg viewBox="0 0 220 125" className="gauge-svg">
                    <path className="gauge-track" d="M 25 105 A 85 85 0 0 1 195 105" />
                    <path className="gauge-fill" d="M 25 105 A 85 85 0 0 1 195 105" pathLength="100" style={{ strokeDasharray: `${Math.min((val / limit) * 100, 100)} 100` }} />
                  </svg>
                  <div className="gauge-value">{selectedProjection[param === "iddq" ? "iddq" : param === "leakage" ? "leakage" : "delay"].replace(/[^\d.]/g, "")}</div>
                  <div className="gauge-scale gauge-scale-left">0</div>
                  <div className="gauge-scale gauge-scale-right">{limit}</div>
                </div>
                <div className="gauge-margin">Remaining margin vs. static limit at 500h: {((limit - val) / limit * 100).toFixed(1)}% (limit = {limit} {param === "iddq" ? "μA" : param === "leakage" ? "μA" : "ns"})</div>
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
