"use client";

import { useState, useEffect } from 'react';
import { Activity, Thermometer, Wind, HeartPulse, Play, Square, User, AlertTriangle, Clock, Zap } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';

export default function Dashboard() {
  const [isRunning, setIsRunning] = useState(false);
  const [riskState, setRiskState] = useState('STABLE');
  const [chartData, setChartData] = useState<any[]>([]);

  // Mock patient data
  const patientData = {
    id: "P001",
    age: 63,
    gender: "Male",
    physician: "Dr. Sarah Chen"
  };

  const [metrics, setMetrics] = useState({
    hr: { value: 75, status: 'stable', trend: [70, 72, 75, 74, 75] },
    rr: { value: 16, status: 'stable', trend: [15, 16, 16, 15, 16] },
    temp: { value: 36.8, status: 'stable', trend: [36.7, 36.8, 36.8, 36.8, 36.8] },
    spo2: { value: 98, status: 'stable', trend: [99, 98, 98, 98, 98] }
  });

  // Mocking the simulation loop
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isRunning) {
      interval = setInterval(() => {
        const time = new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit' });
        
        const newHr = 70 + Math.random() * 10;
        const newRr = 15 + Math.random() * 4;
        const newTemp = 36.5 + Math.random() * 1;
        const newSpo2 = 95 + Math.random() * 5;

        setChartData(prev => {
          const newData = [...prev, { time, hr: newHr, spo2: newSpo2 }];
          if (newData.length > 20) return newData.slice(newData.length - 20);
          return newData;
        });

        setMetrics(prev => ({
          hr: { ...prev.hr, value: newHr, trend: [...prev.hr.trend.slice(-4), newHr] },
          rr: { ...prev.rr, value: newRr, trend: [...prev.rr.trend.slice(-4), newRr] },
          temp: { ...prev.temp, value: newTemp, trend: [...prev.temp.trend.slice(-4), newTemp] },
          spo2: { ...prev.spo2, value: newSpo2, trend: [...prev.spo2.trend.slice(-4), newSpo2] }
        }));
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isRunning]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans p-4">
      {/* Top Navbar / Demographics */}
      <header className="flex justify-between items-center mb-6 bg-slate-900 p-4 rounded-2xl border border-slate-800 shadow-lg">
        <div className="flex items-center space-x-4">
          <div className="bg-blue-600/20 p-2 rounded-lg border border-blue-500/30">
            <Activity className="text-blue-400" size={28} />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-100 tracking-wide">ICU DIGITAL TWIN</h1>
            <p className="text-xs text-slate-400">BED 04 • WARD A</p>
          </div>
        </div>

        <div className="flex items-center space-x-8">
          <div className="flex flex-col">
            <span className="text-xs text-slate-500 uppercase font-semibold">Patient ID</span>
            <span className="font-mono text-slate-200">{patientData.id}</span>
          </div>
          <div className="flex flex-col">
            <span className="text-xs text-slate-500 uppercase font-semibold">Demographics</span>
            <span className="text-slate-200">{patientData.age}yo {patientData.gender}</span>
          </div>
          <div className="flex flex-col">
            <span className="text-xs text-slate-500 uppercase font-semibold">Physician</span>
            <span className="text-slate-200">{patientData.physician}</span>
          </div>
          
          <div className="flex space-x-3 ml-4">
            <button 
              onClick={() => setIsRunning(!isRunning)}
              className={`flex items-center px-6 py-2 rounded-lg font-medium transition-all ${
                isRunning 
                  ? 'bg-red-500/10 text-red-400 border border-red-500/30 hover:bg-red-500/20' 
                  : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/20'
              }`}
            >
              {isRunning ? <><Square size={16} className="mr-2" /> STOP SIM</> : <><Play size={16} className="mr-2" /> START SIM</>}
            </button>
          </div>
        </div>
      </header>

      {/* Bento Box Grid */}
      <div className="grid grid-cols-12 gap-4 h-[calc(100vh-120px)]">
        
        {/* Left Column: Vitals (3 cols) */}
        <div className="col-span-3 flex flex-col gap-4">
          <VitalCard title="HEART RATE" value={metrics.hr.value} unit="BPM" color="red" icon={<HeartPulse size={20} />} trendData={metrics.hr.trend} range="60-100" />
          <VitalCard title="SpO2" value={metrics.spo2.value} unit="%" color="emerald" icon={<Activity size={20} />} trendData={metrics.spo2.trend} range="95-100" />
          <VitalCard title="RESP RATE" value={metrics.rr.value} unit="RPM" color="blue" icon={<Wind size={20} />} trendData={metrics.rr.trend} range="12-20" />
          <VitalCard title="TEMP" value={metrics.temp.value} unit="°C" color="orange" icon={<Thermometer size={20} />} trendData={metrics.temp.trend} range="36.5-37.5" />
        </div>

        {/* Center Column: Main Trajectory (6 cols) */}
        <div className="col-span-6 flex flex-col gap-4">
          
          {/* Risk Banner */}
          <div className={`p-6 rounded-2xl border flex items-center justify-between transition-colors duration-500 ${
            riskState === 'STABLE' 
              ? 'bg-emerald-950/30 border-emerald-900/50 text-emerald-400' 
              : 'bg-red-950/30 border-red-900/50 text-red-400 shadow-[0_0_30px_rgba(220,38,38,0.15)]'
          }`}>
            <div>
              <p className="text-xs uppercase tracking-wider font-bold opacity-80 mb-1">Current State</p>
              <h2 className="text-3xl font-black tracking-tight">{riskState}</h2>
            </div>
            {riskState === 'CRITICAL' && <AlertTriangle size={40} className="animate-pulse" />}
            {riskState === 'STABLE' && <Activity size={40} className="opacity-50" />}
          </div>

          {/* Main Chart */}
          <div className="flex-1 bg-slate-900 rounded-2xl border border-slate-800 p-6 flex flex-col relative overflow-hidden">
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center">
              <Zap size={16} className="mr-2 text-yellow-500" /> Real-Time Trajectory
            </h3>
            
            <div className="flex-1 min-h-0 w-full relative">
              {chartData.length === 0 && !isRunning && (
                <div className="absolute inset-0 flex items-center justify-center text-slate-600 font-medium z-10">
                  Click START SIM to begin streaming data...
                </div>
              )}
              
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorHr" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis dataKey="time" stroke="#475569" tick={{fill: '#64748b', fontSize: 11}} tickMargin={10} minTickGap={30} />
                  <YAxis yAxisId="left" stroke="#475569" tick={{fill: '#64748b', fontSize: 11}} domain={['auto', 'auto']} />
                  <YAxis yAxisId="right" orientation="right" stroke="#475569" tick={{fill: '#64748b', fontSize: 11}} domain={[85, 100]} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px', color: '#f8fafc' }}
                    itemStyle={{ color: '#e2e8f0' }}
                  />
                  <Area yAxisId="left" type="monotone" dataKey="hr" stroke="#ef4444" fillOpacity={1} fill="url(#colorHr)" strokeWidth={2} isAnimationActive={false} />
                  <Line yAxisId="right" type="monotone" dataKey="spo2" stroke="#10b981" strokeWidth={2} dot={false} isAnimationActive={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Right Column: Explainability & Logs (3 cols) */}
        <div className="col-span-3 flex flex-col gap-4">
          
          {/* AI Explainability */}
          <div className="bg-slate-900 rounded-2xl border border-slate-800 p-5 flex-1 flex flex-col">
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">Isolation Forest SHAP</h3>
            <div className="flex-1 flex items-center justify-center border-2 border-dashed border-slate-800 rounded-xl bg-slate-900/50">
              <div className="text-center p-4 text-slate-500 text-sm">
                <Activity className="mx-auto mb-2 opacity-50" size={24} />
                Awaiting connection to API for SHAP explanations...
              </div>
            </div>
          </div>

          {/* Clinical Log */}
          <div className="bg-slate-900 rounded-2xl border border-slate-800 p-5 flex-[1.2] flex flex-col">
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center">
              <Clock size={16} className="mr-2" /> Audit Trail
            </h3>
            
            <div className="flex-1 overflow-y-auto pr-2 space-y-4">
              {/* Fake logs for design testing */}
              <LogItem time="10:42:05" type="info" message="Simulation started. Patient baseline loaded." />
              <LogItem time="10:45:12" type="warning" message="Heart Rate elevated > 90 BPM for 3 mins." />
              <LogItem time="10:48:30" type="critical" message="SpO2 dropped to 89%. Rule Engine triggered." />
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}

function VitalCard({ title, value, unit, color, icon, trendData, range }: { title: string, value: number, unit: string, color: string, icon: React.ReactNode, trendData: number[], range: string }) {
  const colorMap: Record<string, { bg: string, text: string, border: string, chart: string }> = {
    red: { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/20', chart: '#ef4444' },
    emerald: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20', chart: '#10b981' },
    blue: { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/20', chart: '#3b82f6' },
    orange: { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/20', chart: '#f97316' },
  };

  const style = colorMap[color];
  const chartData = trendData.map((val, i) => ({ i, val }));

  return (
    <div className={`bg-slate-900 rounded-2xl border border-slate-800 p-5 flex flex-col justify-between flex-1 relative overflow-hidden group hover:border-slate-700 transition-colors`}>
      <div className="flex justify-between items-start mb-2 z-10">
        <h3 className="text-slate-400 text-xs font-bold tracking-wider uppercase">{title}</h3>
        <div className={`p-1.5 rounded-lg ${style.bg} ${style.text}`}>
          {icon}
        </div>
      </div>
      
      <div className="flex items-baseline space-x-1 z-10">
        <span className={`text-4xl font-black font-mono tracking-tighter text-slate-100`}>
          {value.toFixed(1)}
        </span>
        <span className="text-slate-500 text-sm font-medium">{unit}</span>
      </div>
      
      <div className="mt-2 text-[10px] text-slate-500 font-mono tracking-wider z-10">
        NORMAL RANGE: {range}
      </div>

      {/* Mini Sparkline Background */}
      <div className="absolute bottom-0 right-0 left-0 h-16 opacity-30 group-hover:opacity-60 transition-opacity">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <Line type="monotone" dataKey="val" stroke={style.chart} strokeWidth={2} dot={false} isAnimationActive={false} />
            <YAxis domain={['auto', 'auto']} hide />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function LogItem({ time, type, message }: { time: string, type: 'info' | 'warning' | 'critical', message: string }) {
  const typeStyles = {
    info: 'border-blue-500/30 text-slate-300',
    warning: 'border-yellow-500/50 text-yellow-200/90',
    critical: 'border-red-500/50 text-red-300 bg-red-950/20'
  };

  const dotStyles = {
    info: 'bg-blue-400',
    warning: 'bg-yellow-400',
    critical: 'bg-red-400 animate-pulse'
  };

  return (
    <div className={`p-3 rounded-lg border-l-2 text-sm ${typeStyles[type]} pl-3 relative`}>
      <div className={`absolute -left-[5px] top-4 w-2 h-2 rounded-full ${dotStyles[type]}`}></div>
      <div className="text-xs font-mono text-slate-500 mb-1">{time}</div>
      <p className="leading-snug">{message}</p>
    </div>
  );
}
