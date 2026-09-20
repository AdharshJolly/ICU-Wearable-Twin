import React, { useEffect, useRef } from 'react';
import { HeartPulse } from 'lucide-react';
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

      // 1. ECG Waveform (Green) - Centered directly on the actual HR value
      let ecg = m.hr; 
      if (phase > 0.1 && phase < 0.15) ecg += Math.sin((phase - 0.1) * 20 * Math.PI) * 12; // P wave
      else if (phase > 0.3 && phase < 0.32) ecg -= 20; // Q wave
      else if (phase >= 0.32 && phase < 0.35) ecg += 50; // R spike
      else if (phase >= 0.35 && phase < 0.38) ecg -= 25; // S wave
      else if (phase > 0.55 && phase < 0.7) ecg += Math.sin((phase - 0.55) * 6.66 * Math.PI) * 15; // T wave

      // 2. SpO2 Plethysmograph (Cyan) - Centered directly on actual SpO2 value
      let spo2P = (phase + 0.4) % 1.0; 
      let plethVal = Math.sin(spo2P * Math.PI);
      if (spo2P > 0.4 && spo2P < 0.6) {
         plethVal -= 0.15 * Math.sin((spo2P - 0.4) * 5 * Math.PI); // Dicrotic notch
      }
      if (plethVal < 0) plethVal = 0;
      let spo2Wave = (m.spo2 - 5) + (plethVal * 15);

      hrSeries.current.append(now, ecg);
      spo2Series.current.append(now, spo2Wave);
    }, 30); // ~33 fps
    
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (canvasRef.current) {
      if (!chartRef.current) {
        chartRef.current = new SmoothieChart({
          millisPerPixel: 15, 
          grid: {
            strokeStyle: 'rgba(16, 185, 129, 0.1)', // Subtle medical green grid
            fillStyle: '#000000', 
            lineWidth: 1,
            millisPerLine: 1000,
            verticalSections: 12,
            borderVisible: false
          },
          labels: { disabled: true },
          minValue: 20, // Expanded scale to handle overlaps better
          maxValue: 180,
          responsive: true,
        });
  
        chartRef.current.addTimeSeries(hrSeries.current, { 
          strokeStyle: '#10b981', // emerald-500
          lineWidth: 2.5 
        });
        
        chartRef.current.addTimeSeries(spo2Series.current, { 
          strokeStyle: '#06b6d4', // cyan-500
          lineWidth: 2.5 
        });
      }
      
      if (isRunning) {
        chartRef.current.streamTo(canvasRef.current, 1000);
      } else {
        chartRef.current.stop();
      }
    }
  }, [isRunning]);

  const map = Math.round(metrics.dbp + (metrics.sbp - metrics.dbp) / 3);

  return (
    <div className="clinical-panel flex flex-row h-full w-full relative overflow-hidden bg-black border-slate-700/50 shadow-[0_0_30px_rgba(0,0,0,0.8)] rounded-xl" aria-label="Main Central Monitor" role="region">
      
      {/* Canvas Area (Waveforms) */}
      <div className="flex-1 relative border-r border-slate-800/80 bg-black">
        {/* Trace Labels overlay */}
        <div className="absolute top-2 left-2 z-10 flex flex-col gap-1">
          <span className="text-emerald-500 font-bold text-[10px] uppercase bg-black/60 px-1 rounded">ECG II (1.0 mV)</span>
          <span className="text-cyan-500 font-bold text-[10px] uppercase bg-black/60 px-1 rounded">PLETH (SpO2)</span>
        </div>
        <canvas ref={canvasRef} className="w-full h-full block"></canvas>
      </div>
      
      {/* Parameters Sidebar (Glowing Digits) */}
      <div className="w-48 lg:w-64 flex flex-col divide-y divide-slate-800/80 bg-[#040814] shadow-[-10px_0_20px_rgba(0,0,0,0.5)] z-20">
        
        {/* ECG Parameter */}
        <div className="flex-1 flex flex-col justify-center p-3 relative group">
           <div className="absolute top-2 left-3 text-emerald-500 font-bold text-xs uppercase tracking-widest flex items-center gap-2">
             HR <HeartPulse size={12} className={isRunning ? "animate-pulse" : ""} />
           </div>
           <div className="absolute top-2 right-3 text-emerald-500/40 text-[10px] text-right leading-tight">120<br/>50</div>
           <div className="flex items-baseline justify-end w-full pr-6 lg:pr-8 mt-4">
              <span className="text-emerald-400 font-mono text-6xl lg:text-7xl tracking-tighter" style={{ textShadow: '0 0 20px rgba(16,185,129,0.4)' }}>
                {metrics.hr.toFixed(0)}
              </span>
           </div>
        </div>

        {/* SpO2 Parameter */}
        <div className="flex-1 flex flex-col justify-center p-3 relative group">
           <div className="absolute top-2 left-3 text-cyan-500 font-bold text-xs uppercase tracking-widest">SpO2 %</div>
           <div className="absolute top-2 right-3 text-cyan-500/40 text-[10px] text-right leading-tight">100<br/>90</div>
           <div className="flex items-baseline justify-end w-full pr-6 lg:pr-8 mt-4">
              <span className="text-cyan-400 font-mono text-6xl lg:text-7xl tracking-tighter" style={{ textShadow: '0 0 20px rgba(6,182,212,0.4)' }}>
                {metrics.spo2.toFixed(0)}
              </span>
           </div>
        </div>
        
        {/* NIBP Parameter */}
        <div className="flex-1 flex flex-col justify-center p-3 relative group">
           <div className="absolute top-2 left-3 text-slate-300 font-bold text-xs uppercase tracking-widest">NIBP mmHg</div>
           <div className="absolute top-2 right-3 text-slate-500/60 text-[10px] text-right leading-tight">160<br/>90</div>
           <div className="flex flex-col items-end justify-center w-full pr-4 lg:pr-6 mt-4">
              <div className="flex items-baseline gap-1" style={{ textShadow: '0 0 15px rgba(226,232,240,0.2)' }}>
                <span className="text-slate-200 font-mono text-4xl lg:text-5xl tracking-tighter">{metrics.sbp.toFixed(0)}</span>
                <span className="text-slate-500 text-2xl">/</span>
                <span className="text-slate-200 font-mono text-3xl lg:text-4xl tracking-tighter">{metrics.dbp.toFixed(0)}</span>
              </div>
              <div className="text-slate-400 text-xs font-mono font-bold mt-1">
                MAP ({map})
              </div>
           </div>
        </div>

      </div>
    </div>
  );
}


