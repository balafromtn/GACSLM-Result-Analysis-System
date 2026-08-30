"use client";

import { useEffect, useRef } from 'react';
import Chart from 'chart.js/auto';

export default function PassFailPieChart({ passed, failed }: { passed: number, failed: number }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<Chart | null>(null);

  useEffect(() => {
    if (!canvasRef.current) return;

    if (chartRef.current) {
      chartRef.current.destroy();
    }

    const ctx = canvasRef.current.getContext('2d');
    if (!ctx) return;

    chartRef.current = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Passed', 'Failed'],
        datasets: [{
          data: [passed, failed],
          backgroundColor: [
            'rgba(16, 185, 129, 0.8)', // emerald-500
            'rgba(239, 68, 68, 0.8)',  // red-500
          ],
          borderColor: [
            'rgba(16, 185, 129, 1)',
            'rgba(239, 68, 68, 1)',
          ],
          borderWidth: 2,
          hoverOffset: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              color: '#94a3b8',
              usePointStyle: true,
              padding: 20,
              font: {
                family: 'Inter, sans-serif'
              }
            }
          }
        },
        cutout: '70%'
      }
    });

    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
      }
    };
  }, [passed, failed]);

  return (
    <div className="w-full h-[250px] relative flex items-center justify-center">
      <canvas ref={canvasRef}></canvas>
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        <span className="text-3xl font-bold text-slate-900 dark:text-white">
          {passed + failed > 0 ? Math.round((passed / (passed + failed)) * 100) : 0}%
        </span>
        <span className="text-xs text-slate-500 font-medium">Pass Rate</span>
      </div>
    </div>
  );
}
