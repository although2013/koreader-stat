/* 通用卡片外壳：把重复的玻璃拟态样式收敛到一处 */

// 通栏面板（热力图、图书进度列表）
export function Panel({ className = '', children }) {
  return (
    <div className={`glass-card p-6 rounded-2xl border border-slate-800 ${className}`}>
      {children}
    </div>
  );
}

// 图表卡片：统一外壳 + 头部（图标胶囊 + 标题 + 右侧附加信息）
// iconClass 传完整的 Tailwind 类名（而非拼接颜色），否则 Tailwind 扫描不到
export function ChartCard({ title, icon, iconClass = 'bg-emerald-500/10 text-emerald-400', meta, className = '', children }) {
  return (
    <div className={`glass-card p-6 rounded-2xl border border-slate-800/80 bg-slate-900/60 backdrop-blur-xl flex flex-col justify-between space-y-4 shadow-xl ${className}`}>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
        <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2 tracking-wide">
          <span className={`p-1 rounded-lg text-xs ${iconClass}`}>{icon}</span> {title}
        </h2>
        {meta}
      </div>
      {children}
    </div>
  );
}
