import React from 'react';
import { Activity, AlertTriangle, ArrowDown, ArrowUp, HeartPulse, ShieldAlert, Thermometer, Wind } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';

interface DigitalTwinPanelProps {
  snapshot: any;
  trajectories: any;
}

export default function DigitalTwinPanel({ snapshot, trajectories }: DigitalTwinPanelProps) {
  if (!snapshot || !snapshot.baseline) return (
    <div className="bg-slate-900 p-6 rounded-2xl shadow-lg border border-slate-800 animate-pulse h-full">
      <div className="h-4 bg-slate-800 rounded w-1/3 mb-4"></div>
      <div className="h-8 bg-slate-800 rounded w-1/2 mb-6"></div>
      <div className="space-y-3">
        <div className="h-4 bg-slate-800 rounded"></div>
        <div className="h-4 bg-slate-800 rounded w-5/6"></div>
      </div>
    </div>
  );

  const { baseline, hr, rr, spo2, sbp, risk_state, risk_probability, confidence } = snapshot;

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

  // Convert trajectory payload into Recharts format
  let chartData = [];
  if (trajectories && trajectories.steps && trajectories.trajectories) {
    const steps = trajectories.steps;
    const trajKeys = Object.keys(trajectories.trajectories);
    
    chartData = steps.map((step: number, i: number) => {
      let dataPoint: any = { time: `+${step * 2}m` }; // Assuming ~2 min per step
      trajKeys.forEach(k => {
        dataPoint[k] = trajectories.trajectories[k].risk[i];
      });
      return dataPoint;
    });
  }

  const getStateColor = (state: string) => {
    switch (state) {
      case 'STABLE': return 'bg-emerald-900/30 text-emerald-400 border-emerald-500/50';
      case 'WATCH': return 'bg-blue-900/30 text-blue-400 border-blue-500/50';
      case 'ELEVATED': return 'bg-yellow-900/30 text-yellow-400 border-yellow-500/50';
      case 'HIGH_RISK': return 'bg-orange-900/30 text-orange-400 border-orange-500/50';
      case 'CRITICAL': return 'bg-red-900/30 text-red-400 border-red-500/50';
      default: return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  return (
    <div className="bg-slate-900 p-6 rounded-2xl shadow-lg border border-slate-800 h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-bold text-slate-100 flex items-center">
          <Activity className="w-5 h-5 mr-2 text-indigo-400" />
          DIGITAL TWIN
        </h2>
        <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getStateColor(risk_state)}`}>
          {risk_state}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Calibrated Risk</div>
          <div className="text-3xl font-black text-slate-100">{risk_probability.toFixed(1)}%</div>
        </div>
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Model Confidence</div>
          <div className="text-xl font-bold text-slate-200 mt-1">{confidence}</div>
        </div>
      </div>

      <div className="mb-6">
        <h3 className="text-sm font-bold text-slate-300 mb-3 uppercase tracking-wider border-b border-slate-800 pb-2">Baseline Deviation</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="flex items-center text-slate-400"><HeartPulse className="w-4 h-4 mr-2" /> HR</span>
            <span className={`font-mono font-medium ${devs.hr.dir === 'up' ? 'text-red-400' : 'text-slate-300'}`}>
              {devs.hr.sign}{devs.hr.val} bpm {devs.hr.dir === 'up' ? <ArrowUp className="w-3 h-3 inline" /> : <ArrowDown className="w-3 h-3 inline" />}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="flex items-center text-slate-400"><Wind className="w-4 h-4 mr-2" /> RR</span>
            <span className={`font-mono font-medium ${devs.rr.dir === 'up' ? 'text-red-400' : 'text-slate-300'}`}>
              {devs.rr.sign}{devs.rr.val} /min {devs.rr.dir === 'up' ? <ArrowUp className="w-3 h-3 inline" /> : <ArrowDown className="w-3 h-3 inline" />}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="flex items-center text-slate-400"><Activity className="w-4 h-4 mr-2" /> SpO2</span>
            <span className={`font-mono font-medium ${devs.spo2.dir === 'down' ? 'text-red-400' : 'text-slate-300'}`}>
              {devs.spo2.sign}{devs.spo2.val}% {devs.spo2.dir === 'up' ? <ArrowUp className="w-3 h-3 inline" /> : <ArrowDown className="w-3 h-3 inline" />}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="flex items-center text-slate-400"><ShieldAlert className="w-4 h-4 mr-2" /> SBP</span>
            <span className={`font-mono font-medium ${devs.sbp.dir === 'down' ? 'text-orange-400' : 'text-slate-300'}`}>
              {devs.sbp.sign}{devs.sbp.val} mmHg {devs.sbp.dir === 'up' ? <ArrowUp className="w-3 h-3 inline" /> : <ArrowDown className="w-3 h-3 inline" />}
            </span>
          </div>
        </div>
      </div>

      <div className="flex-1 flex flex-col">
        <h3 className="text-sm font-bold text-slate-300 mb-3 uppercase tracking-wider border-b border-slate-800 pb-2">Learned Trajectory Forecast</h3>
        {chartData.length > 0 ? (
          <div className="flex-1 min-h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" />
                <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#94a3b8' }} tickMargin={10} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <Tooltip 
                  contentStyle={{ borderRadius: '8px', backgroundColor: '#0f172a', border: '1px solid #334155', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.3)' }}
                  labelStyle={{ fontWeight: 'bold', color: '#f8fafc' }}
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
                  />
                ))}
                <Legend iconType="circle" wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center bg-slate-950 rounded-xl border border-slate-800 text-sm text-slate-500">
            Awaiting Counterfactual Simulation...
          </div>
        )}
      </div>
    </div>
  );
}
