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

export default function GradeChart({ metrics }: { metrics: any }) {
  const data = {
    labels: ['Passed', 'Failed'],
    datasets: [
      {
        label: 'Number of Students',
        data: [metrics?.passed || 0, metrics?.failed || 0],
        backgroundColor: ['rgba(16, 185, 129, 0.6)', 'rgba(239, 68, 68, 0.6)'],
        borderColor: ['rgba(16, 185, 129, 1)', 'rgba(239, 68, 68, 1)'],
        borderWidth: 1,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: { color: '#cbd5e1' },
      },
      title: {
        display: true,
        text: 'Class Performance Overview',
        color: '#f8fafc',
      },
    },
    scales: {
      x: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } },
      y: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } },
    },
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
      <Bar data={data} options={options} />
    </div>
  );
}