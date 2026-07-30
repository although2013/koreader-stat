/* 数据加载中 / 加载失败的整屏占位 */

function LoadingScreen() {
  return (
    <div className="flex justify-center items-center min-h-screen text-slate-400">
      <div className="flex items-center gap-3">
        <span className="animate-spin text-xl">⏳</span>
        <span>正在读取阅读记录数据...</span>
      </div>
    </div>
  );
}

function ErrorScreen({ message }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen text-rose-400 gap-2">
      <p className="text-lg font-semibold">⚠️ 数据加载失败</p>
      <p className="text-sm text-slate-500">{message}</p>
    </div>
  );
}
