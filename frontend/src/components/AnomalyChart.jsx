import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

function AnomalyChart({ anomalyData: propData }) {
  const grouped = new Map();
  (propData || []).forEach((dut) => {
    const checkpoint = Number(dut.checkpoint_h);
    const key = Number.isFinite(checkpoint) ? checkpoint : 'latest';
    const item = grouped.get(key) || { anomalies: 0, total: 0 };
    item.total += 1;
    if (dut.anomaly_decision === 'ANOMALY') item.anomalies += 1;
    grouped.set(key, item);
  });
  const data = [...grouped.entries()]
    .sort(([left], [right]) => String(left).localeCompare(String(right), undefined, { numeric: true }))
    .map(([checkpoint, values]) => ({
      hour: checkpoint === 'latest' ? 'Latest' : `${checkpoint}h`,
      anomalies: values.anomalies,
      total: values.total,
    }));

  if (data.length === 0) {
    return <div className="chart-empty-state">Upload telemetry to view anomaly trend.</div>;
  }

  if (data.length === 1) {
    const overview = [{
      checkpoint: data[0].hour,
      anomalies: data[0].anomalies,
      normal: Math.max(data[0].total - data[0].anomalies, 0),
    }];
    return (
      <div style={{ width: "100%", height: 260 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={overview} margin={{ top: 18, right: 18, left: 0, bottom: 5 }} barGap={8}>
            <CartesianGrid stroke="rgba(120, 180, 220, 0.12)" strokeDasharray="4 6" vertical={false} />
            <XAxis dataKey="checkpoint" stroke="rgba(160, 195, 220, 0.55)" tick={{ fontSize: 11, fill: "#9fb5ca" }} tickLine={false} />
            <YAxis allowDecimals={false} width={24} stroke="rgba(160, 195, 220, 0.55)" tick={{ fontSize: 11, fill: "#9fb5ca" }} tickLine={false} />
            <Tooltip contentStyle={{ background: "rgba(7, 18, 32, 0.95)", border: "1px solid rgba(100, 190, 255, 0.35)", borderRadius: "10px", color: "#e8f5ff" }} />
            <Bar dataKey="anomalies" name="Anomalies" fill="#ff6b5f" radius={[5, 5, 0, 0]} barSize={42} />
            <Bar dataKey="normal" name="Normal" fill="#32d583" radius={[5, 5, 0, 0]} barSize={42} />
          </BarChart>
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
