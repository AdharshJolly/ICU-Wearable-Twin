"use client";

import React, { useState, useEffect, useRef, use } from 'react';
import { Activity, Thermometer, Wind, HeartPulse, Play, Square, User, Users, AlertTriangle, Clock, Zap, Heart, History, RefreshCw, FileText, ChevronRight, ChevronLeft } from 'lucide-react';
import Link from 'next/link';
// @ts-ignore
import { SmoothieChart, TimeSeries } from 'smoothie';
import DigitalTwinPanel from '@/components/DigitalTwinPanel';
import PatientHeader from '@/components/PatientHeader';
import ICUStripCard from '@/components/ICUStripCard';
import MainMonitor from '@/components/MainMonitor';
import HistoryMonitor from '@/components/HistoryMonitor';

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

  // High-frequency authentic waveform generation for individual metrics
  useEffect(() => {
    let lastTime = new Date().getTime();
    let cardiacPhase = 0;
    let respPhase = 0;
    
    const interval = setInterval(() => {
      const now = new Date().getTime();
      const dt = now - lastTime;
      lastTime = now;
      const m = metricsRef.current;
      
      const hr = m.hr || 75;
      const rr = m.rr || 16;
      
      cardiacPhase += dt / (60000 / hr);
      if (cardiacPhase > 1) cardiacPhase -= 1;
      
      respPhase += dt / (60000 / rr);
      if (respPhase > 1) respPhase -= 1;

      // ECG for HR card
      let ecg = m.hr; 
      if (cardiacPhase > 0.1 && cardiacPhase < 0.15) ecg += Math.sin((cardiacPhase - 0.1) * 20 * Math.PI) * 10;
      else if (cardiacPhase > 0.3 && cardiacPhase < 0.32) ecg -= 15;
      else if (cardiacPhase >= 0.32 && cardiacPhase < 0.35) ecg += 40;
      else if (cardiacPhase >= 0.35 && cardiacPhase < 0.38) ecg -= 20;
      else if (cardiacPhase > 0.55 && cardiacPhase < 0.7) ecg += Math.sin((cardiacPhase - 0.55) * 6.66 * Math.PI) * 10;

      // Pleth for SpO2 card
      let spo2P = (cardiacPhase + 0.4) % 1.0;
      let plethVal = Math.sin(spo2P * Math.PI);
      if (spo2P > 0.4 && spo2P < 0.6) plethVal -= 0.15 * Math.sin((spo2P - 0.4) * 5 * Math.PI);
      if (plethVal < 0) plethVal = 0;
      let spo2Wave = (m.spo2 - 5) + (plethVal * 15);

      // Capnography for RR card
      let rrVal = Math.sin(respPhase * Math.PI);
      if (rrVal < 0) rrVal = 0;
      rrVal = Math.min(rrVal * 1.5, 1.0); 
      let rrWave = (m.rr - 5) + (rrVal * 15);

      hrSeriesSide.current.append(now, ecg);
      spo2SeriesSide.current.append(now, spo2Wave);
      rrSeriesSide.current.append(now, rrWave);

    }, 30);
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
    if (viewMode === 'history' && isRunning) {
       setIsRunning(false); // Auto-pause live monitor if switching to history
    }
  }, [viewMode]);

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
        setTwinSnapshot(data);
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
    <div className="min-h-screen xl:h-screen p-2 lg:p-4 mx-auto flex flex-col max-w-[1800px] xl:overflow-hidden">
      
      <div className="flex flex-col md:flex-row justify-between md:items-center mb-2 flex-shrink-0 w-full gap-2">
        
        <div className="flex items-center gap-2">
          <Link href="/" aria-label="Back to Ward View" className="p-2 bg-slate-800/50 hover:bg-slate-700/60 border border-slate-700/50 rounded-lg transition-colors text-slate-400 hover:text-slate-200">
            <ChevronLeft size={18} />
          </Link>
          <PatientHeader patientData={patientData} riskState={riskState} />
        </div>
        
        <div className="flex gap-2 w-full md:w-auto">
          <button 
            onClick={() => setViewMode(viewMode === 'live' ? 'history' : 'live')}
            className={`flex-1 md:flex-none flex items-center justify-center gap-1.5 px-4 py-1.5 rounded-lg text-sm font-bold shadow-lg transition-all ${
              viewMode === 'history' ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/50 hover:bg-indigo-500/30' : 'bg-slate-800/50 text-slate-400 border border-slate-700/50 hover:bg-slate-700/50'
            }`}
          >
            <History size={14} />
            <span>{viewMode === 'history' ? 'BACK TO LIVE' : 'HISTORY'}</span>
          </button>

          {viewMode === 'live' && (
            <button 
              onClick={() => setIsRunning(!isRunning)}
              aria-label={isRunning ? "Stop Monitor" : "Start Monitor"}
              className={`flex-1 md:flex-none flex items-center justify-center gap-1.5 px-4 py-1.5 rounded-lg text-sm font-bold shadow-lg transition-all ${
                isRunning ? 'bg-red-500/20 text-red-500 border border-red-500/50 hover:bg-red-500/30' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 hover:bg-emerald-500/30'
              }`}
            >
              {isRunning ? <Square size={14} aria-hidden="true" /> : <Play size={14} aria-hidden="true" />}
              <span>{isRunning ? 'STOP MONITOR' : 'START MONITOR'}</span>
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-3 flex-1 min-h-0 xl:overflow-hidden">
        
        {/* LEFT COLUMN: Vitals (No Scroll) */}
        <div className="xl:col-span-8 flex flex-col gap-3 h-full xl:overflow-hidden pr-0 xl:pr-1 pb-0">
          
          <div className="flex-1 min-h-[250px]">
            {viewMode === 'live' ? (
               <MainMonitor metrics={metrics} isRunning={isRunning} />
            ) : (
               <HistoryMonitor patientId={patientId} />
            )}
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 flex-shrink-0" aria-live="polite">
            <ICUStripCard title="HEART RATE" value={metrics.hr} unit="bpm" color="green" series={hrSeriesSide.current} minScale={40} maxScale={160} />
            <ICUStripCard title="SpO2" value={metrics.spo2} unit="%" color="cyan" series={spo2SeriesSide.current} minScale={75} maxScale={100} />
            <ICUStripCard title="RESP RATE" value={metrics.rr} unit="/min" color="white" series={rrSeriesSide.current} minScale={5} maxScale={40} />
            <div className="flex gap-2">
              <div className="flex-1 clinical-panel flex flex-col items-center justify-center p-2 h-20">
                <div className="text-slate-400 text-[10px] font-bold uppercase tracking-widest mb-1">NIBP</div>
                <div className="text-xl font-mono text-slate-200 tracking-tighter">
                  {metrics.sbp.toFixed(0)}<span className="text-sm text-slate-500 mx-1" aria-hidden="true">/</span>{metrics.dbp.toFixed(0)}
                </div>
              </div>
              <div className="flex-1 clinical-panel flex flex-col items-center justify-center p-2 h-20">
                <div className="text-slate-400 text-[10px] font-bold uppercase tracking-widest mb-1">TEMP</div>
                <div className="text-xl font-mono text-slate-200 tracking-tighter">{metrics.temp.toFixed(1)}&deg;</div>
              </div>
            </div>
          </div>

        </div>

        {/* RIGHT COLUMN: Interventions, Digital Twin, & AI Consult */}
        <div className="xl:col-span-4 flex flex-col gap-3 xl:overflow-y-auto custom-scrollbar pr-0 xl:pr-1 pb-2">
          
          {/* Active Medications Widget */}
          {Object.keys(activeMedications).length > 0 && (
            <div className="clinical-panel p-3 border-blue-500/30 shadow-[0_0_15px_rgba(59,130,246,0.1)] flex-shrink-0">
              <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2 flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5 text-amber-400" aria-hidden="true" /> Pharmacokinetics (Live)
              </h3>
              <div className="space-y-2">
                {Object.entries(activeMedications).map(([med, level]) => (
                  <div key={med}>
                    <div className="flex justify-between text-[10px] mb-1 font-semibold text-slate-300">
                      <span>{med}</span>
                      <span>{level.toFixed(0)}%</span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-1 overflow-hidden" role="progressbar" aria-valuenow={level} aria-valuemin={0} aria-valuemax={100}>
                      <div className="bg-gradient-to-r from-blue-500 to-indigo-400 h-1 rounded-full transition-all duration-500" style={{ width: `${level}%` }}></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Clinical Interventions */}
          <div className="clinical-panel p-3 flex-shrink-0">
            <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2 flex items-center gap-1.5">
              <HeartPulse className="w-3.5 h-3.5 text-rose-400" aria-hidden="true" /> Clinical Interventions
            </h3>
            <div className="grid grid-cols-2 gap-1.5">
              <button onClick={() => handleIntervention('administer_o2')} className="p-2 bg-slate-800/50 hover:bg-cyan-900/40 border border-slate-700/50 hover:border-cyan-500/50 rounded-lg text-[10px] font-bold text-slate-300 hover:text-cyan-400 transition-all text-center focus:ring-2 focus:ring-cyan-500 outline-none">
                + O2
              </button>
              <button onClick={() => handleIntervention('fluids')} className="p-2 bg-slate-800/50 hover:bg-blue-900/40 border border-slate-700/50 hover:border-blue-500/50 rounded-lg text-[10px] font-bold text-slate-300 hover:text-blue-400 transition-all text-center focus:ring-2 focus:ring-blue-500 outline-none">
                + IV FLUIDS
              </button>
              <button onClick={() => handleIntervention('beta_blockers')} className="p-2 bg-slate-800/50 hover:bg-purple-900/40 border border-slate-700/50 hover:border-purple-500/50 rounded-lg text-[10px] font-bold text-slate-300 hover:text-purple-400 transition-all text-center col-span-2 focus:ring-2 focus:ring-purple-500 outline-none">
                + BETA BLOCKERS
              </button>
            </div>
          </div>

          {/* Digital Twin Panel */}
          <div className="flex-shrink-0 min-h-[300px] flex flex-col">
            <DigitalTwinPanel snapshot={twinSnapshot} trajectories={null} />
          </div>

          {/* AI Consult Agent */}
          <div className="clinical-panel p-0 overflow-hidden flex flex-col flex-shrink-0 min-h-[300px]">
            <div className="p-2.5 border-b border-slate-800/60 bg-slate-900/30 flex justify-between items-center">
               <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1.5">
                 <User className="w-3.5 h-3.5 text-purple-400" aria-hidden="true" /> Board Consult
               </h3>
               <button 
                  onClick={requestConsult} 
                  disabled={isConsulting}
                  className="bg-purple-600 hover:bg-purple-500 text-white px-2.5 py-1 rounded-md text-[10px] font-bold transition-colors disabled:opacity-50 focus:ring-2 focus:ring-purple-400 outline-none"
               >
                 {isConsulting ? 'ANALYZING...' : 'RUN PIPELINE'}
               </button>
            </div>
            
            <div className="p-3 overflow-y-auto flex-1 custom-scrollbar">
              {!consultData ? (
                <div className="h-full flex flex-col items-center justify-center text-slate-600 gap-2 min-h-[150px]">
                  <Activity className="w-6 h-6 opacity-50" aria-hidden="true" />
                  <p className="text-[10px] font-medium uppercase tracking-widest text-center">No Consult History<br/>Click Run Pipeline</p>
                </div>
              ) : (
                <div className="space-y-3 text-sm" aria-live="polite">
                  {typeof consultData.chief_resident === 'object' ? (
                    <>
                      <div>
                        <div className="text-[9px] uppercase font-bold text-slate-500 tracking-widest mb-1">Primary Diagnosis</div>
                        <div className="font-semibold text-slate-200 text-xs">{consultData.chief_resident.primary_diagnosis}</div>
                      </div>
                      <div>
                        <div className="text-[9px] uppercase font-bold text-slate-500 tracking-widest mb-1">Synthesis</div>
                        <div className="text-slate-300 leading-relaxed text-[11px]">{consultData.chief_resident.summary}</div>
                      </div>
                      {consultData.chief_resident.recommended_interventions?.length > 0 && (
                        <div>
                           <div className="text-[9px] uppercase font-bold text-cyan-400 tracking-widest mb-1">Recommendations</div>
                           <ul className="list-disc pl-3 space-y-1 text-slate-300 text-[11px]">
                             {consultData.chief_resident.recommended_interventions.map((item:string, i:number) => <li key={i}>{item}</li>)}
                           </ul>
                        </div>
                      )}
                      {consultData.chief_resident.citations?.length > 0 && (
                        <div className="pt-2 border-t border-slate-800/60">
                           <div className="text-[9px] uppercase font-bold text-emerald-500 tracking-widest mb-1.5">RAG References</div>
                           <div className="flex flex-wrap gap-1.5">
                             {consultData.chief_resident.citations.map((cite:string, i:number) => (
                               <span key={i} className="px-1.5 py-0.5 bg-emerald-950/30 border border-emerald-900/50 rounded text-emerald-400 text-[9px]">{cite}</span>
                             ))}
                           </div>
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="text-slate-300 leading-relaxed whitespace-pre-wrap text-xs">{consultData.chief_resident}</div>
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
