/*
 * 全局依赖解构 + 图表统一样式。
 * 必须最先加载：后续所有脚本都依赖这里声明的全局常量。
 */

const { useState, useEffect, useMemo, useRef } = React;

const {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell
} = window.Recharts;

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
