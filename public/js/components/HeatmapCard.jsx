/* GitHub 风格的 365 天阅读热力图，加载后自动吸附到最右侧（最新数据） */

// 单一数据源：limit 为该档位的上界（分钟），swatch 用于图例，cell 用于格子
const HEATMAP_SCALE = [
  { limit: 0, swatch: 'bg-slate-800/50', cell: 'bg-slate-800/50 hover:border-slate-600' },
  { limit: 15, swatch: 'bg-emerald-950', cell: 'bg-emerald-950 border-emerald-800/50 hover:border-emerald-400' },
  { limit: 45, swatch: 'bg-emerald-800', cell: 'bg-emerald-800 border-emerald-600/50 hover:border-emerald-300' },
  { limit: 90, swatch: 'bg-emerald-600', cell: 'bg-emerald-600 border-emerald-400/50 hover:border-emerald-200' },
  { limit: Infinity, swatch: 'bg-emerald-400', cell: 'bg-emerald-400 border-emerald-200 shadow-sm shadow-emerald-500/50 hover:border-white' },
];

const HEATMAP_DAYS = 365;

function heatmapCellClass(minutes) {
  if (minutes === 0) return HEATMAP_SCALE[0].cell;
  return HEATMAP_SCALE.find(level => minutes < level.limit).cell;
}

function HeatmapLegend() {
  return (
    <div className="flex items-center gap-1.5 text-xs text-slate-400">
      <span>Less</span>
      {HEATMAP_SCALE.map(level => (
        <span key={level.swatch} className={`w-2.5 h-2.5 rounded-sm ${level.swatch}`}></span>
      ))}
      <span>More</span>
    </div>
  );
}

function HeatmapCard({ heatmapData = {} }) {
  const heatmapRef = useRef(null);

  // 生成过去 365 天的连续日期数组
  const days = useMemo(() => {
    const result = [];
    const today = new Date();
    for (let i = HEATMAP_DAYS - 1; i >= 0; i--) {
      const d = new Date();
      d.setDate(today.getDate() - i);
      const dateStr = d.toISOString().split('T')[0];
      result.push({ date: dateStr, minutes: heatmapData[dateStr] || 0 });
    }
    return result;
  }, [heatmapData]);

  // 数据准备完毕后，自动滚动到最右边（最新数据处）
  useEffect(() => {
    if (heatmapRef.current) {
      heatmapRef.current.scrollLeft = heatmapRef.current.scrollWidth;
    }
  }, [heatmapData]);

  return (
    <Panel className="space-y-3">
      <div className="flex justify-between items-center">
        <h2 className="text-base font-semibold text-slate-200 flex items-center gap-2">
          <span>📅</span> 过去 365 天阅读热力图 (Contribution)
        </h2>
        <HeatmapLegend />
      </div>

      {/* 网格容器：按 7 行（周一至周日）排布，绑定 ref 实现自动右滑 */}
      <div
        ref={heatmapRef}
        className="overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-slate-800 scrollbar-track-transparent"
        style={{ scrollBehavior: 'smooth' }}
      >
        <div className="grid grid-rows-7 grid-flow-col gap-1.5 min-w-[720px]">
          {days.map(day => (
            <div
              key={day.date}
              title={`${day.date}: ${day.minutes ? `${day.minutes} 分钟` : '无阅读记录'}`}
              className={`w-3 h-3 rounded-sm border border-transparent transition-all cursor-pointer ${heatmapCellClass(day.minutes)}`}
            />
          ))}
        </div>
      </div>
      <p className="text-[10px] text-slate-500 text-right sm:hidden">← 左右滑动查看历史</p>
    </Panel>
  );
}
