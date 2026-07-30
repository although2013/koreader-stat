/* 页面骨架：只负责取数据 + 按顺序拼装各个卡片 */

function App() {
  const { data, error } = useReadingData();

  if (error) return <ErrorScreen message={error} />;
  if (!data) return <LoadingScreen />;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      <DashboardHeader period={data.period} recent={data.recent} />

      {data.overall && <MetricsGrid overall={data.overall} />}

      <HeatmapCard heatmapData={data.heatmap || {}} />

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
