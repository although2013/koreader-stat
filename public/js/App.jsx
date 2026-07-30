/* 页面骨架：只负责取数据 + 按顺序拼装各个卡片 */

// 兼容旧版 JSON（还没有 metrics 段时退化成只有「总计」一档）
function readMetrics(data) {
  if (data.metrics) return data.metrics;
  if (!data.overall) return null;
  return { all: { ...data.overall, label: `${data.period?.start || ''} ~ ${data.period?.end || ''}` } };
}

function App() {
  const { data, error } = useReadingData();
  const [period, setPeriod] = usePeriodTab();

  if (error) return <ErrorScreen message={error} />;
  if (!data) return <LoadingScreen />;

  const metrics = readMetrics(data);
  // 时区来自 JSON（源头是 export_stats.py 的 TZ_OFFSET_HOURS），逐层传给需要切分日期的组件
  const tzOffset = tzOffsetFromPeriod(data.period);

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      <DashboardHeader period={data.period} recent={data.recent} />

      {metrics && (
        <div className="space-y-4">
          <PeriodTabs metrics={metrics} active={period} onSelect={setPeriod} tzOffset={tzOffset} />
          <MetricsGrid metrics={metrics} period={metrics[period] ? period : 'all'} />
        </div>
      )}

      <HeatmapCard heatmapData={data.heatmap || {}} tzOffset={tzOffset} />

      {/* 图表区：大屏 3 列宫格，7 天简报占 2 列作为主视觉 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {data.last7Days && <WeeklyReportCard last7Days={data.last7Days} />}
        <HourlyDistributionCard timeDistribution={data.timeDistribution || []} />
        {data.books && <TopBooksCard books={data.books} />}
      </div>

      {data.books && <BookProgressCard books={data.books} />}
    </div>
  );
}
