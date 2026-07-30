/* 核心指标卡片区 */

function MetricCard({ title, value, sub, icon }) {
  return (
    <div className="glass-card p-4 rounded-xl border border-slate-800/80 flex flex-col justify-between hover:border-slate-700 hover:bg-slate-900/90 transition-all">
      <div className="flex justify-between text-xs text-slate-400">
        <span>{title}</span>
        <span>{icon}</span>
      </div>
      <div className="mt-2">
        <div className="text-xl font-bold text-slate-100 tracking-tight">{value}</div>
        <div className="text-[11px] text-slate-400 mt-0.5">{sub}</div>
      </div>
    </div>
  );
}

function MetricsGrid({ overall }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
      <MetricCard title="总阅读时长" value={`${overall.totalHours}h`} sub={`${overall.totalMinutes || Math.round(overall.totalHours * 60)} 分钟`} icon="⏱️" />
      <MetricCard title="总翻页数" value={overall.totalPages?.toLocaleString() || 0} sub={`${overall.avgSpeedPph || 0} 页/小时`} icon="📄" />
      <MetricCard title="打卡 Streak" value={`${overall.currentStreak || 0} 天`} sub={`最高: ${overall.maxStreak || 0} 天`} icon="🔥" />
      <MetricCard title="夜猫子指数" value={`${overall.nightOwlRatio || 0}%`} sub="00:00 - 06:00 时段" icon="🌙" />
      <MetricCard title="阅读会话" value={`${overall.totalSessions || 0} 次`} sub={`均单次 ${overall.avgSessionMin || 0}min`} icon="🎯" />
      <MetricCard title="活跃书目" value={`${overall.activeBooks || 0} 本`} sub="已产生阅读时长" icon="📚" />
      <MetricCard title="划线与标注" value={`${overall.totalHighlights || 0} 处`} sub="累计笔记" icon="✏️" />
      <MetricCard title="翻页效率" value={`${overall.avgSecPerPage || 0}s`} sub="平均每页耗时" icon="⚡" />
    </div>
  );
}
