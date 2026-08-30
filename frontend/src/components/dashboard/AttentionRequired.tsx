'use client';

import { AlertTriangle } from 'lucide-react';

export default function AttentionRequired({ alerts }: { alerts: any[] }) {
  if (!alerts || alerts.length === 0) return null;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle className="w-4 h-4 text-amber-500" />
        <h3 className="text-sm font-semibold text-slate-300">
          ⚠️ {alerts.length} Students Require Attention
        </h3>
      </div>
      
      <div className="space-y-2 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
        {alerts.map((alert, idx) => (
          <div key={idx} className="flex justify-between items-center p-2 rounded-lg bg-amber-500/10 border border-amber-500/20">
            <div>
              <p className="text-xs font-medium text-amber-200">{alert.student}</p>
              <p className="text-[10px] text-amber-400/70">{alert.reason}</p>
            </div>
            <div className="text-xs font-bold text-amber-500 bg-amber-950 px-2 py-1 rounded">
              {alert.average}%
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
