import React, { useEffect, useRef } from 'react';
// @ts-ignore
import { SmoothieChart, TimeSeries } from 'smoothie';

interface ICUStripCardProps {
  title: string;
  value: number;
  unit: string;
  color: 'green' | 'cyan' | 'white' | 'orange';
  series: any;
  minScale: number;
  maxScale: number;
}

export default function ICUStripCard({ title, value, unit, color, series, minScale, maxScale }: ICUStripCardProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  
  const colorMap: Record<string, { bg: string, text: string, chart: string }> = {
    green: { bg: 'bg-emerald-950/20', text: 'text-emerald-400', chart: '#10b981' },
    cyan: { bg: 'bg-cyan-950/20', text: 'text-cyan-400', chart: '#06b6d4' },
    white: { bg: 'bg-slate-800/30', text: 'text-slate-200', chart: '#f8fafc' },
    orange: { bg: 'bg-amber-950/20', text: 'text-amber-500', chart: '#f59e0b' },
  };

  const style = colorMap[color] || colorMap.white;

  useEffect(() => {
    if (canvasRef.current && series) {
      const chart = new SmoothieChart({
        millisPerPixel: 15,
        grid: { strokeStyle: 'transparent', fillStyle: 'transparent', borderVisible: false },
        labels: { disabled: true },
        minValue: minScale,
        maxValue: maxScale,
        responsive: true
      });
      
      chart.addTimeSeries(series, { 
        strokeStyle: style.chart, 
        lineWidth: 2.0 
      });
      
      chart.streamTo(canvasRef.current, 1000);
      
      return () => {
         chart.stop();
      };
    }
  }, [series, style.chart, minScale, maxScale]);

  return (
    <div 
      className="flex h-24 overflow-hidden clinical-panel group"
      role="region"
      aria-label={`${title} telemetry: ${value.toFixed(1)} ${unit}`}
    >
      {/* Waveform area (Left) */}
      <div className="flex-[2] relative bg-[#020617] rounded-l-xl" aria-hidden="true">
        <canvas ref={canvasRef} className="w-full h-full" style={{ display: 'block' }}></canvas>
        <div className={`absolute top-2 left-3 ${style.text} text-xs font-bold tracking-widest opacity-80`}>
          {title}
        </div>
      </div>
      
      {/* Numbers area (Right) */}
      <div className={`flex-1 flex flex-col justify-center items-end p-4 border-l border-slate-800/50 rounded-r-xl ${style.bg}`} aria-hidden="true">
        <div className={`text-4xl clinical-data-value ${style.text}`}>
          {value.toFixed(1)}
        </div>
        <div className={`text-xs font-bold uppercase mt-1 ${style.text} opacity-70 tracking-widest`}>
          {unit}
        </div>
      </div>
    </div>
  );
}
