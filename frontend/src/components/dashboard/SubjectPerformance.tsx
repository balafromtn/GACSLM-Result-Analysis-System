'use client';

export default function SubjectPerformance({ subjects }: { subjects: any[] }) {
  if (!subjects || subjects.length === 0) return null;

  // Find highest and lowest to highlight
  const highest = Math.max(...subjects.map(s => s.average));
  const lowest = Math.min(...subjects.map(s => s.average));

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 overflow-hidden">
      <h3 className="text-sm font-semibold text-slate-300 mb-4">Subject-wise Performance</h3>
      <div className="space-y-4">
        {subjects.map((sub, idx) => {
          const isHighest = sub.average === highest;
          const isLowest = sub.average === lowest;
          
          return (
            <div key={idx} className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className={`font-medium flex items-center gap-2 ${isHighest ? 'text-emerald-400' : isLowest ? 'text-red-400' : 'text-slate-300'}`}>
                  {sub.name}
                  {isHighest && <span className="px-1.5 py-0.5 rounded text-[10px] bg-emerald-400/20 text-emerald-400">Best</span>}
                  {isLowest && <span className="px-1.5 py-0.5 rounded text-[10px] bg-red-400/20 text-red-400">Weakest</span>}
                </span>
                <span className="text-slate-400">{sub.average}% Avg • {sub.pass_rate}% Pass</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2 relative">
                <div 
                  className={`h-2 rounded-full ${isHighest ? 'bg-emerald-500' : isLowest ? 'bg-red-500' : 'bg-indigo-500'}`}
                  style={{ width: `${sub.average}%` }}
                ></div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
