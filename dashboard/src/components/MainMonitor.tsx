import React, { useEffect, useRef } from 'react';
// @ts-ignore
import { SmoothieChart, TimeSeries } from 'smoothie';

interface MainMonitorProps {
  metrics: { hr: number; spo2: number; rr: number; temp: number; sbp: number; dbp: number };
  isRunning: boolean;
}

export default function MainMonitor({ metrics, isRunning }: MainMonitorProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const chartRef = useRef<SmoothieChart | null>(null);
  const hrSeries = useRef<TimeSeries>(new TimeSeries());
  const spo2Series = useRef<TimeSeries>(new TimeSeries());
  const metricsRef = useRef(metrics);

  useEffect(() => {
    metricsRef.current = metrics;
  }, [metrics]);

  // High-frequency append
  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date().getTime();
      const m = metricsRef.current;
      hrSeries.current.append(now, m.hr);
      spo2Series.current.append(now, m.spo2);
    }, 250);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (canvasRef.current) {
      if (!chartRef.current) {
        chartRef.current = new SmoothieChart({
          millisPerPixel: 20, 
          grid: {
            strokeStyle: '#1e293b',
            fillStyle: '#000000', 
            lineWidth: 1,
            millisPerLine: 2000,
            verticalSections: 6
          },
          labels: { fillStyle: '#64748b', fontSize: 12, precision: 0 },
          timestampFormatter: SmoothieChart.timeFormatter,
          minValue: 30,
          maxValue: 170,
          responsive: true,
        });
  
        chartRef.current.addTimeSeries(hrSeries.current, { 
          strokeStyle: '#10b981', // emerald-500
          lineWidth: 2 
        });
        
        chartRef.current.addTimeSeries(spo2Series.current, { 
          strokeStyle: '#06b6d4', // cyan-500
          lineWidth: 2 
        });
      }
      
      if (isRunning) {
        chartRef.current.streamTo(canvasRef.current, 1000);
      } else {
        chartRef.current.stop();
      }
    }
  }, [isRunning]);

  return (
    <div className="clinical-panel p-4 flex flex-col mb-4 h-64 relative border-blue-500/20 shadow-[0_0_15px_rgba(59,130,246,0.05)]" aria-label="Main Central Monitor" role="region">
      <div className="flex justify-between items-center mb-2 px-2 absolute top-4 left-4 right-4 z-10 pointer-events-none">
        <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2 bg-black/50 p-2 rounded backdrop-blur-sm border border-slate-800">
          <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)] animate-pulse"></span>
          CENTRAL TELEMETRY (HR & SpO2)
        </h2>
      </div>
      <div className="flex-1 w-full relative rounded-lg overflow-hidden bg-black border border-slate-800/80">
        <canvas ref={canvasRef} className="w-full h-full block"></canvas>
      </div>
    </div>
  );
}
