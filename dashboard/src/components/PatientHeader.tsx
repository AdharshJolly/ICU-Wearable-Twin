import React from 'react';

export default function PatientHeader({ patientData, riskState }: { patientData: any, riskState: string }) {
  return (
    <div className="flex items-center gap-3">
      <div className="w-10 h-10 bg-slate-800 border border-slate-700 rounded-full flex items-center justify-center text-base font-bold text-slate-300 shadow-inner">
        {patientData.id}
      </div>
      <div className="flex flex-col justify-center">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-bold text-slate-50 leading-none">{patientData.name}</h1>
          <div className="px-2 py-0.5 rounded-md bg-slate-800/80 border border-slate-700/50 text-[10px] font-bold text-slate-300 uppercase tracking-wider">
            <span className={riskState === 'CRITICAL' ? 'text-red-400' : riskState === 'HIGH_RISK' ? 'text-orange-400' : 'text-emerald-400'}>{riskState}</span>
          </div>
        </div>
        <p className="text-xs text-slate-400 mt-1 leading-none">
          {patientData.age}yo {patientData.gender} &bull; Attending: {patientData.physician}
        </p>
      </div>
    </div>
  );
}
