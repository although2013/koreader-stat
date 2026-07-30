/* 核心指标卡片区：数值随周期 Tab 切换 */

function TrendBadge({ change }) {
  if (!change) return null;

  const styles = {
    up: 'text-emerald-300 bg-emerald-500/10 border-emerald-400/20',
    down: 'text-rose-300 bg-rose-500/10 border-rose-400/20',
    flat: 'text-amber-300 bg-amber-500/10 border-amber-400/20',
  };
  const paths = {
    up: 'M4 17 10 11l3 3 7-8M15 6h5v5',
    down: 'M4 7l6 6 3-3 7 8m0-5v5h-5',
    flat: 'M4 12h16m-5-5 5 5-5 5',
  };
  const sign = change.direction === 'up' ? '+' : change.direction === 'down' ? '-' : '';

  return (
    <span title="较前一天" className={`inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[10px] font-semibold leading-none ${styles[change.direction]}`}>
      <svg aria-hidden="true" viewBox="0 0 24 24" className="h-3 w-3 fill-none stroke-current stroke-[2.4] stroke-linecap-round stroke-linejoin-round">
        <path d={paths[change.direction]} />
      </svg>
      {sign}{change.percent}%
    </span>
  );
}

function MetricCard({ title, value, sub, icon, change }) {
  return (
    <div className="glass-card p-4 rounded-xl border border-slate-800/80 flex flex-col justify-between hover:border-slate-700 hover:bg-slate-900/90 transition-all">
      <div className="flex justify-between text-xs text-slate-400">
        <span>{title}</span>
        <span>{icon}</span>
      </div>
      <div className="mt-2">
        <div className="text-xl font-bold text-slate-100 tracking-tight">{value}</div>
        <div className="mt-0.5 flex items-end justify-between gap-2">
          <div className="text-[11px] text-slate-400">{sub}</div>
          <TrendBadge change={change} />
        </div>
      </div>
    </div>
  );
}

// 打卡卡片三档语义不同：总计看连续天数，本周看 7 天内打卡几天，当天看今天是否已读
function percentageChange(current, previous) {
  if (typeof previous !== 'number' || previous <= 0) return null;
  const raw = ((current - previous) / previous) * 100;
  if (Math.abs(raw) < 1) return { percent: 0, direction: 'flat' };
  return { percent: Math.round(Math.abs(raw)), direction: raw > 0 ? 'up' : 'down' };
}

function todayChanges(m) {
  const previous = m.previousDay;
  if (!previous) return {};
  return {
    duration: percentageChange(m.totalMinutes || 0, previous.totalMinutes),
    pages: percentageChange(m.totalPages || 0, previous.totalPages),
    sessions: percentageChange(m.totalSessions || 0, previous.totalSessions),
  };
}

function streakCard(m, period) {
  if (period === 'all') {
    return { title: '打卡 Streak', icon: '🔥', value: `${m.currentStreak || 0} 天`, sub: `最高: ${m.maxStreak || 0} 天` };
  }
  if (period === 'week') {
    const days = m.daysWithReading || 0;
    return { title: '本周打卡', icon: '🔥', value: `${days}/${m.days || 7} 天`, sub: `打卡率 ${Math.round((days / (m.days || 7)) * 100)}%` };
  }
  return {
    title: '今日打卡',
    icon: '🔥',
    value: m.totalMinutes > 0 ? '已打卡' : '未打卡',
    sub: `连续 ${m.currentStreak || 0} 天`,
  };
}

// 分钟数 -> HH:MM（1252 -> "20:52"）。用 totalMinutes 而非已四舍五入的 totalHours，保证与副文案一致
function formatHoursMinutes(totalMinutes) {
  const mins = Math.max(0, Math.round(totalMinutes || 0));
  return `${String(Math.floor(mins / 60)).padStart(2, '0')}:${String(mins % 60).padStart(2, '0')}`;
}

// 时长副文案：总计给总分钟数，周期态给日均
function durationSub(m, period) {
  if (period === 'all') return `${m.totalMinutes || 0} 分钟`;
  if (period === 'week') return `日均 ${m.avgDailyMin || 0} 分钟`;
  return `${m.totalMinutes || 0} 分钟`;
}

// 划线数没有时间戳，无法按周期拆分；周期态改为展示最长单次会话
function highlightOrSessionCard(m, period) {
  if (period === 'all') {
    return { title: '划线与标注', icon: '✏️', value: `${m.totalHighlights || 0} 处`, sub: '累计笔记' };
  }
  return { title: '最长单次会话', icon: '⏳', value: `${m.maxSessionMin || 0}min`, sub: '期间内最久一次' };
}

export function buildMetricCards(m, period) {
  const isAll = period === 'all';
  const changes = period === 'today' ? todayChanges(m) : {};

  const cards = [
    { title: '总阅读时长', icon: '⏱️', value: formatHoursMinutes(m.totalMinutes), sub: durationSub(m, period) },
    { title: '总翻页数', icon: '📄', value: (m.totalPages || 0).toLocaleString(), sub: `${m.avgSpeedPph || 0} 页/小时` },
    streakCard(m, period),
    { title: '夜猫子指数', icon: '🌙', value: `${m.nightOwlRatio || 0}%`, sub: '00:00 - 06:00 时段' },
    { title: '阅读会话', icon: '🎯', value: `${m.totalSessions || 0} 次`, sub: `均单次 ${m.avgSessionMin || 0}min` },
    { title: '活跃书目', icon: '📚', value: `${m.activeBooks || 0} 本`, sub: isAll ? '已产生阅读时长' : '期间内翻页' },
    highlightOrSessionCard(m, period),
    { title: '翻页效率', icon: '⚡', value: `${m.avgSecPerPage || 0}s`, sub: '平均每页耗时' },
  ];

  return cards.map((card, index) => ({
    ...card,
    change: [changes.duration, changes.pages, null, null, changes.sessions][index],
  }));
}

export function MetricsGrid({ metrics, period }) {
  const current = metrics[period] || metrics.all || {};

  return (
    // key 随周期变化 -> 重新挂载，触发 metric-fade 过渡
    <div key={period} className="grid grid-cols-2 sm:grid-cols-4 gap-4 metric-fade">
      {buildMetricCards(current, period).map(card => (
        <MetricCard key={card.title} {...card} />
      ))}
    </div>
  );
}
