"use client";

import { useEffect, useRef } from 'react';
import Chart from 'chart.js/auto';

export default function GenderPerformanceChart({ data }: { data: Record<string, any> }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<Chart | null>(null);

  useEffect(() => {
    if (!canvasRef.current) return;

    if (chartRef.current) {
      chartRef.current.destroy();
    }

    const ctx = canvasRef.current.getContext('2d');
    if (!ctx) return;

    const male = data['Male'] || { average: 0, pass_rate: 0 };
    const female = data['Female'] || { average: 0, pass_rate: 0 };

    chartRef.current = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['Male', 'Female'],
        datasets: [
          {
            label: 'Average Score (%)',
            data: [male.average, female.average],
            backgroundColor: 'rgba(99, 102, 241, 0.8)', // indigo-500
            borderRadius: 6,
          },
          {
            label: 'Pass Rate (%)',
            data: [male.pass_rate, female.pass_rate],
            backgroundColor: 'rgba(16, 185, 129, 0.8)', // emerald-500
            borderRadius: 6,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top',
            labels: {
              color: '#94a3b8',
              usePointStyle: true,
              font: {
                family: 'Inter, sans-serif'
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            grid: {
              color: 'rgba(148, 163, 184, 0.1)',
            },
            ticks: {
              color: '#94a3b8',
              font: {
                family: 'Inter, sans-serif'
              }
            }
          },
          x: {
            grid: {
              display: false
            },
            ticks: {
              color: '#94a3b8',
              font: {
                family: 'Inter, sans-serif',
                weight: 'bold'
              }
            }
          }
        }
      }
    });

    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
      }
    };
  }, [data]);

  return (
    <div className="w-full h-[250px]">
      <canvas ref={canvasRef}></canvas>
    </div>
  );
}
