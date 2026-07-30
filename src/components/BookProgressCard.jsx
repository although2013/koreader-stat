/* 研读图书进度与预估 ETA */

import { Panel } from './Card.jsx';

function ProgressBar({ progress }) {
  return (
    <div className="flex items-center gap-2">
      <div className="w-24 bg-slate-800 h-2 rounded-full overflow-hidden">
        <div
          className="bg-gradient-to-r from-teal-500 to-emerald-400 h-full rounded-full transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>
      <span className="text-xs font-mono text-slate-300 w-10 text-right">{progress}%</span>
    </div>
  );
}

// 已完成显示绿色徽标，否则显示按 PPH 预估的剩余时间
function StatusBadge({ status, eta }) {
  const finished = status === 'finished';

  return (
    <span className={`text-xs px-2.5 py-1 rounded-full font-medium border ${
      finished
        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
        : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
    }`}>
      {finished ? '已完成' : `还需 ${eta}`}
    </span>
  );
}

function BookProgressRow({ book }) {
  return (
    <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/80 hover:bg-emerald-950/30 hover:border-emerald-500/30 hover:shadow-lg transition-all duration-200 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 group">
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold text-slate-400 group-hover:text-emerald-400 transition-colors">{book.medal}</span>
          <span className="font-semibold text-slate-100 group-hover:text-emerald-300 transition-colors">{book.title}</span>
        </div>
        <p className="text-xs text-slate-400">已读 {book.duration} · 标注 {book.highlights} 处</p>
      </div>

      <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end">
        <ProgressBar progress={book.progress} />
        <StatusBadge status={book.status} eta={book.eta} />
      </div>
    </div>
  );
}

export function BookProgressCard({ books }) {
  return (
    <Panel className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-slate-200 flex items-center gap-2">
          <span>🏆</span> 研读图书进度与预估 ETA
        </h2>
        <span className="text-xs text-slate-500">根据 PPH 自动预测</span>
      </div>

      <div className="space-y-3">
        {books.map((book, idx) => (
          <BookProgressRow key={book.rank || idx} book={book} />
        ))}
      </div>
    </Panel>
  );
}
