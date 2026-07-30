/* 周期切换 Tab：总计 / 本周（最近 7 天滚动）/ 当天 */

import { useEffect, useState } from 'react';
import { dateStrInTz } from '../lib/time.js';

const PERIOD_TABS = [
  { key: 'all', label: '总计' },
  { key: 'week', label: '本周' },
  { key: 'today', label: '当天' },
];

const PERIOD_KEYS = PERIOD_TABS.map(tab => tab.key);

export function periodFromHash() {
  const key = window.location.hash.replace('#', '');
  return PERIOD_KEYS.includes(key) ? key : 'all';
}

// Tab 状态同步到 URL hash，刷新后保持；也响应浏览器前进/后退
export function usePeriodTab() {
  const [active, setActive] = useState(periodFromHash);

  useEffect(() => {
    const sync = () => setActive(periodFromHash());
    window.addEventListener('hashchange', sync);
    return () => window.removeEventListener('hashchange', sync);
  }, []);

  const select = (key) => {
    window.location.hash = key;
    setActive(key);
  };

  return [active, select];
}

export function PeriodTabs({ metrics, active, onSelect, tzOffset = 0 }) {
  const tabs = PERIOD_TABS.filter(tab => metrics[tab.key]);
  const current = metrics[active] || {};

  // 「当天」取的是 JSON 里最后有记录的一天，可能不是目标时区的今天
  const today = dateStrInTz(new Date(), tzOffset);
  const isStale = active === 'today' && current.date && current.date !== today;

  return (
    <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
      <div className="flex gap-1 p-1 bg-slate-900/60 border border-slate-800 rounded-xl w-fit">
        {tabs.map(tab => (
          <button
            key={tab.key}
            type="button"
            onClick={() => onSelect(tab.key)}
            aria-pressed={tab.key === active}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
              tab.key === active
                ? 'bg-emerald-500/15 text-emerald-300 shadow-sm shadow-emerald-500/10'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <p className="text-xs text-slate-500 flex flex-wrap items-center gap-x-2">
        <span>{current.label || ''}</span>
        {isStale && <span className="text-amber-400/80">数据截至 {current.date}</span>}
      </p>
    </div>
  );
}
