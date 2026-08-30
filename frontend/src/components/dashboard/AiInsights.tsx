'use client';

import { Sparkles } from 'lucide-react';

export default function AiInsights({ insights }: { insights: string }) {
  if (!insights) return null;

  return (
    <div className="bg-gradient-to-br from-indigo-900/50 to-purple-900/50 border border-indigo-500/30 rounded-xl p-6 relative overflow-hidden">
      <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 rounded-full blur-2xl transform translate-x-1/2 -translate-y-1/2"></div>
      
      <div className="flex items-center gap-2 mb-3 relative z-10">
        <Sparkles className="w-5 h-5 text-indigo-400" />
        <h3 className="text-sm font-bold text-indigo-100">AI-Generated Insights</h3>
      </div>
      
      <div className="relative z-10">
        <p className="text-sm text-indigo-200/90 leading-relaxed italic">
          "{insights}"
        </p>
      </div>
    </div>
  );
}
