"use client";

import { useState } from 'react';
import { Send, Bot, Loader2 } from 'lucide-react';
import { getWorkspaceChat } from '@/src/lib/api';

export default function ChatPanel({ workspaceId }: { workspaceId: string }) {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<{role: 'user' | 'bot', text: string}[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!query.trim()) return;

    const userQuery = query.trim();
    setMessages(prev => [...prev, { role: 'user', text: userQuery }]);
    setQuery('');
    setLoading(true);

    try {
      const data = await getWorkspaceChat(workspaceId, userQuery);
      setMessages(prev => [...prev, { role: 'bot', text: data.response }]);
    } catch (err: any) {
      setMessages(prev => [...prev, { role: 'bot', text: `Error: ${err.response?.data?.detail || err.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-[#0f111a] border border-[#1a1b26] rounded-2xl overflow-hidden flex flex-col h-[500px]">
      <div className="bg-[#1a1b26] p-4 border-b border-[#2a2b36] flex items-center gap-3">
        <Bot className="w-6 h-6 text-indigo-400" />
        <div>
          <h3 className="font-semibold text-slate-200">Academic Assistant</h3>
          <p className="text-xs text-slate-500">Ask questions about this specific class's performance</p>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar bg-[#13141f]">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center text-slate-500 text-sm text-center px-4">
            I'm ready to answer questions about this workspace! Try asking "What is the pass rate?" or "How many students failed?"
          </div>
        ) : (
          messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-xl px-4 py-3 text-sm leading-relaxed ${
                m.role === 'user' 
                  ? 'bg-indigo-600 text-white rounded-tr-sm' 
                  : 'bg-[#1a1b26] border border-[#2a2b36] text-slate-200 rounded-tl-sm'
              }`}>
                {m.text}
              </div>
            </div>
          ))
        )}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-[#1a1b26] border border-[#2a2b36] rounded-xl px-4 py-3 rounded-tl-sm">
              <Loader2 className="w-5 h-5 text-indigo-400 animate-spin" />
            </div>
          </div>
        )}
      </div>
      
      <div className="p-4 bg-[#1a1b26] border-t border-[#2a2b36]">
        <form 
          onSubmit={(e) => { e.preventDefault(); handleSend(); }}
          className="flex gap-2"
        >
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about this class..."
            className="flex-1 bg-[#13141f] border border-[#2a2b36] rounded-lg px-4 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="bg-indigo-600 hover:bg-indigo-500 text-white p-2 rounded-lg transition-colors disabled:opacity-50"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  );
}
