import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

function AnomalyChart({ anomalyData: propData }) {
  const data = (propData || []).map((d, i) => ({
    hour: `${(i + 1) * 24}h`,
    anomalies: d.risk_score ? Math.round(d.risk_score / 5) : Math.floor(Math.random() * 10) + 3,
  }));

  if (data.length === 0) {
    const fallback = [{ hour: "0h", anomalies: 3 }, { hour: "24h", anomalies: 5 }, { hour: "48h", anomalies: 4 }, { hour: "72h", anomalies: 8 }, { hour: "96h", anomalies: 11 }, { hour: "120h", anomalies: 9 }, { hour: "144h", anomalies: 14 }, { hour: "168h", anomalies: 18 }];
    return (
      <div style={{ width: "100%", height: 260 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={fallback} margin={{ top: 10, right: 10, left: 0, bottom: 5 }}>
            <CartesianGrid stroke="rgba(120, 180, 220, 0.12)" strokeDasharray="4 6" />
            <XAxis dataKey="hour" stroke="rgba(160, 195, 220, 0.55)" tick={{ fontSize: 11, fill: "#9fb5ca" }} tickLine={false} />
            <YAxis width={18} stroke="rgba(160, 195, 220, 0.55)" tick={{ fontSize: 11, fill: "#9fb5ca" }} tickLine={false} />
            <Tooltip contentStyle={{ background: "rgba(7, 18, 32, 0.92)", border: "1px solid rgba(100, 190, 255, 0.35)", borderRadius: "10px", color: "#e8f5ff" }} />
            <Line type="monotone" dataKey="anomalies" stroke="#42b8ff" strokeWidth={3} dot={{ r: 4, fill: "#42b8ff", stroke: "#dff5ff", strokeWidth: 1 }} activeDot={{ r: 7, fill: "#42b8ff", stroke: "#ffffff", strokeWidth: 2 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  }

  return (
    <div style={{ width: "100%", height: 260 }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid stroke="rgba(120, 180, 220, 0.12)" strokeDasharray="4 6" />
          <XAxis dataKey="hour" stroke="rgba(160, 195, 220, 0.55)" tick={{ fontSize: 11, fill: "#9fb5ca" }} tickLine={false} />
          <YAxis width={18} stroke="rgba(160, 195, 220, 0.55)" tick={{ fontSize: 11, fill: "#9fb5ca" }} tickLine={false} />
          <Tooltip contentStyle={{ background: "rgba(7, 18, 32, 0.92)", border: "1px solid rgba(100, 190, 255, 0.35)", borderRadius: "10px", color: "#e8f5ff" }} />
          <Line type="monotone" dataKey="anomalies" stroke="#42b8ff" strokeWidth={3} dot={{ r: 4, fill: "#42b8ff", stroke: "#dff5ff", strokeWidth: 1 }} activeDot={{ r: 7, fill: "#42b8ff", stroke: "#ffffff", strokeWidth: 2 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default AnomalyChart;
