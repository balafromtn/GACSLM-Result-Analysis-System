'use client';

import { useState, useEffect } from 'react';
import KpiCards from '@/src/components/dashboard/KpiCards';
import DistributionChart from '@/src/components/dashboard/DistributionChart';
import TrendChart from '@/src/components/dashboard/TrendChart';
import PassFailPieChart from '@/src/components/dashboard/PassFailPieChart';
import GenderPerformanceChart from '@/src/components/dashboard/GenderPerformanceChart';
import StudentTable from '@/src/components/dashboard/StudentTable';
import AiInsights from '@/src/components/dashboard/AiInsights';
import AttentionRequired from '@/src/components/dashboard/AttentionRequired';
import { 
  uploadStudentCsv, 
  getWorkspaceSummary, 
  getWorkspaceStudents,
  getWorkspaceSubjects,
  getWorkspaceDistribution,
  getWorkspaceInsights,
  getPassFailDistribution,
  getGenderPerformance
} from '@/src/lib/api';
import { Upload, CheckCircle2, AlertCircle, RefreshCw, Printer } from 'lucide-react';

export default function Dashboard() {
  const [workspaceName, setWorkspaceName] = useState('');
  const [activeWorkspaceId, setActiveWorkspaceId] = useState<string | number | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  
  // Data States
  const [summary, setSummary] = useState<any>(null);
  const [students, setStudents] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [distribution, setDistribution] = useState<any>(null);
  const [passFailData, setPassFailData] = useState<any>(null);
  const [genderData, setGenderData] = useState<any>(null);
  const [insights, setInsights] = useState<any>(null);
  
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchDashboardData = async (workspaceId: string | number) => {
    try {
      const summaryData = await getWorkspaceSummary(workspaceId);
      setSummary(summaryData);
      
      const studentsData = await getWorkspaceStudents(workspaceId);
      setStudents(studentsData.students || []);

      const subjectsData = await getWorkspaceSubjects(workspaceId);
      setSubjects(subjectsData.subjects || []);

      const distData = await getWorkspaceDistribution(workspaceId);
      setDistribution(distData.distribution || null);

      const passFail = await getPassFailDistribution(workspaceId);
      setPassFailData(passFail);

      const gender = await getGenderPerformance(workspaceId);
      setGenderData(gender);

      const insightsData = await getWorkspaceInsights(workspaceId);
      setInsights(insightsData);
      
    } catch (err: any) {
      if (err.response?.status === 404) {
        console.log("Data is still processing in the background...");
      } else {
        console.error("Failed to fetch dashboard data:", err);
      }
    }
  };

  const handleRefresh = async () => {
    const idToFetch = activeWorkspaceId || workspaceName;
    if (!idToFetch) return;
    setIsRefreshing(true);
    await fetchDashboardData(idToFetch);
    setIsRefreshing(false);
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!workspaceName || !file) {
      setMessage('Please provide a workspace name and select a file.');
      return;
    }

    setLoading(true);
    setMessage('');
    setSummary(null);

    try {
      const data = await uploadStudentCsv(workspaceName, file);
      setMessage(`✅ ${data.message || 'Upload successful!'}`);
      
      const targetId = data.workspace_id || workspaceName;
      setActiveWorkspaceId(targetId);
      
      await fetchDashboardData(targetId);
      
    } catch (err: any) {
      console.error("Full upload error:", err);
      const errorDetail = err.response?.data?.detail || err.message || JSON.stringify(err);
      setMessage(`Upload failed: ${errorDetail}`);
    } finally {
      setLoading(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="min-h-full p-8 pb-20">
      
      {/* Upload Section - Hidden when printing */}
      <div className="max-w-4xl mx-auto space-y-6 mb-12 print:hidden">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2 text-slate-200">
            <Upload className="w-5 h-5 text-indigo-400" /> Ingest Student Records
          </h2>

          <form onSubmit={handleUpload} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
      </div>

      {/* Loading State */}
      {activeWorkspaceId && !summary && (
        <div className="max-w-4xl mx-auto bg-indigo-950/30 border border-indigo-900/50 rounded-xl p-8 text-center space-y-4 shadow-inner print:hidden">
          <div className="animate-pulse flex justify-center mb-2">
            <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
          <h3 className="text-lg font-medium text-indigo-200">Scraping in progress...</h3>
          <p className="text-slate-400 text-sm max-w-md mx-auto">
            The backend is extracting student results. Click refresh below to check if data is ready.
          </p>
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="mt-4 mx-auto flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-6 py-2 rounded-lg transition-colors text-sm font-medium shadow-md"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            {isRefreshing ? 'Checking Database...' : 'Check Status / Refresh'}
          </button>
        </div>
      )}

      {/* Full Dashboard */}
      {summary && summary.metrics && (
        <div className="space-y-8 animate-in fade-in duration-500 max-w-7xl mx-auto">
          
          <div className="flex justify-between items-end print:hidden">
            <div>
              <h1 className="text-2xl font-bold text-slate-100">Class Performance Overview</h1>
              <p className="text-sm text-slate-400 mt-1">Detailed analysis and insights for {workspaceName}</p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={handlePrint}
                className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 px-4 py-2 rounded-lg transition-colors text-sm font-medium border border-slate-700 shadow-sm"
              >
                <Printer className="w-4 h-4" /> Export HTML/PDF
              </button>
              <button
                onClick={handleRefresh}
                disabled={isRefreshing}
                className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg transition-colors text-sm font-medium shadow-sm"
              >
                <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                {isRefreshing ? 'Refreshing...' : 'Refresh Data'}
              </button>
            </div>
          </div>

          {/* Level 1: KPIs */}
          <KpiCards metrics={summary.metrics} />

          {/* AI Insights & Attention Required */}
          {insights && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <AiInsights insights={insights.insights} />
              </div>
              <div className="lg:col-span-1">
                <AttentionRequired alerts={insights.attention_required} />
              </div>
            </div>
          )}

          {/* Level 2: Charts & Distributions */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            <div className="lg:col-span-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm transition-colors">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-6">Performance Distribution</h3>
              <DistributionChart distribution={distribution} />
            </div>
            <div className="lg:col-span-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm transition-colors">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-6">Subject Averages</h3>
              <TrendChart subjects={subjects} />
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm transition-colors">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-6">Pass/Fail Ratio</h3>
              {passFailData && <PassFailPieChart passed={passFailData.passed} failed={passFailData.failed} />}
            </div>
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm transition-colors">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-6">Gender Performance</h3>
              {genderData && <GenderPerformanceChart data={genderData} />}
            </div>
          </div>

          {/* Level 3: Student Details */}
          <StudentTable students={students} />

        </div>
      )}
    </div>
  );
}