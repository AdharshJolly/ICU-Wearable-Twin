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

  // High-frequency authentic waveform generation
  useEffect(() => {
    let lastTime = new Date().getTime();
    let phase = 0;
    
    const interval = setInterval(() => {
      const now = new Date().getTime();
      const dt = now - lastTime;
      lastTime = now;
      const m = metricsRef.current;
      
      const hr = m.hr || 75;
      const beatDuration = 60000 / hr;
      phase += dt / beatDuration;
      if (phase > 1) phase -= 1;

      // 1. ECG Waveform (Green, Top Track: 110 to 200)
      let ecg = 135; // Baseline
      if (phase > 0.1 && phase < 0.15) ecg += Math.sin((phase - 0.1) * 20 * Math.PI) * 12; // P wave
      else if (phase > 0.3 && phase < 0.32) ecg -= 20; // Q wave
      else if (phase >= 0.32 && phase < 0.35) ecg += 60; // R spike
      else if (phase >= 0.35 && phase < 0.38) ecg -= 25; // S wave
      else if (phase > 0.55 && phase < 0.7) ecg += Math.sin((phase - 0.55) * 6.66 * Math.PI) * 18; // T wave
      ecg += (Math.random() - 0.5) * 4; // Sensor noise

      // 2. SpO2 Plethysmograph (Cyan, Bottom Track: 10 to 90)
      let spo2P = (phase + 0.4) % 1.0; // Delayed from ECG
      let plethVal = Math.sin(spo2P * Math.PI);
      if (spo2P > 0.4 && spo2P < 0.6) {
         plethVal -= 0.15 * Math.sin((spo2P - 0.4) * 5 * Math.PI); // Dicrotic notch
      }
      if (plethVal < 0) plethVal = 0;
      let spo2Wave = 20 + (plethVal * 55) + (Math.random() - 0.5) * 2;

      hrSeries.current.append(now, ecg);
      spo2Series.current.append(now, spo2Wave);
    }, 30); // ~33 fps
    
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (canvasRef.current) {
      if (!chartRef.current) {
        chartRef.current = new SmoothieChart({
          millisPerPixel: 12, // Faster scrolling for ECG
          grid: {
            strokeStyle: '#1e293b',
            fillStyle: '#000000', 
            lineWidth: 1,
            millisPerLine: 1000,
            verticalSections: 8
          },
          labels: { disabled: true },
          minValue: 0,
          maxValue: 210,
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
    <div className="clinical-panel p-3 flex flex-col h-full w-full relative border-blue-500/20 shadow-[0_0_15px_rgba(59,130,246,0.05)]" aria-label="Main Central Monitor" role="region">
      <div className="flex justify-between items-center mb-2 px-2 absolute top-4 left-4 right-4 z-10 pointer-events-none">
        <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2 bg-black/50 p-2 rounded backdrop-blur-sm border border-slate-800">
          <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)] animate-pulse"></span>
          CENTRAL TELEMETRY (ECG II & PLETH)
        </h2>
      </div>
      <div className="flex-1 w-full relative rounded-lg overflow-hidden bg-black border border-slate-800/80 shadow-inner">
        <canvas ref={canvasRef} className="w-full h-full block"></canvas>
      </div>
    </div>
  );
}
