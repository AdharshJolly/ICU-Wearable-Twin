"use client";

import { useEffect, useState } from 'react';
import { Activity, Users, AlertTriangle, CheckCircle } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function WardView() {
  const router = useRouter();
  const [patients, setPatients] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/patients')
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
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans p-6">
      <header className="flex justify-between items-center mb-8 bg-slate-900 p-6 rounded-2xl border border-slate-800 shadow-xl">
        <div className="flex items-center space-x-4">
          <div className="bg-blue-600/20 p-3 rounded-xl border border-blue-500/30">
            <Users className="text-blue-400" size={32} />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-slate-100 tracking-wide">CENTRAL NURSING STATION</h1>
            <p className="text-sm text-slate-400 mt-1">WARD A • {patients.length} BEDS OCCUPIED</p>
          </div>
        </div>
        <div className="flex items-center space-x-4 bg-slate-950/50 p-4 rounded-xl border border-slate-800">
           <div className="flex items-center text-sm font-semibold text-green-400"><CheckCircle size={16} className="mr-2" /> All Stable</div>
        </div>
      </header>

      {loading ? (
        <div className="flex items-center justify-center h-64 text-slate-500">
          <Activity className="animate-spin mr-3" size={24} /> Loading Patient Roster...
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {patients.map((p, index) => (
            <div 
              key={p.Patient_ID || index} 
              onClick={() => router.push(`/patient/${p.Patient_ID}`)}
              className="bg-slate-900 border border-slate-800 rounded-2xl p-6 cursor-pointer hover:bg-slate-800 hover:border-slate-600 hover:shadow-2xl hover:shadow-blue-900/20 transition-all duration-300 group"
            >
              <div className="flex justify-between items-start mb-4">
                <div className="bg-slate-800 px-3 py-1 rounded text-xs font-bold text-slate-400 group-hover:text-slate-300">
                  BED {String(index + 1).padStart(2, '0')}
                </div>
                <div className="flex items-center space-x-1 text-green-500 bg-green-500/10 px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider">
                  Stable
                </div>
              </div>
              
              <h2 className="text-xl font-bold text-slate-100 mb-1">Patient {p.Patient_ID || `P00${index+1}`}</h2>
              <div className="flex space-x-3 text-sm text-slate-500 mb-6">
                <span>Age: {p.Age || 65}</span>
                <span>•</span>
                <span>Sex: {p.Gender == 1 ? "M" : "F"}</span>
              </div>

              <div className="bg-slate-950 rounded-lg p-3 flex justify-between items-center border border-slate-800 group-hover:border-slate-700">
                 <div className="flex items-center">
                    <Activity size={14} className="text-slate-500 mr-2" />
                    <span className="text-xs text-slate-400 uppercase tracking-widest font-semibold">Telemetry</span>
                 </div>
                 <span className="text-xs font-bold text-blue-400 group-hover:text-blue-300">CONNECT &rarr;</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
