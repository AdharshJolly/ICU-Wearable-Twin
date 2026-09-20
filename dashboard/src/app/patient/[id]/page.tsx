"use client";

import React, { useState, useEffect, useRef, use } from 'react';
import { Activity, Thermometer, Wind, HeartPulse, Play, Square, User, Users, AlertTriangle, Clock, Zap, Heart, History, RefreshCw, FileText, ChevronRight } from 'lucide-react';
// @ts-ignore
import { SmoothieChart, TimeSeries } from 'smoothie';
import DigitalTwinPanel from '@/components/DigitalTwinPanel';
import PatientHeader from '@/components/PatientHeader';
import ICUStripCard from '@/components/ICUStripCard';

export default function Dashboard({ params }: { params: Promise<{ id: string }> }) {
  const unwrappedParams = use(params);
  const patientId = unwrappedParams.id;
  
  const [isRunning, setIsRunning] = useState(false);
  const [riskState, setRiskState] = useState('STABLE');
  const [patientData, setPatientData] = useState({ 
    id: patientId, 
    name: `Patient ${patientId}`,
    age: 65,
    gender: 'Unknown',
    physician: 'Dr. Sarah Chen'
  });

  const [metrics, setMetrics] = useState({ hr: 75, rr: 16, temp: 36.8, spo2: 98, sbp: 120, dbp: 80 });
  const metricsRef = useRef(metrics);
  useEffect(() => { metricsRef.current = metrics; }, [metrics]);

  const [reasons, setReasons] = useState<string[]>([]);
  const [logs, setLogs] = useState<{time: string, type: string, message: string}[]>([]);
  
  const ws = useRef<WebSocket | null>(null);
  
  // Smoothie chart time series
  const hrSeriesSide = useRef<TimeSeries>(new TimeSeries());
  const spo2SeriesSide = useRef<TimeSeries>(new TimeSeries());
  const rrSeriesSide = useRef<TimeSeries>(new TimeSeries());
  const tempSeriesSide = useRef<TimeSeries>(new TimeSeries());
  
  const [viewMode, setViewMode] = useState<'live' | 'history'>('live');
  const [consultData, setConsultData] = useState<any>(null);
  const [isConsulting, setIsConsulting] = useState(false);
  const [twinSnapshot, setTwinSnapshot] = useState<any>(null);
  const [activeMedications, setActiveMedications] = useState<Record<string, number>>({});
  const riskStateRef = useRef(riskState);

  useEffect(() => { riskStateRef.current = riskState; }, [riskState]);

  // High-frequency UI update for smoothness (SmoothieChart needs this)
  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date().getTime();
      const m = metricsRef.current;
      hrSeriesSide.current.append(now, m.hr);
      spo2SeriesSide.current.append(now, m.spo2);
      rrSeriesSide.current.append(now, m.rr);
      tempSeriesSide.current.append(now, m.temp);
    }, 250);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/patients/${patientId}`)
      .then(res => res.json())
      .then(data => {
        if (!data.error) {
          setPatientData({
            id: data.id,
            name: `Patient ${data.id}`,
            age: data.age,
            gender: data.gender,
            physician: data.physician
          });
        }
      });
  }, [patientId]);

  useEffect(() => {
    if (isRunning) {
      ws.current = new WebSocket(`${(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace('http', 'ws')}/ws/simulate/${patientId}`); 
      setLogs(prev => [{ time: new Date().toLocaleTimeString(), type: 'info', message: 'WebSocket Connected. Streaming Patient Data...' }, ...prev]);
      
      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        setMetrics({
          hr: data.hr, rr: data.rr, temp: data.temp, spo2: data.spo2, sbp: data.sbp || 120, dbp: data.dbp || 80
        });
        
        if (data.active_medications) setActiveMedications(data.active_medications);

        if (data.risk_state !== riskStateRef.current) {
            let type = 'info';
            if (data.risk_state === 'HIGH_RISK') type = 'warning';
            if (data.risk_state === 'CRITICAL') type = 'critical';
            setLogs(prev => [{ time: data.time, type, message: `Risk State changed to ${data.risk_state}` }, ...prev]);
            setRiskState(data.risk_state);
        }
        
        if (data.reasons && data.reasons.length > 0) setReasons(data.reasons);
        if (data.twin_snapshot) setTwinSnapshot(data.twin_snapshot);
      };

      ws.current.onclose = () => {
        setLogs(prev => [{ time: new Date().toLocaleTimeString(), type: 'warning', message: 'WebSocket Disconnected.' }, ...prev]);
        setIsRunning(false);
      };
      
      ws.current.onerror = (e) => {
        console.error("WebSocket Error", e);
      };
    } else {
      if (ws.current) ws.current.close();
    }
    return () => { if (ws.current) ws.current.close(); };
  }, [isRunning, patientId]);

  const handleIntervention = (action: string) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ action }));
      setLogs(prev => [{ time: new Date().toLocaleTimeString(), type: 'info', message: `Applied Intervention: ${action.toUpperCase().replace('_', ' ')}` }, ...prev]);
    }
  };

  const requestConsult = async () => {
    setIsConsulting(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/patients/${patientId}/consult`, { method: 'POST' });
      const data = await res.json();
      setConsultData(data);
    } catch(err) {
      console.error(err);
    }
    setIsConsulting(false);
  };

  return (
    <div className="min-h-screen p-4 lg:p-6 mx-auto flex flex-col max-w-[1600px] h-screen overflow-hidden">
      
      <div className="flex justify-between items-center flex-shrink-0 w-full gap-4">
        <PatientHeader patientData={patientData} riskState={riskState} />
        
        <div className="flex gap-4">
          <button 
            onClick={() => setIsRunning(!isRunning)}
            className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold shadow-lg transition-all ${
              isRunning ? 'bg-red-500/20 text-red-500 border border-red-500/50 hover:bg-red-500/30' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 hover:bg-emerald-500/30'
            }`}
          >
            {isRunning ? <Square size={18} /> : <Play size={18} />}
            <span>{isRunning ? 'STOP MONITOR' : 'START MONITOR'}</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 flex-1 min-h-0 overflow-hidden mt-4">
        
        {/* LEFT COLUMN: Vitals & Twin */}
        <div className="xl:col-span-8 flex flex-col gap-4 overflow-y-auto custom-scrollbar pr-2 pb-4">
          
          <div className="flex items-center justify-between px-2 flex-shrink-0">
            <h2 className="text-sm font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-400" /> Real-time Telemetry
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 flex-shrink-0">
            <ICUStripCard title="HEART RATE" value={metrics.hr} unit="bpm" color="green" series={hrSeriesSide.current} minScale={40} maxScale={160} />
            <ICUStripCard title="SpO2" value={metrics.spo2} unit="%" color="cyan" series={spo2SeriesSide.current} minScale={75} maxScale={100} />
            <ICUStripCard title="RESP RATE" value={metrics.rr} unit="/min" color="white" series={rrSeriesSide.current} minScale={5} maxScale={40} />
            <div className="flex gap-4">
              <div className="flex-1 clinical-panel flex flex-col items-center justify-center p-4 h-24">
                <div className="text-slate-400 text-[10px] font-bold uppercase tracking-widest mb-1">NIBP</div>
                <div className="text-3xl font-mono text-slate-200 tracking-tighter">
                  {metrics.sbp.toFixed(0)}<span className="text-xl text-slate-500 mx-1">/</span>{metrics.dbp.toFixed(0)}
                </div>
              </div>
              <div className="flex-1 clinical-panel flex flex-col items-center justify-center p-4 h-24">
                <div className="text-slate-400 text-[10px] font-bold uppercase tracking-widest mb-1">TEMP</div>
                <div className="text-3xl font-mono text-slate-200 tracking-tighter">{metrics.temp.toFixed(1)}°</div>
              </div>
            </div>
          </div>

          <div className="flex-1 mt-2 min-h-[400px]">
             <DigitalTwinPanel snapshot={twinSnapshot} trajectories={null} />
          </div>

        </div>

        {/* RIGHT COLUMN: Interventions & AI Consult */}
        <div className="xl:col-span-4 flex flex-col gap-6 overflow-y-auto custom-scrollbar pr-2 pb-4">
          
          {/* Active Medications Widget */}
          {Object.keys(activeMedications).length > 0 && (
            <div className="clinical-panel p-5 border-blue-500/30 shadow-[0_0_15px_rgba(59,130,246,0.1)] flex-shrink-0">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-400" /> Pharmacokinetics (Live)
              </h3>
              <div className="space-y-4">
                {Object.entries(activeMedications).map(([med, level]) => (
                  <div key={med}>
                    <div className="flex justify-between text-sm mb-1 font-semibold text-slate-300">
                      <span>{med}</span>
                      <span>{level.toFixed(0)}%</span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                      <div className="bg-gradient-to-r from-blue-500 to-indigo-400 h-1.5 rounded-full transition-all duration-500" style={{ width: `${level}%` }}></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Clinical Interventions */}
          <div className="clinical-panel p-5 flex-shrink-0">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
              <HeartPulse className="w-4 h-4 text-rose-400" /> Clinical Interventions
            </h3>
            <div className="grid grid-cols-2 gap-3">
              <button onClick={() => handleIntervention('administer_o2')} className="p-3 bg-slate-800/50 hover:bg-cyan-900/40 border border-slate-700/50 hover:border-cyan-500/50 rounded-xl text-xs font-bold text-slate-300 hover:text-cyan-400 transition-all text-center">
                + SUPPLEMENTAL O2
              </button>
              <button onClick={() => handleIntervention('fluids')} className="p-3 bg-slate-800/50 hover:bg-blue-900/40 border border-slate-700/50 hover:border-blue-500/50 rounded-xl text-xs font-bold text-slate-300 hover:text-blue-400 transition-all text-center">
                + IV FLUIDS
              </button>
              <button onClick={() => handleIntervention('beta_blockers')} className="p-3 bg-slate-800/50 hover:bg-purple-900/40 border border-slate-700/50 hover:border-purple-500/50 rounded-xl text-xs font-bold text-slate-300 hover:text-purple-400 transition-all text-center col-span-2">
                + BETA BLOCKERS
              </button>
            </div>
          </div>

          {/* AI Consult Agent */}
          <div className="clinical-panel p-0 overflow-hidden flex flex-col flex-1 min-h-[350px]">
            <div className="p-4 border-b border-slate-800/60 bg-slate-900/30 flex justify-between items-center">
               <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                 <User className="w-4 h-4 text-purple-400" /> Board Consult (GenAI)
               </h3>
               <button 
                  onClick={requestConsult} 
                  disabled={isConsulting}
                  className="bg-purple-600 hover:bg-purple-500 text-white px-3 py-1.5 rounded-lg text-xs font-bold transition-colors disabled:opacity-50"
               >
                 {isConsulting ? 'ANALYZING...' : 'RUN PIPELINE'}
               </button>
            </div>
            
            <div className="p-5 overflow-y-auto flex-1 custom-scrollbar">
              {!consultData ? (
                <div className="h-full flex flex-col items-center justify-center text-slate-600 gap-3 min-h-[200px]">
                  <Activity className="w-8 h-8 opacity-50" />
                  <p className="text-xs font-medium uppercase tracking-widest text-center">No Consult History<br/>Click Run Pipeline</p>
                </div>
              ) : (
                <div className="space-y-5 text-sm">
                  {typeof consultData.chief_resident === 'object' ? (
                    <>
                      <div>
                        <div className="text-[10px] uppercase font-bold text-slate-500 tracking-widest mb-1">Primary Diagnosis</div>
                        <div className="font-semibold text-slate-200">{consultData.chief_resident.primary_diagnosis}</div>
                      </div>
                      <div>
                        <div className="text-[10px] uppercase font-bold text-slate-500 tracking-widest mb-1">Synthesis</div>
                        <div className="text-slate-300 leading-relaxed">{consultData.chief_resident.summary}</div>
                      </div>
                      {consultData.chief_resident.recommended_interventions?.length > 0 && (
                        <div>
                           <div className="text-[10px] uppercase font-bold text-cyan-400 tracking-widest mb-1">Recommendations</div>
                           <ul className="list-disc pl-4 space-y-1 text-slate-300">
                             {consultData.chief_resident.recommended_interventions.map((item:string, i:number) => <li key={i}>{item}</li>)}
                           </ul>
                        </div>
                      )}
                      {consultData.chief_resident.citations?.length > 0 && (
                        <div className="pt-3 border-t border-slate-800/60">
                           <div className="text-[10px] uppercase font-bold text-emerald-500 tracking-widest mb-2">RAG References</div>
                           <div className="flex flex-wrap gap-2">
                             {consultData.chief_resident.citations.map((cite:string, i:number) => (
                               <span key={i} className="px-2 py-1 bg-emerald-950/30 border border-emerald-900/50 rounded text-emerald-400 text-[10px]">{cite}</span>
                             ))}
                           </div>
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="text-slate-300 leading-relaxed whitespace-pre-wrap">{consultData.chief_resident}</div>
                  )}
                </div>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
