"use client";

import { useEffect, useRef } from 'react';
import Chart from 'chart.js/auto';

export default function CommunityChart({ data }: { data: Record<string, any> }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chartRef = useRef<Chart | null>(null);

  useEffect(() => {
    if (!canvasRef.current || !data || Object.keys(data).length === 0) return;

    if (chartRef.current) {
      chartRef.current.destroy();
    }

    const ctx = canvasRef.current.getContext('2d');
    if (!ctx) return;

    const labels = Object.keys(data);
    const passRates = labels.map(label => data[label].pass_rate);
    const averages = labels.map(label => data[label].average);

    chartRef.current = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Average Score (%)',
            data: averages,
            backgroundColor: 'rgba(99, 102, 241, 0.8)', // indigo-500
            borderRadius: 6,
          },
          {
            label: 'Pass Rate (%)',
            data: passRates,
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
