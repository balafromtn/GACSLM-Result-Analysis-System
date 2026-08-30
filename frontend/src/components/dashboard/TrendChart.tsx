'use client';

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default function TrendChart({ subjects }: { subjects: any[] }) {
  if (!subjects || subjects.length === 0) return null;

  const data = {
    labels: subjects.map(s => s.code),
    datasets: [
      {
        label: 'Average Score',
        data: subjects.map(s => s.average),
        borderColor: 'rgba(99, 102, 241, 1)', // Indigo 500
        backgroundColor: 'rgba(99, 102, 241, 0.1)',
        borderWidth: 2,
        tension: 0.4,
        fill: true,
        pointBackgroundColor: 'rgba(99, 102, 241, 1)',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: 'rgba(99, 102, 241, 1)',
        pointRadius: 4,
        pointHoverRadius: 6,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          title: (items: any) => {
            if (!items.length) return '';
            const idx = items[0].dataIndex;
            return subjects[idx].name;
          },
          label: (item: any) => `Average: ${item.raw}%`
        }
      }
    },
    scales: {
      x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 10 } } },
      y: { 
        grid: { color: '#334155', borderDash: [4, 4] }, 
        ticks: { color: '#94a3b8' },
        min: 0,
        max: 100
      },
    },
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 h-72">
      <h3 className="text-sm font-semibold text-slate-300 mb-4">Subject Performance Trend</h3>
      <div className="h-52">
        <Line data={data} options={options} />
      </div>
    </div>
  );
}
