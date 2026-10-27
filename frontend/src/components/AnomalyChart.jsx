// AnomalyChart.jsx
// MetricBarChart is kept as a utility but no longer rendered by default.
// VideoTimelineChart has been removed — video module is frontend-hidden.

import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

export function MetricBarChart({ breakdown = [] }) {
  if (!breakdown || breakdown.length === 0) return null;

  const data = breakdown.map((item) => ({
    name: item.metric.length > 22 ? item.metric.substring(0, 20) + '..' : item.metric,
    fullName: item.metric,
    score: item.score,
    status: item.status,
  }));

  const getBarColor = (score) => {
    if (score >= 80) return '#E8603C';
    if (score >= 50) return '#F2C94C';
    return '#6FCF97';
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload?.length) {
      const d = payload[0].payload;
      return (
        <div className="bg-[#14171C] border border-[#2A2F3A] p-2.5 rounded-lg text-xs font-mono space-y-1 shadow-lg">
          <p className="font-semibold text-[#E7E9EC]">{d.fullName}</p>
          <p className="text-[#8B93A3]">
            ANOMALY_INDEX: <span className="font-bold text-[#4FD6C4]">{d.score}/100</span>
          </p>
          <p className="text-[11px]">
            STATUS: <span className={d.score >= 80 ? 'text-[#E8603C] font-semibold' : 'text-[#6FCF97]'}>{d.status}</span>
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full h-64 font-mono text-xs">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 10, right: 20, left: 10, bottom: 5 }}
        >
          <XAxis type="number" domain={[0, 100]} stroke="#2A2F3A" tick={{ fill: '#8B93A3', fontSize: 10 }} />
          <YAxis type="category" dataKey="name" stroke="#2A2F3A" tick={{ fill: '#E7E9EC', fontSize: 10 }} width={125} />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(79, 214, 196, 0.05)' }} />
          <Bar dataKey="score" radius={[0, 3, 3, 0]} barSize={14}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getBarColor(entry.score)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
