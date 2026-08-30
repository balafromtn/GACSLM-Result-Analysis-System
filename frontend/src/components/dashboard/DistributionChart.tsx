'use client';

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

export default function DistributionChart({ distribution }: { distribution: any }) {
  if (!distribution) return null;

  const data = {
    labels: ['90-100', '80-89', '70-79', '60-69', '50-59', '<50'],
    datasets: [
      {
        label: 'Students',
        data: [
          distribution['90-100'] || 0,
          distribution['80-89'] || 0,
          distribution['70-79'] || 0,
          distribution['60-69'] || 0,
          distribution['50-59'] || 0,
          distribution['<50'] || 0,
        ],
        backgroundColor: [
          'rgba(52, 211, 153, 0.8)', // Emerald
          'rgba(96, 165, 250, 0.8)', // Blue
          'rgba(129, 140, 248, 0.8)', // Indigo
          'rgba(192, 132, 252, 0.8)', // Purple
          'rgba(251, 191, 36, 0.8)', // Amber
          'rgba(248, 113, 113, 0.8)', // Red
        ],
        borderRadius: 4,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      title: { display: false },
    },
    scales: {
      x: { grid: { display: false }, ticks: { color: '#94a3b8' } },
      y: { grid: { color: '#334155', borderDash: [4, 4] }, ticks: { color: '#94a3b8', stepSize: 2 } },
    },
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 h-72">
      <h3 className="text-sm font-semibold text-slate-300 mb-4">Performance Distribution</h3>
      <div className="h-52">
        <Bar data={data} options={options} />
      </div>
    </div>
  );
}
