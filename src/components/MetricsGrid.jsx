/* 核心指标卡片区：数值随周期 Tab 切换 */

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

// 打卡卡片三档语义不同：总计看连续天数，本周看 7 天内打卡几天，当天看今天是否已读
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

  return [
    { title: '总阅读时长', icon: '⏱️', value: `${m.totalHours || 0}h`, sub: durationSub(m, period) },
    { title: '总翻页数', icon: '📄', value: (m.totalPages || 0).toLocaleString(), sub: `${m.avgSpeedPph || 0} 页/小时` },
    streakCard(m, period),
    { title: '夜猫子指数', icon: '🌙', value: `${m.nightOwlRatio || 0}%`, sub: '00:00 - 06:00 时段' },
    { title: '阅读会话', icon: '🎯', value: `${m.totalSessions || 0} 次`, sub: `均单次 ${m.avgSessionMin || 0}min` },
    { title: '活跃书目', icon: '📚', value: `${m.activeBooks || 0} 本`, sub: isAll ? '已产生阅读时长' : '期间内翻页' },
    highlightOrSessionCard(m, period),
    { title: '翻页效率', icon: '⚡', value: `${m.avgSecPerPage || 0}s`, sub: '平均每页耗时' },
  ];
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
