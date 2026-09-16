import { useState } from "react";
import {
  LineChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

function DigitalTwin() {
  const [selectedDut, setSelectedDut] = useState("IC0060");
  const [isDutOpen, setIsDutOpen] = useState(false);
  const [selectedParameter, setSelectedParameter] = useState("iddq");
  const dutProjections = {
  IC0060: {
    iddq: "42.8 μA",
    leakage: "8.6 μA",
    delay: "12.4 ns",
    margin: "18.4%",
  },

  IC0075: {
    iddq: "45.2 μA",
    leakage: "9.1 μA",
    delay: "12.9 ns",
    margin: "15.8%",
  },

  IC0201: {
    iddq: "51.6 μA",
    leakage: "10.4 μA",
    delay: "13.7 ns",
    margin: "11.2%",
  },

  IC0211: {
    iddq: "48.9 μA",
    leakage: "10.1 μA",
    delay: "13.4 ns",
    margin: "12.6%",
  },

  IC0042: {
    iddq: "39.7 μA",
    leakage: "7.8 μA",
    delay: "11.9 ns",
    margin: "21.3%",
  },

  IC0288: {
    iddq: "43.5 μA",
    leakage: "8.9 μA",
    delay: "12.7 ns",
    margin: "16.7%",
  },
};

const selectedProjection = dutProjections[selectedDut];
const parameterData = {
  iddq: [
  { hour: 0, measured: 30, predicted: 30, lower: 29, upper: 31, limit: 60 },
  { hour: 24, measured: 32, predicted: 32, lower: 31, upper: 33, limit: 60 },
  { hour: 48, measured: 34, predicted: 34, lower: 33, upper: 35, limit: 60 },
  { hour: 72, measured: 37, predicted: 37, lower: 36, upper: 38, limit: 60 },
  { hour: 96, measured: 41, predicted: 40, lower: 38, upper: 42, limit: 60 },
  { hour: 120, measured: 44, predicted: 44, lower: 41, upper: 47, limit: 60 },
  { hour: 144, measured: 48, predicted: 48, lower: 44, upper: 52, limit: 60 },
  { hour: 168, measured: 52, predicted: 52, lower: 47, upper: 57, limit: 60 },
  { hour: 240, measured: null, predicted: 57, lower: 51, upper: 63, limit: 60 },
  { hour: 300, measured: null, predicted: 61, lower: 54, upper: 68, limit: 60 },
  { hour: 400, measured: null, predicted: 67, lower: 58, upper: 76, limit: 60 },
  { hour: 500, measured: null, predicted: 73, lower: 62, upper: 84, limit: 60 },
],

  leakage: [
    { hour: 0, measured: 4, predicted: 4, limit: 15 },
    { hour: 24, measured: 4.5, predicted: 4.5, limit: 15 },
    { hour: 48, measured: 5, predicted: 5, limit: 15 },
    { hour: 72, measured: 5.5, predicted: 5.5, limit: 15 },
    { hour: 96, measured: 6.2, predicted: 6.1, limit: 15 },
    { hour: 120, measured: 6.8, predicted: 6.8, limit: 15 },
    { hour: 144, measured: 7.5, predicted: 7.5, limit: 15 },
    { hour: 168, measured: 8.2, predicted: 8.2, limit: 15 },
    { hour: 240, measured: null, predicted: 9.4, limit: 15 },
    { hour: 300, measured: null, predicted: 10.3, limit: 15 },
    { hour: 400, measured: null, predicted: 12.1, limit: 15 },
    { hour: 500, measured: null, predicted: 14.0, limit: 15 },
  ],

  delay: [
    { hour: 0, measured: 9.5, predicted: 9.5, limit: 18 },
    { hour: 24, measured: 9.8, predicted: 9.8, limit: 18 },
    { hour: 48, measured: 10.1, predicted: 10.1, limit: 18 },
    { hour: 72, measured: 10.5, predicted: 10.5, limit: 18 },
    { hour: 96, measured: 11.0, predicted: 10.9, limit: 18 },
    { hour: 120, measured: 11.4, predicted: 11.4, limit: 18 },
    { hour: 144, measured: 11.9, predicted: 11.9, limit: 18 },
    { hour: 168, measured: 12.4, predicted: 12.4, limit: 18 },
    { hour: 240, measured: null, predicted: 13.3, limit: 18 },
    { hour: 300, measured: null, predicted: 14.1, limit: 18 },
    { hour: 400, measured: null, predicted: 15.5, limit: 18 },
    { hour: 500, measured: null, predicted: 17.0, limit: 18 },
  ],
};

const driftData = parameterData[selectedParameter].map((point) => ({
  ...point,
  confidenceBand: point.upper - point.lower,
}));
  return (
    <div className="analysis-page">

      <div className="analysis-page-header">
        <span className="panel-label">PREDICTIVE SIMULATION</span>
        <h1>Digital Twin</h1>
        <p>
          Projected component behaviour beyond burn-in
        </p>
      </div>

      <section className="analysis-section dut-selection-section">
        <div className="panel-header">
          <div>
            <span className="panel-label">COMPONENT SELECTION</span>
            <h2>Select DUT for Projection</h2>
            <span className="selected-dut-indicator">
  Active component: {selectedDut}
</span>
          </div>
        </div>

        <div className="dut-selector">
  <label htmlFor="dut-select">Select DUT</label>

  <div className="custom-dut-select">
  <button
    type="button"
    className="custom-dut-trigger"
    onClick={() => setIsDutOpen(!isDutOpen)}
  >
    <span>
      {selectedDut === "IC0060" && "IC0060 • LOT2026B"}
      {selectedDut === "IC0075" && "IC0075 • LOT2026B"}
      {selectedDut === "IC0201" && "IC0201 • LOT2026E"}
      {selectedDut === "IC0211" && "IC0211 • LOT2026E"}
      {selectedDut === "IC0042" && "IC0042 • LOT2026A"}
      {selectedDut === "IC0288" && "IC0288 • LOT2026G"}
    </span>

    <span className={`dut-arrow ${isDutOpen ? "open" : ""}`}>
      ▾
    </span>
  </button>

  {isDutOpen && (
    <div className="custom-dut-options">
      <button
        type="button"
        className={selectedDut === "IC0060" ? "selected" : ""}
        onClick={() => {
          setSelectedDut("IC0060");
          setIsDutOpen(false);
        }}
      >
        IC0060 • LOT2026B
      </button>

      <button
        type="button"
        className={selectedDut === "IC0075" ? "selected" : ""}
        onClick={() => {
          setSelectedDut("IC0075");
          setIsDutOpen(false);
        }}
      >
        IC0075 • LOT2026B
      </button>

      <button
        type="button"
        className={selectedDut === "IC0201" ? "selected" : ""}
        onClick={() => {
          setSelectedDut("IC0201");
          setIsDutOpen(false);
        }}
      >
        IC0201 • LOT2026E
      </button>

      <button
        type="button"
        className={selectedDut === "IC0211" ? "selected" : ""}
        onClick={() => {
          setSelectedDut("IC0211");
          setIsDutOpen(false);
        }}
      >
        IC0211 • LOT2026E
      </button>

      <button
        type="button"
        className={selectedDut === "IC0042" ? "selected" : ""}
        onClick={() => {
          setSelectedDut("IC0042");
          setIsDutOpen(false);
        }}
      >
        IC0042 • LOT2026A
      </button>

      <button
        type="button"
        className={selectedDut === "IC0288" ? "selected" : ""}
        onClick={() => {
          setSelectedDut("IC0288");
          setIsDutOpen(false);
        }}
      >
        IC0288 • LOT2026G
      </button>
    </div>
  )}
</div>
</div>
      </section>

      <section className="analysis-section">
        <div className="panel-header">
          <div>
            <span className="panel-label">DRIFT PREDICTION</span>
            <h2>Parameter Trends</h2>
          </div>
        </div>

        <div className="drift-chart-container">

  <div className="parameter-selector">
  <span className="filter-label">Parameter</span>

  <div className="parameter-options">
    {[
      { value: "iddq", label: "IDDQ (μA)" },
      { value: "leakage", label: "Leakage (μA)" },
      { value: "delay", label: "Delay (ns)" },
    ].map((parameter) => (
      <button
        key={parameter.value}
        className={`parameter-chip ${
          selectedParameter === parameter.value ? "active" : ""
        }`}
        onClick={() => setSelectedParameter(parameter.value)}
      >
        {parameter.label}
      </button>
    ))}
  </div>
</div>
<div className="drift-summary">

  <div className="drift-status">
    <span className="panel-label">PROJECTION STATUS</span>
    <strong>
  {selectedParameter === "iddq"
    ? "IDDQ projected to exceed safety limit"
    : selectedParameter === "leakage"
    ? "Leakage approaching safety limit"
    : "Delay approaching safety limit"}
</strong>
    <p>
  {selectedParameter === "iddq"
    ? "The predicted IDDQ trajectory crosses the static safety limit within the projection horizon."
    : selectedParameter === "leakage"
    ? "The predicted leakage trajectory shows increasing drift beyond the burn-in period."
    : "The predicted delay trajectory shows increasing drift toward the static safety limit."}
</p>
  </div>

  <div className="drift-summary-stat">
    <span>Projection Horizon</span>
    <strong>500h</strong>
  </div>

  <div className="drift-summary-stat">
    <span>Confidence</span>
    <strong>90%</strong>
  </div>

</div>
  <div className="chart-legend">
    <span>
      <i className="legend-measured"></i>
      Measured trajectory
    </span>

    <span>
      <i className="legend-predicted"></i>
      Predicted trajectory
    </span>

    <span>
      <i className="legend-limit"></i>
      Static safety limit
    </span>
  </div>

  <div className="drift-chart-placeholder digital-twin-chart">
  <ResponsiveContainer width="100%" height="100%">
    <LineChart
      data={driftData}
      margin={{
        top: 15,
        right: 20,
        left: 5,
        bottom: 20,
      }}
    >
      <CartesianGrid
        stroke="rgba(150, 200, 235, 0.08)"
        vertical={false}
      />

      <XAxis
        dataKey="hour"
        tick={{ fill: "#718da5", fontSize: 9 }}
        tickLine={false}
        axisLine={{ stroke: "rgba(150, 200, 235, 0.12)" }}
        label={{
          value: "Burn-in Time (hours)",
          position: "insideBottom",
          offset: -10,
          fill: "#617d94",
          fontSize: 9,
        }}
      />

      <YAxis
        tick={{ fill: "#718da5", fontSize: 9 }}
        tickLine={false}
        axisLine={false}
        label={{
  value:
    selectedParameter === "iddq"
      ? "IDDQ (μA)"
      : selectedParameter === "leakage"
      ? "Leakage (μA)"
      : "Delay (ns)",
  angle: -90,
  position: "insideLeft",
  fill: "#617d94",
  fontSize: 9,
}}
      />

      <Tooltip
        contentStyle={{
          background: "rgba(4, 14, 25, 0.95)",
          border: "1px solid rgba(66, 184, 255, 0.25)",
          borderRadius: "8px",
          color: "#e8f6ff",
          fontSize: "11px",
        }}
      />

      <Area
  type="monotone"
  dataKey="lower"
  stackId="confidence"
  stroke="none"
  fill="transparent"
  legendType="none"
/>

<Area
  type="monotone"
  dataKey="confidenceBand"
  stackId="confidence"
  stroke="none"
  fill="rgba(66, 184, 255, 0.08)"
  name="90% Confidence"
  legendType="none"
/>
      <Line
        type="monotone"
        dataKey="measured"
        stroke="#42b8ff"
        strokeWidth={2}
        dot={{ r: 3 }}
        connectNulls={false}
        name="Measured"
      />

      <Line
        type="monotone"
        dataKey="predicted"
        stroke="#ff9f43"
        strokeWidth={2}
        strokeDasharray="6 4"
        dot={{ r: 3 }}
        name="Predicted"
      />

      <Line
        type="monotone"
        dataKey="limit"
        stroke="#ff5f6d"
        strokeWidth={1.5}
        strokeDasharray="4 4"
        dot={false}
        name="Safety Limit"
      />
      <Line
  type="monotone"
  dataKey="predicted"
  stroke="transparent"
  dot={(props) => {
    const { cx, cy, payload } = props;

    if (payload.predicted >= payload.limit) {
      return (
        <circle
          cx={cx}
          cy={cy}
          r={5}
          fill="#ff5f6d"
          stroke="#fff"
          strokeWidth={1}
        />
      );
    }

    return null;
  }}
  activeDot={false}
  legendType="none"
/>
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
      <span className="projection-dut-label">
        Digital Twin: {selectedDut}
      </span>
    </div>
  </div>

  <div className="projection-gauges">

    <div className="gauge-card">
      <div className="gauge-title">
        <span>iddq_uA</span>
        <small>projected @ 500h</small>
      </div>

      <div className="gauge">
        <svg viewBox="0 0 220 125" className="gauge-svg">
          <path
            className="gauge-track"
            d="M 25 105 A 85 85 0 0 1 195 105"
          />

          <path
            className="gauge-fill"
            d="M 25 105 A 85 85 0 0 1 195 105"
            pathLength="100"
            style={{
              strokeDasharray: `${Math.min(
                (parseFloat(selectedProjection.iddq) / 60) * 100,
                100
              )} 100`,
            }}
          />
        </svg>

        <div className="gauge-value">
          {selectedProjection.iddq.replace(" μA", "")}
        </div>

        <div className="gauge-scale gauge-scale-left">
          0
        </div>

        <div className="gauge-scale gauge-scale-right">
          60
        </div>
      </div>

      <div className="gauge-margin">
        Remaining margin vs. static limit at 500h:
        {" "}
        {(
          ((60 - parseFloat(selectedProjection.iddq)) / 60) *
          100
        ).toFixed(1)}
        % (limit = 60 μA)
      </div>
    </div>


    <div className="gauge-card">
      <div className="gauge-title">
        <span>leakage_uA</span>
        <small>projected @ 500h</small>
      </div>

      <div className="gauge">
        <svg viewBox="0 0 220 125" className="gauge-svg">
          <path
            className="gauge-track"
            d="M 25 105 A 85 85 0 0 1 195 105"
          />

          <path
            className="gauge-fill"
            d="M 25 105 A 85 85 0 0 1 195 105"
            pathLength="100"
            style={{
              strokeDasharray: `${Math.min(
                (parseFloat(selectedProjection.leakage) / 15) * 100,
                100
              )} 100`,
            }}
          />
        </svg>

        <div className="gauge-value">
          {selectedProjection.leakage.replace(" μA", "")}
        </div>

        <div className="gauge-scale gauge-scale-left">
          0
        </div>

        <div className="gauge-scale gauge-scale-right">
          15
        </div>
      </div>

      <div className="gauge-margin">
        Remaining margin vs. static limit at 500h:
        {" "}
        {(
          ((15 - parseFloat(selectedProjection.leakage)) / 15) *
          100
        ).toFixed(1)}
        % (limit = 15 μA)
      </div>
    </div>


    <div className="gauge-card">
      <div className="gauge-title">
        <span>delay_ns</span>
        <small>projected @ 500h</small>
      </div>

      <div className="gauge">
        <svg viewBox="0 0 220 125" className="gauge-svg">
          <path
            className="gauge-track"
            d="M 25 105 A 85 85 0 0 1 195 105"
          />

          <path
            className="gauge-fill"
            d="M 25 105 A 85 85 0 0 1 195 105"
            pathLength="100"
            style={{
              strokeDasharray: `${Math.min(
                (parseFloat(selectedProjection.delay) / 18) * 100,
                100
              )} 100`,
            }}
          />
        </svg>

        <div className="gauge-value">
          {selectedProjection.delay.replace(" ns", "")}
        </div>

        <div className="gauge-scale gauge-scale-left">
          0
        </div>

        <div className="gauge-scale gauge-scale-right">
          18
        </div>
      </div>

      <div className="gauge-margin">
        Remaining margin vs. static limit at 500h:
        {" "}
        {(
          ((18 - parseFloat(selectedProjection.delay)) / 18) *
          100
        ).toFixed(1)}
        % (limit = 18 ns)
      </div>
    </div>

  </div>

  <div className="projection-explanation">
    <span className="panel-label">PROJECTION EXPLANATION</span>

    <p>
      Digital twin projection re-applies the DUT's physics-normalised
      drift rate, scaled by its Arrhenius temperature-acceleration factor,
      to estimate behaviour beyond the end of the burn-in window.
      This is a simplified analytical PoC projection, not a full physics
      simulator.
    </p>
  </div>
</section>

    </div>
  );
}

export default DigitalTwin;