'use client';

import { useState } from 'react';
import { uploadStudentCsv, getWorkspaceSummary } from '@/src/lib/api';
import { Upload, CheckCircle2, AlertCircle, BarChart3, Users } from 'lucide-react';

export default function Dashboard() {
  const [workspaceName, setWorkspaceName] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [summary, setSummary] = useState<any>(null);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!workspaceName || !file) {
      setMessage('Please provide a workspace name and select a file.');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const data = await uploadStudentCsv(workspaceName, file);
      setMessage(`Successfully queued ${data.message}`);
      
      // Fetch summary metrics after successful upload/queue initialization
      if (data.workspace_id) {
        setTimeout(async () => {
          const stats = await getWorkspaceSummary(data.workspace_id);
          setSummary(stats);
        }, 1500);
      }
    } catch (err: any) {
      console.error("Full upload error:", err);
      // Safely extract the error message whether it's a string, Axios object, or standard Error
      const errorDetail = 
        err.response?.data?.detail || 
        err.message || 
        JSON.stringify(err);
      
      setMessage(`Upload failed: ${errorDetail}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="border-b border-slate-800 pb-4">
          <h1 className="text-3xl font-bold tracking-tight">Academic Intelligence Dashboard</h1>
          <p className="text-slate-400 mt-1">Upload class result spreadsheets to generate automated insights and analytics.</p>
        </div>

        {/* Upload Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Upload className="w-5 h-5 text-indigo-400" /> Ingest Student Records
          </h2>

          <form onSubmit={handleUpload} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Workspace / Class Name</label>
              <input
                type="text"
                placeholder="e.g., BCA Semester 4 - 2026"
                value={workspaceName}
                onChange={(e) => setWorkspaceName(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-slate-100 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Dataset File (.csv or .xlsx)</label>
              <input
                type="file"
                accept=".csv, .xlsx"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="w-full text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-700 cursor-pointer"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-2 rounded-lg transition-colors disabled:opacity-50"
            >
              {loading ? 'Processing & Scraping...' : 'Upload & Trigger Scraper'}
            </button>
          </form>

          {message && (
            <div className={`mt-4 p-3 rounded-lg text-sm flex items-center gap-2 ${message.includes('failed') ? 'bg-red-950/50 border border-red-900 text-red-300' : 'bg-emerald-950/50 border border-emerald-900 text-emerald-300'}`}>
              {message.includes('failed') ? <AlertCircle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
              {message}
            </div>
          )}
        </div>

        {/* Analytics Summary Section */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-sm font-medium">Total Students</span>
                <Users className="w-5 h-5 text-indigo-400" />
              </div>
              <div className="text-3xl font-bold">{summary.total_students}</div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-sm font-medium">Pass Percentage</span>
                <BarChart3 className="w-5 h-5 text-emerald-400" />
              </div>
              <div className="text-3xl font-bold text-emerald-400">{summary.metrics?.pass_percentage}%</div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-sm font-medium">Class Average SGPA</span>
                <span className="text-xs bg-indigo-950 text-indigo-300 px-2 py-0.5 rounded">GPA</span>
              </div>
              <div className="text-3xl font-bold text-indigo-400">{summary.metrics?.average_sgpa}</div>
            </div>
          </div>
        )}

      </div>
    </main>
  );
}