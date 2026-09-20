import React from 'react';
import { User, ShieldAlert, Activity } from 'lucide-react';

interface PatientHeaderProps {
  patientData: any;
  riskState: string;
}

export default function PatientHeader({ patientData, riskState }: PatientHeaderProps) {
  const getStateColor = (state: string) => {
    switch (state) {
      case 'STABLE': return 'bg-emerald-900/30 text-emerald-400 border-emerald-500/50 shadow-[0_0_10px_rgba(16,185,129,0.2)]';
      case 'WATCH': return 'bg-blue-900/30 text-blue-400 border-blue-500/50 shadow-[0_0_10px_rgba(59,130,246,0.2)]';
      case 'ELEVATED': return 'bg-yellow-900/30 text-yellow-400 border-yellow-500/50 shadow-[0_0_10px_rgba(234,179,8,0.2)]';
      case 'HIGH_RISK': return 'bg-orange-900/30 text-orange-400 border-orange-500/50 shadow-[0_0_10px_rgba(249,115,22,0.2)]';
      case 'CRITICAL': return 'bg-red-900/30 text-red-400 border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.4)] animate-pulse';
      default: return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  return (
    <header className="clinical-panel p-5 mb-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 w-full">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700">
          <User className="text-slate-400 w-6 h-6" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-50 tracking-tight">{patientData.name}</h1>
          <div className="flex gap-3 text-sm text-slate-400 mt-1 font-medium">
            <span>ID: <span className="text-slate-300">{patientData.id}</span></span>
            <span>•</span>
            <span>{patientData.age} yr</span>
            <span>•</span>
            <span>{patientData.gender}</span>
            <span>•</span>
            <span>Attending: <span className="text-slate-300">{patientData.physician}</span></span>
          </div>
        </div>
      </div>
      
      <div className="flex items-center gap-4">
        <div className="text-right">
          <div className="text-xs uppercase tracking-widest text-slate-500 font-bold mb-1">System Status</div>
          <div className={`px-4 py-1.5 rounded-lg text-sm font-bold border uppercase tracking-wider ${getStateColor(riskState)}`}>
            {riskState}
          </div>
        </div>
      </div>
    </header>
  );
}
