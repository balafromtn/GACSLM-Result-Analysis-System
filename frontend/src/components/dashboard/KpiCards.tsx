import { Users, CheckCircle, XCircle, Percent, Trophy, ArrowDown } from 'lucide-react';

export default function KpiCards({ metrics }: { metrics: any }) {
  if (!metrics) return null;

  const cards = [
    { title: 'Total Students', value: metrics.total_completed || 0, icon: Users, color: 'text-blue-400', bg: 'bg-blue-400/10' },
    { title: 'Passed', value: metrics.passed || 0, icon: CheckCircle, color: 'text-emerald-400', bg: 'bg-emerald-400/10' },
    { title: 'Failed', value: metrics.failed || 0, icon: XCircle, color: 'text-red-400', bg: 'bg-red-400/10' },
    { title: 'Pass Rate', value: `${metrics.pass_percentage || 0}%`, icon: Percent, color: 'text-indigo-400', bg: 'bg-indigo-400/10' },
    { title: 'Class Avg', value: `${metrics.average_sgpa || 0} / 10`, icon: Trophy, color: 'text-amber-400', bg: 'bg-amber-400/10' },
    { title: 'Highest / Lowest', value: `${metrics.highest_mark || 0} / ${metrics.lowest_mark || 0}`, icon: ArrowDown, color: 'text-purple-400', bg: 'bg-purple-400/10' }
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {cards.map((card, i) => (
        <div key={i} className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
          <div className="flex justify-between items-start mb-4">
            <p className="text-slate-400 text-xs font-medium">{card.title}</p>
            <div className={`p-1.5 rounded-lg ${card.bg}`}>
              <card.icon className={`w-4 h-4 ${card.color}`} />
            </div>
          </div>
          <p className="text-2xl font-bold text-white">{card.value}</p>
        </div>
      ))}
    </div>
  );
}
