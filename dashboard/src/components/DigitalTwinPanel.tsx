import React from 'react';
import { Activity, ArrowDown, ArrowUp, HeartPulse, ShieldAlert, Wind } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';

interface DigitalTwinPanelProps {
  snapshot: any;
  trajectories: any;
}

export default function DigitalTwinPanel({ snapshot, trajectories }: DigitalTwinPanelProps) {
  if (!snapshot || !snapshot.baseline) return (
    <div 
      className="clinical-panel p-6 animate-pulse h-full flex flex-col justify-between"
      aria-busy="true"
      aria-label="Loading digital twin state"
    >
      <div className="h-6 bg-slate-800/50 rounded w-1/3 mb-4"></div>
      <div className="h-12 bg-slate-800/50 rounded w-1/2 mb-6"></div>
      <div className="space-y-4">
        <div className="h-4 bg-slate-800/50 rounded w-full"></div>
        <div className="h-4 bg-slate-800/50 rounded w-5/6"></div>
        <div className="h-4 bg-slate-800/50 rounded w-4/6"></div>
      </div>
    </div>
  );

  const { baseline, hr, rr, spo2, sbp, risk_probability, confidence } = snapshot;

  const getDeviation = (current: number, base: number) => {
    const diff = current - base;
    return {
      val: Math.abs(diff).toFixed(1),
      sign: diff > 0 ? '+' : diff < 0 ? '-' : '',
      dir: diff > 0 ? 'up' : diff < 0 ? 'down' : 'flat'
    };
  };

  const devs = {
    hr: getDeviation(hr, baseline.hr),
    rr: getDeviation(rr, baseline.rr),
    spo2: getDeviation(spo2, baseline.spo2),
    sbp: getDeviation(sbp, baseline.sbp)
  };

  let chartData: any[] = [];
  if (trajectories && trajectories.steps && trajectories.trajectories) {
    const steps = trajectories.steps;
    const trajKeys = Object.keys(trajectories.trajectories);
    chartData = steps.map((step: number, i: number) => {
      let dataPoint: any = { time: `+${step * 2}m` };
      trajKeys.forEach(k => { dataPoint[k] = trajectories.trajectories[k].risk[i]; });
      return dataPoint;
    });
  }

  return (
    <div className="clinical-panel p-6 h-full flex flex-col" aria-label="Digital Twin Overview" role="region">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
          <Activity className="w-5 h-5 text-purple-400" aria-hidden="true" />
          Digital Twin State
        </h2>
        <div className="text-xs font-semibold text-slate-500 uppercase tracking-widest">
          Active
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-[#020617]/50 p-4 rounded-xl border border-slate-800/60">
          <div className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Calibrated Risk</div>
          <div className="text-3xl clinical-data-value text-slate-50">{risk_probability.toFixed(1)}<span className="text-lg text-slate-500 ml-1">%</span></div>
        </div>
        <div className="bg-[#020617]/50 p-4 rounded-xl border border-slate-800/60">
          <div className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Model Confidence</div>
          <div className="text-xl font-bold text-slate-200 mt-1">{confidence}</div>
        </div>
      </div>

      <div className="mb-6">
        <h3 className="text-xs font-bold text-slate-500 mb-3 uppercase tracking-widest border-b border-slate-800/60 pb-2">Physiological Deviation</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="flex items-center text-slate-400 font-medium"><HeartPulse className="w-4 h-4 mr-2" aria-hidden="true" /> Heart Rate</span>
            <span className={`clinical-data-value ${devs.hr.dir === 'up' ? 'text-red-400' : 'text-slate-300'}`}>
              {devs.hr.sign}{devs.hr.val} <span className="text-xs opacity-50">bpm</span>
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="flex items-center text-slate-400 font-medium"><Wind className="w-4 h-4 mr-2" aria-hidden="true" /> Respiratory</span>
            <span className={`clinical-data-value ${devs.rr.dir === 'up' ? 'text-amber-400' : 'text-slate-300'}`}>
              {devs.rr.sign}{devs.rr.val} <span className="text-xs opacity-50">/min</span>
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="flex items-center text-slate-400 font-medium"><Activity className="w-4 h-4 mr-2" aria-hidden="true" /> SpO₂</span>
            <span className={`clinical-data-value ${devs.spo2.dir === 'down' ? 'text-red-400' : 'text-slate-300'}`}>
              {devs.spo2.sign}{devs.spo2.val} <span className="text-xs opacity-50">%</span>
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="flex items-center text-slate-400 font-medium"><ShieldAlert className="w-4 h-4 mr-2" aria-hidden="true" /> Systolic BP</span>
            <span className={`clinical-data-value ${devs.sbp.dir === 'down' ? 'text-amber-400' : 'text-slate-300'}`}>
              {devs.sbp.sign}{devs.sbp.val} <span className="text-xs opacity-50">mmHg</span>
            </span>
          </div>
        </div>
      </div>

      <div className="flex-1 flex flex-col">
        <h3 className="text-xs font-bold text-slate-500 mb-3 uppercase tracking-widest border-b border-slate-800/60 pb-2">Counterfactual Trajectory</h3>
        {chartData.length > 0 ? (
          <div className="flex-1 min-h-[200px]" role="img" aria-label="Line chart showing projected risk across different interventions">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e293b" />
                <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#64748b' }} tickMargin={10} axisLine={{ stroke: '#334155' }} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#64748b' }} axisLine={{ stroke: '#334155' }} tickLine={false} />
                <Tooltip 
                  contentStyle={{ borderRadius: '12px', backgroundColor: '#0f172a', border: '1px solid #334155', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.5)' }}
                  labelStyle={{ fontWeight: 'bold', color: '#f8fafc', marginBottom: '4px' }}
                  itemStyle={{ fontSize: '12px', fontWeight: 600 }}
                />
                {Object.keys(trajectories.trajectories).map((k) => (
                  <Line 
                    key={k}
                    type="monotone" 
                    dataKey={k} 
                    name={trajectories.trajectories[k].label}
                    stroke={trajectories.trajectories[k].color} 
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4, strokeWidth: 0 }}
                  />
                ))}
                <Legend iconType="circle" wrapperStyle={{ fontSize: '11px', paddingTop: '10px', color: '#94a3b8' }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center bg-[#020617]/50 rounded-xl border border-slate-800/60 text-xs font-medium text-slate-500">
            Awaiting Counterfactual Simulation...
          </div>
        )}
      </div>
    </div>
  );
}
