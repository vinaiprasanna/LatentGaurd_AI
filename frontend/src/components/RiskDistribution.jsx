import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";

function RiskDistribution({ anomalyData: propData }) {
  const data = propData || [];
  const low = data.filter((d) => d.risk_band === "LOW").length;
  const medium = data.filter((d) => d.risk_band === "MEDIUM").length;
  const high = data.filter((d) => d.risk_band === "HIGH").length;
  const critical = data.filter((d) => d.risk_band === "CRITICAL").length;

  const riskData = [
    { name: "Low Risk", value: low },
    { name: "Medium Risk", value: medium },
    { name: "High Risk", value: high },
    { name: "Critical", value: critical },
  ];

  if (!data.length) {
    return <div className="chart-empty-state">Upload telemetry to view risk distribution.</div>;
  }

  const COLORS = ["#32d583", "#f5c451", "#ff9f43", "#ff4d5e"];

  return (
    <div className="risk-chart">
      <div className="risk-pie">
        <ResponsiveContainer width="100%" height={210}>
          <PieChart>
            <Pie data={riskData} cx="50%" cy="50%" innerRadius={55} outerRadius={80} paddingAngle={3} dataKey="value">
              {riskData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index]} />
              ))}
            </Pie>
            <Tooltip contentStyle={{ background: "#0b111d", border: "1px solid #29445c", borderRadius: "8px", color: "#e8edf5" }} />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="risk-legend">
        {riskData.map((risk, index) => (
          <div className="risk-item" key={risk.name}>
            <span className="risk-dot" style={{ background: COLORS[index] }}></span>
            <span>{risk.name}</span>
            <strong>{risk.value}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}

export default RiskDistribution;
