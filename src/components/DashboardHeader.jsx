/* 页头：标题 + 统计周期 + 最近在读 */

export function DashboardHeader({ period = {}, recent }) {
  return (
    <header className="flex flex-col md:flex-row justify-between items-start md:items-center glass-card p-6 rounded-2xl border border-slate-800 gap-4">
      <div>
        <div className="flex items-center gap-3">
          <span className="text-3xl">📖</span>
          <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400">
            KOReader 阅读深度看板
          </h1>
        </div>
        <p className="text-xs text-slate-400 mt-2 flex flex-wrap items-center gap-2">
          <span>⏱️ 统计周期：{period.start || ''} ~ {period.end || ''} ({period.totalDays || 0} 天)</span>
          <span>•</span>
          <span>更新时间：{period.updatedAt || ''}</span>
        </p>
      </div>

      {recent && (
        <div className="flex items-center gap-3 bg-emerald-950/40 border border-emerald-500/20 px-4 py-2.5 rounded-xl text-emerald-400 text-sm self-stretch md:self-auto justify-between md:justify-start">
          <div>
            <p className="text-xs text-slate-400">最近在读</p>
            <p className="font-semibold text-slate-200">《{recent.title}》</p>
          </div>
          <span className="text-xs text-slate-400 ml-2">{recent.time?.split(' ')[1] || ''}</span>
        </div>
      )}
    </header>
  );
}
