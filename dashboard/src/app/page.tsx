"use client";

import { useEffect, useState } from 'react';
import { Activity, Users, AlertCircle, Signal, CheckCircle2, ChevronRight, Filter } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function WardView() {
  const router = useRouter();
  const [patients, setPatients] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    fetch(`${apiUrl}/api/patients`)
      .then(res => res.json())
      .then(data => {
        setPatients(data.patients || []);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching patients", err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="min-h-screen p-4 md:p-6 lg:p-8 xl:p-10 max-w-7xl mx-auto">
      {/* Top Bar Header */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-slate-50 tracking-tight flex items-center gap-3">
            ICU Central Monitoring
          </h1>
          <p className="text-sm text-slate-400 mt-1 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)] animate-pulse" aria-hidden="true"></span>
            Live Telemetry &bull; Ward A &bull; {patients.length} Beds Occupied
          </p>
        </div>
        
        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="flex items-center justify-center gap-2 bg-slate-900/60 border border-slate-800/60 px-4 py-2 rounded-lg text-sm text-slate-300 flex-1 md:flex-none">
            <Signal className="w-4 h-4 text-emerald-400" aria-hidden="true" />
            <span>Sensors Online</span>
          </div>
          <button aria-label="Filter patients" className="flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 border border-slate-700/60 px-4 py-2 rounded-lg text-sm text-slate-200 transition-colors flex-1 md:flex-none">
            <Filter className="w-4 h-4" aria-hidden="true" />
            Filter
          </button>
        </div>
      </header>

      {/* Main Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 mb-8">
        <div className="clinical-panel p-4 md:p-5 flex flex-col justify-between">
          <div className="text-slate-400 text-xs uppercase tracking-widest font-semibold mb-2">Total Patients</div>
          <div className="text-2xl md:text-3xl font-light text-slate-50">{patients.length}</div>
        </div>
        <div className="clinical-panel p-4 md:p-5 flex flex-col justify-between border-emerald-500/20 bg-emerald-950/10">
          <div className="text-emerald-400/80 text-xs uppercase tracking-widest font-semibold mb-2">Stable</div>
          <div className="text-2xl md:text-3xl font-light text-emerald-400">{patients.length}</div>
        </div>
        <div className="clinical-panel p-4 md:p-5 flex flex-col justify-between border-amber-500/20 bg-amber-950/10">
          <div className="text-amber-400/80 text-xs uppercase tracking-widest font-semibold mb-2">Elevated Risk</div>
          <div className="text-2xl md:text-3xl font-light text-amber-400">0</div>
        </div>
        <div className="clinical-panel p-4 md:p-5 flex flex-col justify-between border-red-500/20 bg-red-950/10">
          <div className="text-red-400/80 text-xs uppercase tracking-widest font-semibold mb-2">Critical</div>
          <div className="text-2xl md:text-3xl font-light text-red-400">0</div>
        </div>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center h-64 text-slate-500 clinical-panel" aria-busy="true" aria-live="polite">
          <Activity className="animate-spin mb-4 text-blue-500" size={32} aria-hidden="true" />
          <p className="text-sm font-medium tracking-wide">INITIALIZING WARD DATA...</p>
        </div>
      ) : patients.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-slate-500 clinical-panel">
          <Users className="mb-4 text-slate-600 opacity-50" size={48} aria-hidden="true" />
          <h2 className="text-lg font-bold text-slate-300 mb-2">No Active Patients</h2>
          <p className="text-sm text-slate-500">The ward roster is currently empty.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
          {patients.map((p, index) => {
            const bedNum = String(index + 1).padStart(2, '0');
            const pId = p.Patient_ID || `P${String(index+1).padStart(3, '0')}`;
            
            return (
              <div 
                key={pId} 
                onClick={() => router.push(`/patient/${p.Patient_ID}`)}
                className="clinical-panel p-0 cursor-pointer hover:border-slate-600 hover:bg-slate-800/40 transition-all duration-300 group overflow-hidden relative flex flex-col h-[200px]"
                role="button"
                tabIndex={0}
                aria-label={`View patient ${pId} in bed ${bedNum}`}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    router.push(`/patient/${p.Patient_ID}`);
                  }
                }}
              >
                {/* Header */}
                <div className="p-4 border-b border-slate-800/60 bg-slate-900/30 flex justify-between items-center">
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-bold text-slate-400 bg-slate-950 px-2 py-1 rounded border border-slate-800">BED {bedNum}</span>
                    <span className="text-sm font-semibold text-slate-200">Patient {pId}</span>
                  </div>
                  <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]" title="Stable Status"></div>
                </div>
                
                {/* Body */}
                <div className="p-4 flex-1 flex flex-col justify-center">
                  <div className="flex items-center justify-between mb-4 text-sm">
                    <div className="text-slate-400">Age: <span className="text-slate-200 font-medium">{p.Age || 65}</span></div>
                    <div className="text-slate-400">Sex: <span className="text-slate-200 font-medium">{p.Gender == 1 ? "M" : "F"}</span></div>
                  </div>
                  
                  {/* Mock Sparkline Area */}
                  <div className="h-10 w-full flex items-end justify-between gap-[2px] opacity-30 group-hover:opacity-80 transition-opacity" aria-hidden="true">
                    {[40, 45, 60, 50, 45, 65, 70, 60, 55, 65, 75, 80].map((val, i) => (
                      <div key={i} className="flex-1 bg-blue-500/60 rounded-t-sm" style={{ height: `${val}%` }}></div>
                    ))}
                  </div>
                </div>

                {/* Footer */}
                <div className="px-4 py-3 bg-slate-950/40 flex justify-between items-center text-xs font-semibold text-slate-400 group-hover:text-blue-400 transition-colors border-t border-slate-800/60">
                  <span className="flex items-center gap-1.5 tracking-wider"><Activity className="w-3.5 h-3.5" /> DIGITAL TWIN</span>
                  <ChevronRight className="w-4 h-4" />
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  );
}
