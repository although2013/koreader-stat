/* 核心图书投入时长对比 Top 5（横向柱状图） */

const TOP_BOOK_COLORS = ['#10b981', '#06b6d4', '#6366f1', '#8b5cf6', '#a855f7'];

// 单行 Y 轴刻度：书名过长时截断
function CustomYAxisTick({ x, y, payload }) {
  const title = payload.value || '';
  const formattedTitle = title.length > 7 ? `${title.substring(0, 7)}...` : title;

  return (
    <g transform={`translate(${x},${y})`}>
      <text x={-8} y={4} textAnchor="end" fill="#cbd5e1" fontSize={12} fontWeight={500}>
        {formattedTitle}
      </text>
    </g>
  );
}

function TopBooksCard({ books }) {
  const topBooks = books.slice(0, TOP_BOOK_COLORS.length);

  return (
    <ChartCard
      title="核心图书投入对比 Top 5"
      icon="📚"
      iconClass="bg-indigo-500/10 text-indigo-400"
      className="lg:col-span-1 md:col-span-2"
    >
      <div className="h-56 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart layout="vertical" data={topBooks} margin={{ top: 5, right: 15, left: 15, bottom: 5 }}>
            <XAxis type="number" unit="h" {...AXIS_PROPS} />
            <YAxis
              type="category"
              dataKey="title"
              stroke="#94a3b8"
              fontSize={11}
              width={100}
              tickLine={false}
              axisLine={false}
              tick={<CustomYAxisTick />}
            />
            <Tooltip
              cursor={{ fill: 'rgba(99, 102, 241, 0.06)' }}
              contentStyle={TOOLTIP_CONTENT_STYLE}
              itemStyle={{ color: '#818cf8', fontWeight: 600 }}
              formatter={(val) => [`${val} 小时`, '累计时长']}
            />
            <Bar dataKey="hours" radius={[0, 4, 4, 0]} barSize={14}>
              {topBooks.map((entry, index) => (
                <Cell key={index} fill={TOP_BOOK_COLORS[index]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </ChartCard>
  );
}
