/* 24 小时阅读时段分布（面积图） */

function HourlyDistributionCard({ timeDistribution = [] }) {
  return (
    <ChartCard title="24小时阅读时段分布" icon="🌙" iconClass="bg-teal-500/10 text-teal-400">
      <div className="h-56 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={timeDistribution} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
            <defs>
              <linearGradient id="colorHours" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="hour" {...AXIS_PROPS} />
            <YAxis unit="h" {...AXIS_PROPS} />
            <Tooltip
              contentStyle={TOOLTIP_CONTENT_STYLE}
              itemStyle={{ color: '#38bdf8', fontWeight: 600 }}
              labelStyle={{ color: '#94a3b8', marginBottom: '4px' }}
              formatter={(val) => [`${val} 小时`, '阅读时长']}
            />
            <Area type="monotone" dataKey="hours" stroke="#06b6d4" strokeWidth={2} fillOpacity={1} fill="url(#colorHours)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </ChartCard>
  );
}
