/* 最近 7 天阅读动态：柱状图 + 主攻图书 */

function WeeklySummary({ totalHours, avgDailyMin }) {
  return (
    <div className="flex items-center gap-4 text-xs">
      <span className="text-slate-400">
        7天累计: <strong className="text-emerald-400 font-mono text-sm">{totalHours}h</strong>
      </span>
      <span className="text-slate-400">
        日均: <strong className="text-teal-300 font-mono text-sm">{avgDailyMin}m</strong>
      </span>
    </div>
  );
}

function WeeklyTopBooks({ books = [] }) {
  return (
    <div className="bg-slate-950/40 p-3 rounded-xl border border-slate-800/60 space-y-2">
      <p className="text-xs font-medium text-slate-400 flex items-center gap-1.5">
        <span className="text-amber-400">🔥</span> 近 7 天主攻图书
      </p>
      {books.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          {books.map((book, idx) => (
            <div
              key={idx}
              className="flex justify-between items-center bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800/60 hover:border-emerald-500/30 transition-all"
            >
              <span className="text-xs text-slate-300 font-medium truncate mr-2" title={book.title}>
                {idx + 1}. 《{book.title}》
              </span>
              <span className="font-mono text-xs text-emerald-400 font-semibold shrink-0">
                {book.hours}h
              </span>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-xs text-slate-500 italic">这 7 天暂无阅读记录</p>
      )}
    </div>
  );
}

function WeeklyReportCard({ last7Days }) {
  return (
    <ChartCard
      title="最近 7 天阅读动态"
      icon="📊"
      iconClass="bg-emerald-500/10 text-emerald-400"
      className="lg:col-span-2"
      meta={<WeeklySummary totalHours={last7Days.totalHours} avgDailyMin={last7Days.avgDailyMin} />}
    >
      <div className="h-44 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={last7Days.chart || []} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
            <XAxis dataKey="day" {...AXIS_PROPS} />
            <YAxis unit="m" {...AXIS_PROPS} />
            <Tooltip
              cursor={{ fill: 'rgba(16, 185, 129, 0.06)' }}
              contentStyle={TOOLTIP_CONTENT_STYLE}
              formatter={(val) => [`${val} 分钟`, '阅读时长']}
            />
            <Bar dataKey="minutes" fill="#10b981" radius={[6, 6, 0, 0]} barSize={24} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <WeeklyTopBooks books={last7Days.topBooks} />
    </ChartCard>
  );
}
