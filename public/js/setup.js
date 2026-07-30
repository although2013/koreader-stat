/*
 * 全局依赖解构 + 图表统一样式。
 * 必须最先加载：后续所有脚本都依赖这里声明的全局常量。
 */

const { useState, useEffect, useMemo, useRef } = React;

const {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell
} = window.Recharts;

// 「一天」的定义不在前端硬编码，而是读 JSON 里的 period.tzOffsetHours，
// 其唯一来源是 export_stats.py 的 TZ_OFFSET_HOURS。
// 既不能用浏览器本地时区（换设备/出差就会错位），也不能直接用 toISOString（那是 UTC）。
const DAY_MS = 24 * 60 * 60 * 1000;

function tzOffsetFromPeriod(period) {
  const offset = period && period.tzOffsetHours;
  if (typeof offset === 'number') return offset;
  console.warn('reading_data.json 缺少 period.tzOffsetHours，暂按 UTC+0 切分日界线，请重新运行 export_stats.py');
  return 0;
}

// 某一时刻在目标时区里属于哪一天 -> YYYY-MM-DD
// 先按偏移量平移，再取 UTC 日期部分；固定偏移的时区这样算是精确的
function dateStrInTz(date, offsetHours) {
  return new Date(date.getTime() + offsetHours * 60 * 60 * 1000).toISOString().slice(0, 10);
}

// Recharts 坐标轴的通用配色，保证各图表观感一致
const AXIS_PROPS = { stroke: '#64748b', fontSize: 11, tickLine: false, axisLine: false };

// 提示框（Tooltip）的通用样式
const TOOLTIP_CONTENT_STYLE = {
  backgroundColor: '#0f172a',
  borderColor: '#334155',
  borderRadius: '0.75rem',
  color: '#f8fafc',
  boxShadow: '0 10px 15px -3px rgba(0,0,0,0.5)',
};
