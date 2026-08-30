'use client';

import { useState, useEffect, use } from 'react';
import { getStudentDetails } from '@/src/lib/api';
import { ArrowLeft, User, BookOpen, Award, CheckCircle2, XCircle } from 'lucide-react';
import Link from 'next/link';

export default function StudentReport({ params }: { params: Promise<{ id: string }> }) {
  const unwrappedParams = use(params);
  
  const [student, setStudent] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function fetchData() {
      try {
        const data = await getStudentDetails(unwrappedParams.id);
        setStudent(data);
      } catch (err: any) {
        setError('Failed to load student details.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [unwrappedParams.id]);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center p-8">
        <div className="animate-spin w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  if (error || !student) {
    return (
      <div className="p-8">
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl">
          {error || 'Student not found.'}
        </div>
      </div>
    );
  }

  const latestSemester = student.semesters[0] || null;

  return (
    <div className="min-h-full p-8 pb-20 max-w-5xl mx-auto space-y-6">
      
      <div className="flex items-center gap-4 mb-8 print:hidden">
        <Link href="/" className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-white">Student Report</h1>
          <p className="text-slate-400 text-sm">Detailed academic profile</p>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 flex flex-col md:flex-row justify-between items-start md:items-center gap-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 pointer-events-none"></div>
        
        <div className="flex items-center gap-6 relative z-10">
          <div className="w-20 h-20 bg-indigo-600 rounded-2xl flex items-center justify-center shadow-lg border border-indigo-500/50">
            <User className="w-10 h-10 text-white" />
          </div>
          <div>
            <h2 className="text-3xl font-bold text-white mb-1">{student.name}</h2>
            <div className="flex items-center gap-4 text-slate-400 font-medium">
              <span className="bg-slate-800 px-3 py-1 rounded-md border border-slate-700">{student.register_number}</span>
              <span>{student.gender !== 'Unknown' ? student.gender : 'B.Sc Computer Science'}</span>
            </div>
          </div>
        </div>

        {latestSemester && (
          <div className="flex gap-4 relative z-10">
            <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 text-center min-w-[120px]">
              <p className="text-slate-400 text-xs font-medium mb-1">Total Score</p>
              <p className="text-2xl font-bold text-indigo-400">{latestSemester.total_score}</p>
            </div>
            <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 text-center min-w-[120px]">
              <p className="text-slate-400 text-xs font-medium mb-1">Average</p>
              <p className="text-2xl font-bold text-emerald-400">{latestSemester.average_score}%</p>
            </div>
            <div className={`border rounded-xl p-4 text-center min-w-[120px] flex flex-col justify-center items-center ${
              latestSemester.status.toUpperCase() === 'PASS' 
                ? 'bg-emerald-950/30 border-emerald-900/50 text-emerald-400'
                : 'bg-red-950/30 border-red-900/50 text-red-400'
            }`}>
              {latestSemester.status.toUpperCase() === 'PASS' ? (
                <>
                  <CheckCircle2 className="w-6 h-6 mb-1" />
                  <span className="font-bold">PASSED</span>
                </>
              ) : (
                <>
                  <XCircle className="w-6 h-6 mb-1" />
                  <span className="font-bold">FAILED</span>
                </>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="space-y-6">
        <h3 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-indigo-400" /> Academic Results
        </h3>
        
        {student.semesters.map((sem: any) => (
          <div key={sem.id} className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
            <div className="bg-slate-800/50 p-4 border-b border-slate-800 flex justify-between items-center">
              <h4 className="font-semibold text-slate-300">Semester {sem.semester_number || 'Current'}</h4>
              <span className="text-sm text-slate-400">SGPA: <span className="font-bold text-indigo-300">{sem.sgpa}</span></span>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-900/80 text-slate-400 text-xs border-b border-slate-800">
                  <tr>
                    <th className="p-4 font-medium">Subject Code</th>
                    <th className="p-4 font-medium">Subject Name</th>
                    <th className="p-4 font-medium">Marks</th>
                    <th className="p-4 font-medium">Grade</th>
                    <th className="p-4 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {sem.subjects.map((sub: any, idx: number) => (
                    <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                      <td className="p-4 text-slate-400 font-mono text-xs">{sub.code}</td>
                      <td className="p-4 text-slate-200 font-medium">{sub.name}</td>
                      <td className="p-4 text-slate-300 font-semibold">{sub.marks}</td>
                      <td className="p-4">
                        <span className={`px-2 py-1 rounded text-xs font-bold ${
                          sub.grade === 'O' || sub.grade === 'A+' ? 'bg-amber-500/20 text-amber-400' :
                          sub.grade === 'A' || sub.grade === 'B+' ? 'bg-emerald-500/20 text-emerald-400' :
                          sub.grade === 'B' || sub.grade === 'C' ? 'bg-blue-500/20 text-blue-400' :
                          'bg-red-500/20 text-red-400'
                        }`}>
                          {sub.grade}
                        </span>
                      </td>
                      <td className="p-4">
                        <span className={`text-xs font-bold ${sub.status.toUpperCase() === 'PASS' ? 'text-emerald-400' : 'text-red-400'}`}>
                          {sub.status.toUpperCase()}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
