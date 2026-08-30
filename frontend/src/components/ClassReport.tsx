'use client';

export default function ClassReport({ students, metrics }: { students: any[], metrics: any }) {
  // Fallback data if API hasn't loaded yet
  const studentList = students || [];
  
  return (
    <div className="space-y-8 mt-8">
      {/* Dynamic Insights Section */}
      <div className="bg-gradient-to-br from-indigo-900/50 to-purple-900/50 border border-indigo-500/30 p-8 rounded-2xl shadow-xl">
        <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          🔍 Key Insights & Analysis
        </h3>
        <ul className="space-y-3 text-indigo-100">
          <li className="flex items-start gap-2">
            <span className="text-indigo-400 font-bold">▶</span>
            Overall pass percentage of {metrics?.pass_percentage || 0}% indicates the current academic performance for this class.
          </li>
          <li className="flex items-start gap-2">
            <span className="text-indigo-400 font-bold">▶</span>
            A total of {metrics?.failed || 0} students require remedial support and guidance.
          </li>
          <li className="flex items-start gap-2">
            <span className="text-indigo-400 font-bold">▶</span>
            The class average SGPA is {metrics?.average_gpa || 0}, reflecting the overall cohort strength.
          </li>
        </ul>
      </div>

      {/* Detailed Results Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
        <div className="bg-gradient-to-r from-blue-600 to-cyan-600 p-6 text-center">
          <h3 className="text-xl font-bold text-white shadow-sm">📋 Detailed Student Results</h3>
        </div>
        
        <div className="overflow-x-auto max-h-[500px]">
          <table className="w-full text-left border-collapse">
            <thead className="sticky top-0 bg-slate-800 z-10 shadow-md">
              <tr>
                <th className="p-4 text-slate-300 font-semibold border-b border-slate-700">Reg No</th>
                <th className="p-4 text-slate-300 font-semibold border-b border-slate-700">Student Name</th>
                <th className="p-4 text-slate-300 font-semibold border-b border-slate-700">GPA / Marks</th>
                <th className="p-4 text-slate-300 font-semibold border-b border-slate-700">Status</th>
                <th className="p-4 text-slate-300 font-semibold border-b border-slate-700">Performance</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {studentList.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-slate-500 italic">
                    Waiting for scraper to finish processing students...
                  </td>
                </tr>
              ) : (
                studentList.map((student, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/50 transition-colors duration-200">
                    <td className="p-4 text-slate-300 font-mono text-sm">{student.register_number}</td>
                    <td className="p-4 text-slate-200 font-medium">{student.name || 'Unknown'}</td>
                    <td className="p-4 text-slate-300">{student.gpa || 'N/A'}</td>
                    <td className="p-4">
                      {student.status === 'Pass' ? (
                        <span className="text-green-400 font-bold">Passed</span>
                      ) : (
                        <span className="text-red-400 font-bold">Failed</span>
                      )}
                    </td>
                    <td className="p-4">
                      {student.gpa >= 9.0 ? (
                        <span className="bg-gradient-to-r from-yellow-400 to-orange-500 text-slate-900 text-xs font-bold px-3 py-1 rounded-full shadow-sm">🏆 Outstanding</span>
                      ) : student.gpa >= 8.0 ? (
                        <span className="bg-gradient-to-r from-emerald-400 to-teal-500 text-slate-900 text-xs font-bold px-3 py-1 rounded-full shadow-sm">⭐ Excellent</span>
                      ) : student.status === 'Pass' ? (
                        <span className="bg-slate-700 text-slate-300 text-xs font-bold px-3 py-1 rounded-full">👍 Good</span>
                      ) : (
                        <span className="bg-red-900/50 text-red-300 text-xs font-bold px-3 py-1 rounded-full border border-red-700/50">Needs Review</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}