import { useRef, useEffect } from 'react';
// @ts-ignore
import { SmoothieChart, TimeSeries } from 'smoothie';

export function ICUStripCard({ title, value, unit, color, series, minScale, maxScale }: { title: string, value: number, unit: string, color: string, series: any, minScale: number, maxScale: number }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  
  const colorMap: Record<string, { bg: string, text: string, chart: string }> = {
    green: { bg: 'bg-green-950/20', text: 'text-green-500', chart: '#22c55e' },
    cyan: { bg: 'bg-cyan-950/20', text: 'text-cyan-400', chart: '#22d3ee' },
    white: { bg: 'bg-slate-800/30', text: 'text-slate-200', chart: '#f1f5f9' },
    orange: { bg: 'bg-orange-950/20', text: 'text-orange-500', chart: '#f97316' },
  };

  const style = colorMap[color] || colorMap['white'];

  useEffect(() => {
    if (canvasRef.current && series) {
      const chart = new SmoothieChart({
        millisPerPixel: 15, // Fast scroll for ECG feel
        grid: { strokeStyle: 'transparent', fillStyle: 'transparent', borderVisible: false },
        labels: { disabled: true },
        minValue: minScale,
        maxValue: maxScale,
        responsive: true
      });
      
      chart.addTimeSeries(series, { 
        strokeStyle: style.chart, 
        lineWidth: 2.5 
      });
      
      chart.streamTo(canvasRef.current, 1000);
      
      return () => {
         chart.stop();
      };
    }
  }, [series, style.chart, minScale, maxScale]);

  return (
    <div className="flex h-24 overflow-hidden group">
      <div className="flex-[2] relative border border-slate-900 bg-black rounded-l-xl">
        <canvas ref={canvasRef} className="w-full h-full" style={{ display: 'block' }}></canvas>
        <div className={`absolute top-2 left-3 ${style.text} text-xs font-bold tracking-widest opacity-80`}>
          {title}
        </div>
      </div>
      
      <div className={`flex-1 flex flex-col justify-center items-end p-4 border-y border-r border-slate-900 rounded-r-xl ${style.bg}`}>
        <div className={`text-4xl font-black font-mono tracking-tighter ${style.text}`}>
          {value.toFixed(1)}
        </div>
        <div className={`text-[10px] font-bold uppercase mt-1 ${style.text} opacity-60 tracking-widest`}>
          {unit}
        </div>
      </div>
    </div>
  );
}
