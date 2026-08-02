import { useMemo, useState } from 'react';
import { Panel } from './Card.jsx';

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const COLORS = [
  'bg-violet-500/85 border-violet-300/30',
  'bg-sky-500/85 border-sky-300/30',
  'bg-amber-500/85 border-amber-300/30',
  'bg-pink-500/85 border-pink-300/30',
  'bg-teal-500/85 border-teal-300/30',
  'bg-indigo-500/85 border-indigo-300/30',
];

const toKey = date => {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
};

const addDays = (date, count) => {
  const copy = new Date(date);
  copy.setDate(copy.getDate() + count);
  return copy;
};

function colorFor(bookId) {
  return COLORS[Math.abs(Number(bookId)) % COLORS.length];
}

function monthLabel(date) {
  return new Intl.DateTimeFormat('en', { month: 'long', year: 'numeric' }).format(date);
}

export function ReadingCalendar({ entries = [], latestDate }) {
  const [month, setMonth] = useState(() => {
    const initial = latestDate ? new Date(`${latestDate}T12:00:00`) : new Date();
    return new Date(initial.getFullYear(), initial.getMonth(), 1);
  });

  const { weeks, bars } = useMemo(() => {
    const monthStart = new Date(month.getFullYear(), month.getMonth(), 1);
    const monthEnd = new Date(month.getFullYear(), month.getMonth() + 1, 0);
    const gridStart = addDays(monthStart, -monthStart.getDay());
    const gridEnd = addDays(monthEnd, 6 - monthEnd.getDay());
    const totalDays = Math.round((gridEnd - gridStart) / 86400000) + 1;
    const days = Array.from({ length: totalDays }, (_, index) => addDays(gridStart, index));
    // Keep the calendar readable: only the three books with the most reading
    // time on each day are eligible for a visible event.
    const entriesByDate = new Map();
    entries.forEach(entry => {
      if (!entriesByDate.has(entry.date)) entriesByDate.set(entry.date, []);
      entriesByDate.get(entry.date).push(entry);
    });
    const visibleEntries = [...entriesByDate.values()].flatMap(dayEntries =>
      dayEntries.sort((a, b) => b.minutes - a.minutes).slice(0, 3)
    );

    const eventByBook = new Map();
    visibleEntries.forEach(entry => {
      if (!eventByBook.has(entry.bookId)) eventByBook.set(entry.bookId, []);
      eventByBook.get(entry.bookId).push(entry);
    });

    const eventBars = [];
    eventByBook.forEach(bookEntries => {
      const dates = new Map(bookEntries.map(entry => [entry.date, entry]));
      days.forEach((day, index) => {
        const entry = dates.get(toKey(day));
        if (!entry || (index > 0 && dates.has(toKey(days[index - 1])))) return;
        let end = index;
        while (end + 1 < days.length && dates.has(toKey(days[end + 1]))) end += 1;
        for (let start = index; start <= end;) {
          const weekEnd = Math.min(end, start + (6 - (start % 7)));
          eventBars.push({ entry, start, end: weekEnd, length: weekEnd - start + 1 });
          start = weekEnd + 1;
        }
      });
    });

    const placed = eventBars
      .sort((a, b) => a.start - b.start || b.length - a.length)
      .map(bar => ({ ...bar, week: Math.floor(bar.start / 7) }));
    const lanes = Array.from({ length: Math.ceil(days.length / 7) }, () => []);
    placed.forEach(bar => {
      const lane = lanes[bar.week].findIndex(occupied => !occupied.some(range => !(bar.end < range.start || bar.start > range.end)));
      const laneIndex = lane === -1 ? lanes[bar.week].length : lane;
      if (!lanes[bar.week][laneIndex]) lanes[bar.week][laneIndex] = [];
      lanes[bar.week][laneIndex].push({ start: bar.start, end: bar.end });
      bar.lane = laneIndex;
    });

    return { weeks: Array.from({ length: days.length / 7 }, (_, i) => days.slice(i * 7, i * 7 + 7)), bars: placed };
  }, [entries, month]);

  const changeMonth = delta => setMonth(current => new Date(current.getFullYear(), current.getMonth() + delta, 1));

  return (
    <Panel className="overflow-hidden p-0">
      <div className="flex items-center justify-between px-5 py-4 sm:px-6 border-b border-slate-800">
        <div>
          <h2 className="text-base font-semibold text-slate-100">Reading calendar</h2>
          <p className="mt-0.5 text-xs text-slate-400">Shows the top 3 books each day; consecutive days are joined.</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => changeMonth(-1)} className="calendar-nav" aria-label="Previous month">‹</button>
          <span className="w-32 text-center text-sm font-medium text-slate-200">{monthLabel(month)}</span>
          <button onClick={() => changeMonth(1)} className="calendar-nav" aria-label="Next month">›</button>
        </div>
      </div>
      <div className="overflow-x-auto">
        <div className="min-w-[700px] p-3 sm:p-4">
          <div className="grid grid-cols-7 border-l border-t border-slate-800/80">
            {WEEKDAYS.map(day => <div key={day} className="border-b border-r border-slate-800/80 py-2 text-center text-[11px] font-medium uppercase tracking-wider text-slate-500">{day}</div>)}
            {weeks.flat().map((day, index) => <div key={toKey(day)} style={{ gridColumn: (index % 7) + 1, gridRow: 2 + Math.floor(index / 7) }} className={`calendar-day ${day.getMonth() === month.getMonth() ? '' : 'calendar-day--outside'}`}><time>{day.getDate()}</time></div>)}
            {bars.map(bar => (
              <div
                key={`${bar.entry.bookId}-${bar.start}`}
                title={`${bar.entry.title} · ${bar.entry.minutes} min`}
                className={`calendar-event ${colorFor(bar.entry.bookId)}`}
                style={{ gridColumn: `${(bar.start % 7) + 1} / span ${bar.length}`, gridRow: `${2 + bar.week}`, transform: `translateY(${22 + bar.lane * 22}px)` }}
              >
                <span>{bar.entry.title}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Panel>
  );
}
