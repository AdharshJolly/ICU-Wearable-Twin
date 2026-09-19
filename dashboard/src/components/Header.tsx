import { Activity, Play, Square } from 'lucide-react';

interface HeaderProps {
  patientData: {
    id: string;
    age: number;
    gender: string;
    physician: string;
  };
  isRunning: boolean;
  setIsRunning: (val: boolean) => void;
}

export function Header({ patientData, isRunning, setIsRunning }: HeaderProps) {
  return (
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
            {isRunning ? <><Square size={16} className="mr-2" /> STOP STREAM</> : <><Play size={16} className="mr-2" /> LIVE STREAM</>}
          </button>
        </div>
      </div>
    </header>
  );
}
