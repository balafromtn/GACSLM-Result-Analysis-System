'use client';

import { useState, useEffect } from 'react';
import KpiCards from '@/src/components/dashboard/KpiCards';
import DistributionChart from '@/src/components/dashboard/DistributionChart';
import TrendChart from '@/src/components/dashboard/TrendChart';
import PassFailPieChart from '@/src/components/dashboard/PassFailPieChart';
import GenderPerformanceChart from '@/src/components/dashboard/GenderPerformanceChart';
import CommunityChart from '@/src/components/dashboard/CommunityChart';
import ChatPanel from '@/src/components/dashboard/ChatPanel';
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
  getGenderPerformance,
  getCommunityPerformance,
  getScrapingStatus
} from '@/src/lib/api';
import { Upload, CheckCircle2, AlertCircle, RefreshCw, Printer, Loader2, XCircle, Circle, CircleDot, Check } from 'lucide-react';

export default function Dashboard() {
  const [academicBatch, setAcademicBatch] = useState('');
  const [programme, setProgramme] = useState('');
  const [branch, setBranch] = useState('');
  const [semester, setSemester] = useState('');
  const workspaceName = (academicBatch && programme && branch && semester) 
    ? `${academicBatch}-${programme}-${branch}-${semester}`
    : '';
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
  const [communityData, setCommunityData] = useState<any>(null);
  const [insights, setInsights] = useState<any>(null);
  
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [scrapingStatuses, setScrapingStatuses] = useState<any[]>([]);

  // Polling for scraping status
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    const checkStatus = async () => {
      if (!activeWorkspaceId) return;
      try {
        const data = await getScrapingStatus(activeWorkspaceId.toString());
        setScrapingStatuses(data.students || []);
        
        // Check if all are completed or failed
        const isDone = data.students.length > 0 && data.students.every((s: any) => 
          s.status === 'completed' || s.status === 'failed'
        );
        
        if (isDone && !summary) {
          fetchDashboardData(activeWorkspaceId);
        }
      } catch (e) {
        console.error("Error fetching scraping status:", e);
      }
    };

    if (activeWorkspaceId && !summary) {
      checkStatus();
      interval = setInterval(checkStatus, 3000); // poll every 3s
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [activeWorkspaceId, summary]);

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

      const community = await getCommunityPerformance(workspaceId);
      setCommunityData(community.communities);

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

  const handleLoadWorkspace = async () => {
    if (!workspaceName) {
      setMessage('Please select all dropdown options to identify the workspace.');
      return;
    }
    
    setLoading(true);
    setMessage('');
    
    try {
      // Just try fetching dashboard data. If it fails (404), it doesn't exist yet.
      await fetchDashboardData(workspaceName);
      setActiveWorkspaceId(workspaceName);
      setMessage(`✅ Loaded workspace ${workspaceName}`);
    } catch (err: any) {
      if (err.response?.status === 404) {
        setMessage(`Workspace ${workspaceName} not found. Please upload a dataset to create it.`);
      } else {
        setMessage(`Error loading workspace: ${err.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!academicBatch || !programme || !branch || !semester || !file) {
      setMessage('Please select all dropdown options and provide a file.');
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
    if (!activeWorkspaceId) return;
    window.open(`http://localhost:8000/api/v1/analytics/${encodeURIComponent(activeWorkspaceId.toString())}/report/download`, '_blank');
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
              <div className="md:col-span-2 grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Academic Batch</label>
                  <select
                    value={academicBatch}
                    onChange={(e) => setAcademicBatch(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-slate-100 focus:outline-none focus:border-indigo-500 appearance-none"
                  >
                    <option value="">Select Batch</option>
                    <option value="2024">2024</option>
                    <option value="2025">2025</option>
                    <option value="2026">2026</option>
                    <option value="2027">2027</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Programme</label>
                  <select
                    value={programme}
                    onChange={(e) => setProgramme(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-slate-100 focus:outline-none focus:border-indigo-500 appearance-none"
                  >
                    <option value="">Select Prog</option>
                    <option value="B.Sc">B.Sc</option>
                    <option value="B.A">B.A</option>
                    <option value="B.Com">B.Com</option>
                    <option value="BBA">BBA</option>
                    <option value="BCA">BCA</option>
                    <option value="M.Sc">M.Sc</option>
                    <option value="M.A">M.A</option>
                    <option value="M.Com">M.Com</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Branch</label>
                  <select
                    value={branch}
                    onChange={(e) => setBranch(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-slate-100 focus:outline-none focus:border-indigo-500 appearance-none"
                  >
                    <option value="">Select Branch</option>
                    <option value="Computer Science">Computer Science</option>
                    <option value="Mathematics">Mathematics</option>
                    <option value="Physics">Physics</option>
                    <option value="Chemistry">Chemistry</option>
                    <option value="English">English</option>
                    <option value="History">History</option>
                    <option value="Commerce">Commerce</option>
                    <option value="Business Administration">Business Administration</option>
                    <option value="Information Technology">Information Technology</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Semester</label>
                  <select
                    value={semester}
                    onChange={(e) => setSemester(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-slate-100 focus:outline-none focus:border-indigo-500 appearance-none"
                  >
                    <option value="">Select Sem</option>
                    <option value="I">I</option>
                    <option value="II">II</option>
                    <option value="III">III</option>
                    <option value="IV">IV</option>
                    <option value="V">V</option>
                    <option value="VI">VI</option>
                  </select>
                </div>
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-slate-300 mb-1">Dataset File (.csv or .xlsx)</label>
                <input
                  type="file"
                  accept=".csv, .xlsx"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="w-full text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-700 cursor-pointer"
                />
              </div>
            </div>

            <div className="flex gap-4">
              <button
                type="button"
                onClick={handleLoadWorkspace}
                disabled={loading || !academicBatch || !programme || !branch || !semester}
                className="w-1/2 bg-slate-800 hover:bg-slate-700 text-white font-medium py-2 rounded-lg transition-colors disabled:opacity-50 border border-slate-700"
              >
                {loading ? 'Loading...' : 'Load Existing Workspace'}
              </button>
              
              <button
                type="submit"
                disabled={loading || !file}
                className="w-1/2 bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-2 rounded-lg transition-colors disabled:opacity-50"
              >
                {loading ? 'Processing...' : 'Upload & Scrape New'}
              </button>
            </div>
          </form>

          {message && (
            <div className={`mt-4 p-3 rounded-lg text-sm flex items-center gap-2 ${message.includes('failed') ? 'bg-red-950/50 border border-red-900 text-red-300' : 'bg-emerald-950/50 border border-emerald-900 text-emerald-300'}`}>
              {message.includes('failed') ? <AlertCircle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
              {message}
            </div>
          )}
        </div>
      </div>

      {/* Detailed Sleek Loading State */}
      {activeWorkspaceId && !summary && (
        <div className="max-w-4xl mx-auto bg-[#0f111a] border border-[#1a1b26] rounded-xl p-8 shadow-2xl print:hidden">
          
          {(() => {
            const total = scrapingStatuses.length;
            const completed = scrapingStatuses.filter(s => s.status === 'completed' || s.status === 'failed').length;
            const percent = total > 0 ? Math.round((completed / total) * 100) : 0;
            const currentScraping = scrapingStatuses.find(s => s.status === 'scraping');
            
            return (
              <div className="mb-8">
                <div className="flex justify-between items-end mb-3">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl font-bold text-indigo-400">{completed} <span className="text-slate-500 text-lg font-medium">/ {total || '--'}</span></span>
                    {currentScraping && (
                      <>
                        <span className="text-slate-600">•</span>
                        <span className="text-slate-400 text-sm">Now: <span className="text-cyan-400 font-semibold">{currentScraping.register_number}</span></span>
                      </>
                    )}
                  </div>
                  <div className="text-indigo-400 font-bold text-xl">{percent}%</div>
                </div>
                
                <div className="w-full h-2.5 bg-[#1a1b26] rounded-full overflow-hidden border border-slate-800/50">
                  <div 
                    className="h-full bg-gradient-to-r from-indigo-500 to-purple-400 transition-all duration-500 ease-out rounded-full"
                    style={{ width: `${percent}%` }}
                  ></div>
                </div>
              </div>
            );
          })()}
          
          <div className="space-y-3 max-h-[28rem] overflow-y-auto pr-2 custom-scrollbar">
            {scrapingStatuses.length === 0 ? (
              <div className="text-center text-slate-500 py-12">Initializing scraper...</div>
            ) : (
              scrapingStatuses.map((s: any) => {
                const isCompleted = s.status === 'completed';
                const isFailed = s.status === 'failed';
                const isScraping = s.status === 'scraping';
                const isPending = s.status === 'pending';
                
                return (
                  <div 
                    key={s.register_number} 
                    className={`flex items-center gap-4 p-4 rounded-lg border transition-all ${
                      isScraping 
                        ? 'bg-[#1a1b26] border-indigo-500/30 shadow-[0_0_15px_rgba(99,102,241,0.1)]' 
                        : 'bg-[#13141f] border-transparent'
                    }`}
                  >
                    <div className="shrink-0 flex items-center justify-center">
                      {isCompleted && <Check className="w-5 h-5 text-emerald-400" />}
                      {isFailed && <XCircle className="w-5 h-5 text-red-400" />}
                      {isScraping && (
                        <div className="relative flex items-center justify-center">
                          <div className="absolute w-4 h-4 rounded-full bg-cyan-400/20 animate-ping"></div>
                          <CircleDot className="w-5 h-5 text-cyan-400 relative z-10" />
                        </div>
                      )}
                      {isPending && <Circle className="w-5 h-5 text-slate-600" />}
                    </div>
                    
                    <span className={`font-semibold tracking-wide flex-1 ${
                      isCompleted ? 'text-emerald-400' 
                      : isFailed ? 'text-red-400' 
                      : isScraping ? 'text-cyan-400' 
                      : 'text-slate-600'
                    }`}>
                      {s.register_number}
                    </span>
                    
                    {isFailed && (
                      <span className="text-xs text-red-400/70 max-w-[200px] truncate">{s.error}</span>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}

      {/* Full Dashboard */}
      {summary && summary.metrics && (
        <div className="space-y-8 animate-in fade-in duration-500 max-w-7xl mx-auto">
          
          <div className="flex justify-between items-end print:hidden">
            <div>
              <div className="text-xs font-bold tracking-widest text-indigo-400 uppercase mb-1">Government Arts College (Autonomous), Salem</div>
              <h1 className="text-2xl font-bold text-slate-100">Class Performance Overview</h1>
              <p className="text-sm text-slate-400 mt-1">Detailed analysis and insights for <span className="text-slate-300 font-medium">{activeWorkspaceId}</span></p>
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
              <div className="lg:col-span-1 flex flex-col gap-6">
                <AttentionRequired alerts={insights.attention_required} />
                <ChatPanel workspaceId={activeWorkspaceId.toString()} />
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

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm transition-colors">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-6">Pass/Fail Ratio</h3>
              {passFailData && <PassFailPieChart passed={passFailData.passed} failed={passFailData.failed} />}
            </div>
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm transition-colors">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-6">Gender Performance</h3>
              {genderData && <GenderPerformanceChart data={genderData} />}
            </div>
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm transition-colors">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-6">Community Performance</h3>
              {communityData && <CommunityChart data={communityData} />}
            </div>
          </div>

          {/* Level 3: Student Details */}
          <StudentTable students={students} />

        </div>
      )}
    </div>
  );
}