'use client';

import { Search } from 'lucide-react';
import { useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';

export default function StudentTable({ students }: { students: any[] }) {
  const router = useRouter();
  const [search, setSearch] = useState('');

  // Extract all unique subjects to create columns
  const subjectColumns = useMemo(() => {
    const subs = new Map();
    students?.forEach(student => {
      student.semesters?.[0]?.subjects?.forEach((sub: any) => {
        subs.set(sub.code, sub.name);
      });
    });
    return Array.from(subs.entries()).map(([code, name]) => ({ code, name }));
  }, [students]);

  const filteredStudents = useMemo(() => {
    if (!students) return [];
    if (!search) return students;
    const lower = search.toLowerCase();
    return students.filter(s => 
      s.name.toLowerCase().includes(lower) || 
      s.register_number.toLowerCase().includes(lower)
    );
  }, [students, search]);

  if (!students || students.length === 0) return (
    <div className="p-8 text-center text-slate-500">Waiting for data...</div>
  );

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden transition-colors duration-300">
      <div className="p-6 border-b border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-white">Detailed Result Analysis</h3>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Comprehensive subject-wise performance matrix</p>
        </div>
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input 
            type="text" 
            placeholder="Search student..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 pr-4 py-2 bg-slate-100 dark:bg-slate-800/50 border border-transparent focus:border-indigo-500/30 rounded-lg text-sm w-full sm:w-64 outline-none text-slate-900 dark:text-slate-200 placeholder:text-slate-500 transition-all focus:bg-white dark:focus:bg-slate-800 focus:shadow-sm"
          />
        </div>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm whitespace-nowrap">
          <thead className="bg-slate-50 dark:bg-slate-900/80 text-slate-500 dark:text-slate-400 text-xs border-b border-slate-200 dark:border-slate-800">
            <tr>
              <th className="p-4 font-semibold sticky left-0 bg-slate-50 dark:bg-slate-900/90 z-10 w-12">S.No</th>
              <th className="p-4 font-semibold sticky left-12 bg-slate-50 dark:bg-slate-900/90 z-10 shadow-[10px_0_15px_-3px_rgba(0,0,0,0.05)] dark:shadow-[10px_0_15px_-3px_rgba(0,0,0,0.2)]">Student Info</th>
              
              {subjectColumns.map(sub => (
                <th key={sub.code} className="p-4 font-semibold text-center border-l border-slate-200 dark:border-slate-800" title={sub.name}>
                  {sub.code}<br/>
                  <span className="text-[10px] font-normal opacity-70 truncate max-w-[100px] inline-block">{sub.name}</span>
                </th>
              ))}
              
              <th className="p-4 font-semibold text-center border-l border-slate-200 dark:border-slate-800">Overall %</th>
              <th className="p-4 font-semibold text-center">Grading</th>
              <th className="p-4 font-semibold text-center">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-800/50">
            {filteredStudents.map((student, idx) => {
              const sem = student.semesters?.[0] || {};
              const subjectsMap = new Map(sem.subjects?.map((s: any) => [s.code, s]) || []);
              
              return (
                <tr 
                  key={student.id} 
                  onClick={() => router.push(`/student/${student.id}`)}
                  className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors group cursor-pointer"
                >
                  <td className="p-4 text-slate-500 dark:text-slate-400 font-mono text-xs sticky left-0 bg-white dark:bg-slate-900 group-hover:bg-slate-50 dark:group-hover:bg-slate-800/90 z-10">{idx + 1}</td>
                  <td className="p-4 sticky left-12 bg-white dark:bg-slate-900 group-hover:bg-slate-50 dark:group-hover:bg-slate-800/90 z-10 shadow-[10px_0_15px_-3px_rgba(0,0,0,0.05)] dark:shadow-[10px_0_15px_-3px_rgba(0,0,0,0.2)]">
                    <div className="font-medium text-slate-900 dark:text-slate-200">{student.name}</div>
                    <div className="text-xs text-indigo-500 dark:text-indigo-400 font-mono mt-0.5">{student.register_number}</div>
                  </td>
                  
                  {subjectColumns.map(col => {
                    const subData = subjectsMap.get(col.code);
                    return (
                      <td key={col.code} className="p-4 text-center border-l border-slate-100 dark:border-slate-800/50">
                        {subData ? (
                          <span className={`font-semibold ${
                            subData.status.toUpperCase() === 'PASS' 
                              ? 'text-slate-700 dark:text-slate-300' 
                              : subData.status.toUpperCase() === 'ABSENT' ? 'text-amber-500 dark:text-amber-400'
                              : 'text-rose-500 dark:text-rose-400'
                          }`}>
                            {subData.marks}
                          </span>
                        ) : (
                          <span className="text-slate-300 dark:text-slate-600 font-bold">-</span>
                        )}
                      </td>
                    );
                  })}
                  
                  <td className="p-4 text-center font-bold text-slate-700 dark:text-slate-200 border-l border-slate-100 dark:border-slate-800/50">
                    {sem.average_score || 0}%
                  </td>
                  <td className="p-4 text-center">
                    <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                      sem.average_score >= 90 ? 'bg-amber-100 dark:bg-amber-400/20 text-amber-600 dark:text-amber-400' :
                      sem.average_score >= 80 ? 'bg-emerald-100 dark:bg-emerald-400/20 text-emerald-600 dark:text-emerald-400' :
                      sem.average_score >= 60 ? 'bg-blue-100 dark:bg-blue-400/20 text-blue-600 dark:text-blue-400' :
                      'bg-rose-100 dark:bg-rose-400/20 text-rose-600 dark:text-rose-400'
                    }`}>
                      {sem.average_score >= 90 ? 'O' : sem.average_score >= 80 ? 'A+' : sem.average_score >= 70 ? 'A' : sem.average_score >= 60 ? 'B+' : sem.average_score >= 50 ? 'B' : sem.average_score >= 40 ? 'C' : 'U'}
                    </span>
                  </td>
                  <td className="p-4 text-center">
                    {sem.status?.toUpperCase() === 'PASS' ? (
                      <span className="text-emerald-500 dark:text-emerald-400 text-xs font-bold">PASS</span>
                    ) : (
                      <span className="text-rose-500 dark:text-rose-400 text-xs font-bold">FAIL</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
