'use client';

export default function TopPerformers({ students }: { students: any[] }) {
  if (!students || students.length === 0) return null;

  const top3 = students.slice(0, 3);
  const medals = ['🥇', '🥈', '🥉'];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-sm font-semibold text-slate-300">Top Performers</h3>
        <button className="text-xs text-indigo-400 hover:text-indigo-300">View Full Ranking</button>
      </div>
      
      <div className="space-y-3">
        {top3.map((student, idx) => (
          <div key={student.id} className="flex items-center justify-between p-3 bg-slate-950 rounded-lg border border-slate-800/50">
            <div className="flex items-center gap-3">
              <span className="text-xl">{medals[idx]}</span>
              <div>
                <p className="text-sm font-medium text-slate-200">{student.name}</p>
                <p className="text-xs text-slate-500">{student.register_number}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm font-bold text-indigo-400">{student.average}%</p>
              <p className="text-[10px] text-emerald-400 font-medium">Excellent</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
