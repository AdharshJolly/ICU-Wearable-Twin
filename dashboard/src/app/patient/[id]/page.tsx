"use client";

import React, { useState, useEffect, useRef, use } from 'react';
import { Activity, Thermometer, Wind, HeartPulse, Play, Square, User, Users, AlertTriangle, Clock, Zap, Heart, History, RefreshCw } from 'lucide-react';
// @ts-ignore
import { SmoothieChart, TimeSeries } from 'smoothie';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';

export default function Dashboard({ params }: { params: Promise<{ id: string }> }) {
  const unwrappedParams = use(params);
  const patientId = unwrappedParams.id;
  
  const [isRunning, setIsRunning] = useState(false);
  const [riskState, setRiskState] = useState('STABLE');
  const [patientData, setPatientData] = useState({ 
    id: patientId, 
    name: 'Doe, J.',
    age: 65,
    gender: 'Male',
    physician: 'Dr. Sarah Chen'
  });

  useEffect(() => {
    fetch(`http://localhost:8000/api/patients/${patientId}`)
      .then(res => res.json())
      .then(data => {
        if (!data.error) {
          setPatientData({
            id: data.id,
            name: 'Doe, J.', // Placeholder name
            age: data.age,
            gender: data.gender,
            physician: data.physician
          });
        }
      })
      .catch(err => console.error("Error fetching patient", err));
  }, [patientId]);
  const [reasons, setReasons] = useState<string[]>([]);
  const [logs, setLogs] = useState<{time: string, type: string, message: string}[]>([]);
  
  // Refs
  const ws = useRef<WebSocket | null>(null);
  const mainCanvasRef = useRef<HTMLCanvasElement | null>(null);
  
  // Smoothie chart time series
  const hrSeriesSide = useRef<TimeSeries>(new TimeSeries());
  const spo2SeriesSide = useRef<TimeSeries>(new TimeSeries());
  const rrSeriesSide = useRef<TimeSeries>(new TimeSeries());
  const tempSeriesSide = useRef<TimeSeries>(new TimeSeries());
  const [viewMode, setViewMode] = useState<'live' | 'history'>('live');
  const [historyData, setHistoryData] = useState<any[]>([]);
  const [isFetchingHistory, setIsFetchingHistory] = useState(false);
  const [consultData, setConsultData] = useState<any>(null);
  const [isConsulting, setIsConsulting] = useState(false);
  const [counterfactualData, setCounterfactualData] = useState<any>(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [riskForecast, setRiskForecast] = useState<any>(null);
  const [showAuditTrail, setShowAuditTrail] = useState(false);
  const [activeMedications, setActiveMedications] = useState<Record<string, number>>({});

  const fetchHistory = async () => {
    setIsFetchingHistory(true);
    try {
      const res = await fetch(`http://localhost:8000/api/patients/${patientId}/history`);
      const data = await res.json();
      setHistoryData(data.history || []);
    } catch (err) {
      console.error(err);
    }
    setIsFetchingHistory(false);
  };

  const runCounterfactual = async () => {
    setIsSimulating(true);
    try {
      const res = await fetch(`http://localhost:8000/api/patients/${patientId}/counterfactual`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ current_vitals: metrics, state: riskState })
      });
      const data = await res.json();
      setCounterfactualData(data);
    } catch(err) {
      console.error(err);
    }
    setIsSimulating(false);
  };

  const requestConsult = async () => {
    setIsConsulting(true);
    try {
      const res = await fetch(`http://localhost:8000/api/patients/${patientId}/consult`, {
        method: 'POST'
      });
      const data = await res.json();
      setConsultData(data);
    } catch (err) {
      console.error(err);
    }
    setIsConsulting(false);
  };

  useEffect(() => {
    if (viewMode === 'history') {
      setIsRunning(false); // Stop live stream
      fetchHistory();
    }
  }, [viewMode]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (viewMode === 'live') {
      const fetchForecast = async () => {
        try {
          const res = await fetch(`http://localhost:8000/api/patients/${patientId}/risk-forecast`);
          const data = await res.json();
          if (!data.error) {
            setRiskForecast(data);
          }
        } catch (err) {}
      };
      fetchForecast(); // initial fetch
      interval = setInterval(fetchForecast, 5000); // every 5s
    }
    return () => clearInterval(interval);
  }, [viewMode, patientId]);
  
  const hrSeriesMain = useRef<TimeSeries>(new TimeSeries());
  const spo2SeriesMain = useRef<TimeSeries>(new TimeSeries());
  
  const mainChartRef = useRef<SmoothieChart | null>(null);

  // Initial Data
  const [metrics, setMetrics] = useState({
    hr: 75,
    rr: 16,
    temp: 36.8,
    spo2: 98,
    sbp: 120,
    dbp: 80
  });

  const [llmSummary, setLlmSummary] = useState<string>("");

  const handleIntervention = (action: string) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ action }));
      setLogs(prev => [{ time: new Date().toLocaleTimeString(), type: 'info', message: `Applied Intervention: ${action.toUpperCase().replace('_', ' ')}` }, ...prev]);
    }
  };

  // Initialize and manage Main Smoothie Chart
  useEffect(() => {
    if (viewMode === 'live' && mainCanvasRef.current) {
      if (!mainChartRef.current) {
        mainChartRef.current = new SmoothieChart({
          millisPerPixel: 20, 
          grid: {
            strokeStyle: '#1e293b',
            fillStyle: '#000000', 
            lineWidth: 1,
            millisPerLine: 2000,
            verticalSections: 6
          },
          labels: { fillStyle: '#64748b', fontSize: 12, precision: 0 },
          timestampFormatter: SmoothieChart.timeFormatter,
          minValue: 30,
          maxValue: 170,
          responsive: true,
        });
  
        mainChartRef.current.addTimeSeries(hrSeriesMain.current, { 
          strokeStyle: '#22c55e', 
          lineWidth: 2 
        });
        
        mainChartRef.current.addTimeSeries(spo2SeriesMain.current, { 
          strokeStyle: '#06b6d4', 
          lineWidth: 2 
        });
      }
      
      mainChartRef.current.streamTo(mainCanvasRef.current, 1000);
    }
    
    return () => {
      if (mainChartRef.current && viewMode !== 'live') {
        mainChartRef.current.stop();
      }
    };
  }, [viewMode]);

  // WebSocket Connection Management
  const riskStateRef = useRef(riskState);
  useEffect(() => {
    riskStateRef.current = riskState;
  }, [riskState]);

  useEffect(() => {
    if (isRunning) {
      ws.current = new WebSocket(`ws://localhost:8000/ws/simulate/${patientId}`); 
      
      setLogs(prev => [{ time: new Date().toLocaleTimeString(), type: 'info', message: 'WebSocket Connected. Streaming Patient Data...' }, ...prev]);

      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        const now = new Date().getTime();
        
        hrSeriesSide.current.append(now, data.hr);
        spo2SeriesSide.current.append(now, data.spo2);
        rrSeriesSide.current.append(now, data.rr);
        tempSeriesSide.current.append(now, data.temp);
        
        hrSeriesMain.current.append(now, data.hr);
        spo2SeriesMain.current.append(now, data.spo2);

        setMetrics({
          hr: data.hr,
          rr: data.rr,
          temp: data.temp,
          spo2: data.spo2,
          sbp: data.sbp || 120,
          dbp: data.dbp || 80
        });
        
        if (data.active_medications) {
          setActiveMedications(data.active_medications);
        }

        if (data.risk_state !== riskStateRef.current) {
            let type = 'info';
            if (data.risk_state === 'HIGH RISK') type = 'warning';
            if (data.risk_state === 'CRITICAL') type = 'critical';
            
            setLogs(prev => [{ 
              time: data.time, 
              type, 
              message: `Risk State changed to ${data.risk_state}` 
            }, ...prev]);
            setRiskState(data.risk_state);
        }
        
        if (data.reasons && data.reasons.length > 0) {
           setReasons(data.reasons);
        } else {
           setReasons([]);
        }
        
        if (data.llm_summary) {
           setLlmSummary(data.llm_summary);
        }
      };

      ws.current.onclose = () => {
        setLogs(prev => [{ time: new Date().toLocaleTimeString(), type: 'info', message: 'WebSocket Disconnected.' }, ...prev]);
        setIsRunning(false);
      };
      
      ws.current.onerror = (error) => {
        console.error("WebSocket error", error);
        setLogs(prev => [{ time: new Date().toLocaleTimeString(), type: 'critical', message: 'WebSocket Error. Server offline.' }, ...prev]);
        setIsRunning(false);
      }
      
    } else {
      if (ws.current) {
        ws.current.close();
      }
    }

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [isRunning, patientId]);

  return (
    <div className="h-screen w-screen overflow-hidden bg-slate-950 text-slate-200 font-sans p-4 flex flex-col">
      {/* Top Navbar / Demographics */}
      <header className="flex-none flex flex-wrap justify-between items-center gap-4 mb-4 bg-slate-900 p-4 rounded-2xl border border-slate-800 shadow-lg">
        <div className="flex items-center space-x-4">
          <div className="bg-blue-600/20 p-2 rounded-lg border border-blue-500/30">
            <Activity className="text-blue-400" size={28} />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-100 tracking-wide">ICU DIGITAL TWIN</h1>
            <p className="text-xs text-slate-400">BED {patientData.id} • WARD A</p>
          </div>
        </div>

        <div className="flex items-center space-x-4 md:space-x-8">
          
          <div className="hidden xl:flex space-x-2 bg-slate-800/50 p-1.5 rounded-lg border border-slate-700">
            <button onClick={() => handleIntervention('administer_o2')} className="text-[10px] uppercase font-bold px-3 py-1.5 rounded bg-slate-700 hover:bg-cyan-600 hover:text-white transition-colors">Give O2</button>
            <button onClick={() => handleIntervention('beta_blockers')} className="text-[10px] uppercase font-bold px-3 py-1.5 rounded bg-slate-700 hover:bg-green-600 hover:text-white transition-colors">Beta Blocker</button>
            <button onClick={() => handleIntervention('fluids')} className="text-[10px] uppercase font-bold px-3 py-1.5 rounded bg-slate-700 hover:bg-blue-600 hover:text-white transition-colors">IV Fluids</button>
          </div>
          
          <div className="hidden lg:flex flex-col">
            <span className="text-xs text-slate-500 uppercase font-semibold">Patient ID</span>
            <span className="font-mono text-slate-200">{patientData.id}</span>
          </div>
          <div className="hidden lg:flex flex-col">
            <span className="text-xs text-slate-500 uppercase font-semibold">Demographics</span>
            <span className="text-slate-200">{patientData.age}yo {patientData.gender}</span>
          </div>
          <div className="hidden lg:flex flex-col">
            <span className="text-xs text-slate-500 uppercase font-semibold">Physician</span>
            <span className="text-slate-200">{patientData.physician}</span>
          </div>
          
          <div className="flex space-x-2">
            {viewMode === 'live' ? (
              <>
                <button 
                  onClick={() => setIsRunning(!isRunning)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-bold shadow transition ${
                    isRunning ? 'bg-red-500/20 text-red-500 border border-red-500/50 hover:bg-red-500/30' : 'bg-emerald-500/20 text-emerald-500 border border-emerald-500/50 hover:bg-emerald-500/30'
                  }`}
                >
                  {isRunning ? <Square size={16} /> : <Play size={16} />}
                  <span>{isRunning ? 'STOP' : 'LIVE'}</span>
                </button>
                <button 
                  onClick={() => setViewMode('history')}
                  className="flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-bold bg-slate-800 text-slate-300 hover:bg-slate-700 transition"
                >
                  <History size={16} />
                  <span>HISTORY</span>
                </button>
              </>
            ) : (
              <button 
                onClick={() => { setViewMode('live'); setIsRunning(true); }}
                className="flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-bold bg-blue-600 hover:bg-blue-500 text-white transition"
              >
                <Activity size={16} />
                <span>BACK TO LIVE</span>
              </button>
            )}
            <button 
              onClick={() => setShowAuditTrail(true)}
              className="flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-bold bg-slate-800 text-slate-300 hover:bg-slate-700 transition"
            >
              <Clock size={16} />
              <span className="hidden sm:inline">AUDIT TRAIL</span>
            </button>
          </div>
        </div>
      </header>

      {/* Bento Box Grid */}
      <div className="flex-1 min-h-0 grid grid-cols-12 gap-4">
        
        {/* Left Column: Authentic ICU Vitals Strip (4 cols) */}
        <div className="col-span-4 flex flex-col gap-3 bg-black p-3 rounded-2xl border border-slate-800 min-h-0">
          <ICUStripCard title="ECG / HR" value={metrics.hr} unit="BPM" color="green" series={hrSeriesSide.current} minScale={30} maxScale={170} />
          <ICUStripCard title="SpO2" value={metrics.spo2} unit="%" color="cyan" series={spo2SeriesSide.current} minScale={70} maxScale={105} />
          <ICUStripCard title="RESP" value={metrics.rr} unit="RPM" color="white" series={rrSeriesSide.current} minScale={0} maxScale={45} />
          <ICUStripCard title="TEMP" value={metrics.temp} unit="°C" color="orange" series={tempSeriesSide.current} minScale={34} maxScale={41} />
        </div>

        {/* Center Column: Main Trajectory (5 cols) */}
        <div className="col-span-5 flex flex-col gap-4 min-h-0">
          
          {/* Risk Banner */}
          <div className={`p-6 rounded-2xl border flex items-center justify-between transition-colors duration-500 ${
            riskState === 'STABLE' ? 'bg-emerald-950/30 border-emerald-900/50 text-emerald-400' :
            riskState === 'HIGH RISK' ? 'bg-yellow-950/30 border-yellow-900/50 text-yellow-500' :
            'bg-red-950/30 border-red-900/50 text-red-400 shadow-[0_0_30px_rgba(220,38,38,0.15)]'
          }`}>
            <div>
              <p className="text-xs uppercase tracking-wider font-bold opacity-80 mb-1">Current State</p>
              <h2 className="text-3xl font-black tracking-tight">{riskState}</h2>
            </div>
            {riskState === 'CRITICAL' && <AlertTriangle size={40} className="animate-pulse" />}
            {riskState === 'STABLE' && <Activity size={40} className="opacity-50" />}
          </div>

          {/* Main Chart (Smoothie Canvas) */}
          <div className="flex-1 bg-black rounded-2xl border border-slate-800 p-6 flex flex-col relative overflow-hidden">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider flex items-center">
                <Zap size={16} className="mr-2 text-yellow-500" /> Overlay Monitor
              </h3>
              <div className="flex space-x-4 text-xs font-bold uppercase tracking-wider">
                <span className="text-green-500">ECG (BPM)</span>
                <span className="text-cyan-500">SpO2 (%)</span>
              </div>
            </div>
            
            <div className="bg-slate-900 rounded-2xl border border-slate-800 p-1 flex-1 relative min-h-0">
              {viewMode === 'live' ? (
                <>
                  {!isRunning && hrSeriesMain.current.data.length === 0 && (
                    <div className="absolute inset-0 flex items-center justify-center text-slate-600 font-medium z-10 bg-black">
                      Click LIVE STREAM to connect to patient data...
                    </div>
                  )}
                  
                  {/* Active Medications Widget */}
                  {Object.keys(activeMedications).length > 0 && (
                    <div className="absolute top-4 right-4 bg-slate-950/90 border border-slate-700 p-3 rounded-xl shadow-2xl backdrop-blur-md z-10 w-64">
                      <h4 className="text-[9px] text-slate-400 font-bold uppercase tracking-widest mb-2 flex items-center">
                        <Activity size={12} className="mr-1 text-purple-400"/> Pharmacokinetics
                      </h4>
                      <div className="space-y-2.5">
                        {Object.entries(activeMedications).map(([med, level]) => (
                           <div key={med}>
                             <div className="flex justify-between text-[10px] font-semibold mb-1">
                               <span className="text-emerald-400 truncate pr-2">{med}</span>
                               <span className="text-slate-300 font-mono">{level.toFixed(0)}%</span>
                             </div>
                             <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
                               <div className="bg-emerald-500 h-full rounded-full transition-all duration-1000 ease-linear" style={{ width: `${Math.min(level, 100)}%` }}></div>
                             </div>
                           </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <canvas ref={mainCanvasRef} className="w-full h-full rounded-lg" style={{ display: 'block' }}></canvas>
                </>
              ) : (
                <div className="absolute inset-0 p-4 bg-slate-950 rounded-lg border border-slate-800">
                  {isFetchingHistory ? (
                    <div className="flex h-full items-center justify-center text-slate-500">
                      <RefreshCw className="animate-spin mr-2" /> Loading History...
                    </div>
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={historyData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                        <XAxis dataKey="time" stroke="#64748b" fontSize={12} />
                        <YAxis stroke="#64748b" fontSize={12} domain={[30, 170]} />
                        <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b' }} />
                        <Legend />
                        <Line type="monotone" dataKey="hr" stroke="#22c55e" strokeWidth={2} dot={false} name="Heart Rate (BPM)" />
                        <Line type="monotone" dataKey="spo2" stroke="#06b6d4" strokeWidth={2} dot={false} name="SpO2 (%)" />
                      </LineChart>
                    </ResponsiveContainer>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Explainability & Logs (3 cols) */}
        <div className="col-span-3 flex flex-col gap-4 min-h-0">
                    {/* AI Explainability */}
            <div className="bg-slate-900 rounded-2xl border border-slate-800 p-5 flex-1 flex flex-col min-h-0">
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 flex justify-between items-center">
                <span>Explainability Engine</span>
                <button 
                  onClick={requestConsult}
                  disabled={isConsulting}
                  className="bg-purple-600 hover:bg-purple-500 text-white text-xs px-3 py-1.5 rounded-lg flex items-center font-bold transition disabled:opacity-50"
                >
                  {isConsulting ? <RefreshCw size={14} className="animate-spin mr-2" /> : <Users size={14} className="mr-2" />}
                  {isConsulting ? "CONSULTING..." : "BOARD CONSULT"}
                </button>
              </h3>
            
            {/* LLM Clinical Note */}
            <div className="mb-4 bg-slate-950 p-4 rounded-xl border border-slate-800 relative flex-none">
              <div className="absolute top-0 right-0 px-2 py-1 bg-purple-500/20 text-purple-400 text-[9px] uppercase font-bold rounded-bl-lg rounded-tr-lg">LLM Note</div>
              <p className="text-sm text-slate-300 leading-relaxed font-serif">
                {llmSummary || "Waiting for baseline assessment..."}
              </p>
            </div>
            
            {/* Predictive Risk Forecast */}
            <div className="mb-4 bg-slate-950 p-4 rounded-xl border border-slate-800 relative flex-none">
              <div className="absolute top-0 right-0 px-2 py-1 bg-cyan-500/20 text-cyan-400 text-[9px] uppercase font-bold rounded-bl-lg rounded-tr-lg">Ensemble Model Risk</div>
              
              {riskForecast ? (
                <div>
                  <div className="flex items-end mb-2">
                    <span className="text-3xl font-bold font-mono text-cyan-400 mr-2">{riskForecast.risk_probability}%</span>
                    <span className="text-xs text-slate-400 mb-1 leading-tight">Ensemble Probability<br/>(1 Hour Horizon)</span>
                  </div>
                  
                  <div className="flex flex-col space-y-2 mb-4">
                    <div className="flex space-x-2">
                      <div className="bg-slate-900 border border-slate-800 px-2 py-1 rounded text-[9px] font-mono text-slate-400 flex-1">
                        <span className="text-purple-400 block font-sans">LSTM</span>
                        {riskForecast.lstm_prob}%
                      </div>
                      <div className="bg-slate-900 border border-slate-800 px-2 py-1 rounded text-[9px] font-mono text-slate-400 flex-1">
                        <span className="text-blue-400 block font-sans">XGBoost</span>
                        {riskForecast.xgboost_prob}%
                      </div>
                    </div>
                    {/* Interactive Weight Slider (Mock for UI Demo) */}
                    <div className="px-1 mt-2">
                      <div className="flex justify-between text-[8px] text-slate-500 mb-1 font-bold uppercase">
                        <span>100% PyTorch</span>
                        <span>100% XGBoost</span>
                      </div>
                      <input type="range" min="0" max="100" defaultValue="40" className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-500" />
                    </div>
                  </div>
                  
                  <div className="space-y-2 mt-2">
                    <div className="text-[10px] uppercase text-slate-500 font-bold mb-1">SHAP Feature Explanations</div>
                    {riskForecast.top_factors.map((factor: any, idx: number) => (
                      <div key={idx} className="flex items-center justify-between bg-slate-900 rounded p-1.5 border border-slate-800">
                        <span className="text-[11px] text-slate-300 truncate w-32">{factor.description}</span>
                        <div className="flex-1 mx-2 bg-slate-950 h-1.5 rounded-full overflow-hidden flex">
                          {factor.shap_impact > 0 ? (
                            <>
                              <div className="flex-1 border-r border-slate-800"></div>
                              <div className="flex-1 bg-red-500" style={{ width: `${Math.min(factor.shap_impact * 20, 100)}%` }}></div>
                            </>
                          ) : (
                            <>
                              <div className="flex-1 bg-blue-500 ml-auto border-r border-slate-800" style={{ width: `${Math.min(Math.abs(factor.shap_impact) * 20, 100)}%` }}></div>
                              <div className="flex-1"></div>
                            </>
                          )}
                        </div>
                        <span className={`text-[10px] font-mono font-bold ${factor.shap_impact > 0 ? 'text-red-400' : 'text-blue-400'}`}>
                          {factor.shap_impact > 0 ? '+' : ''}{factor.shap_impact.toFixed(2)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-xs text-slate-500 flex items-center h-24 justify-center">
                  <RefreshCw className="animate-spin mr-2" size={14} /> Aggregating temporal features...
                </div>
              )}
            </div>

            <div className="flex-1 overflow-y-auto">
                {reasons.length > 0 ? (
                    <ul className="space-y-2">
                        {reasons.map((r, i) => (
                            <li key={i} className="text-xs text-red-300 bg-red-950/40 p-2 rounded border border-red-900/50">
                                • {r}
                            </li>
                        ))}
                    </ul>
                ) : (
                    <div className="h-full flex items-center justify-center border-2 border-dashed border-slate-800 rounded-xl bg-slate-900/50">
                        <div className="text-center p-4 text-slate-500 text-sm">
                            <Activity className="mx-auto mb-2 opacity-50" size={24} />
                            No structural anomalies.
                        </div>
                    </div>
                )}
            </div>
          </div>
        </div>

      </div>

      {/* Audit Trail Slide-over Overlay */}
      {showAuditTrail && (
        <div className="absolute inset-y-0 right-0 w-96 bg-slate-900 border-l border-slate-700 shadow-2xl z-40 flex flex-col transform transition-transform duration-300">
          <div className="flex justify-between items-center p-5 border-b border-slate-800 bg-slate-950/50">
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center">
              <Clock size={16} className="mr-2" /> Audit Trail
            </h3>
            <button 
              onClick={() => setShowAuditTrail(false)}
              className="text-slate-400 hover:text-white bg-slate-800 p-1.5 rounded-full transition-colors"
            >
              ✕
            </button>
          </div>
          
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            {logs.length === 0 ? (
               <div className="text-slate-600 text-sm italic text-center mt-10">Waiting for events...</div>
            ) : (
               logs.map((log, i) => <LogItem key={i} time={log.time} type={log.type as any} message={log.message} />)
            )}
          </div>
        </div>
      )}

      {/* Counterfactual Modal */}
      {counterfactualData && (
        <div className="absolute inset-0 bg-slate-950/90 z-50 flex items-center justify-center p-8 backdrop-blur-md">
          <div className="bg-slate-900 border border-slate-700 rounded-3xl w-full max-w-5xl max-h-[90vh] overflow-y-auto p-8 shadow-2xl flex flex-col">
            <div className="flex justify-between items-center mb-8 flex-none">
              <h2 className="text-2xl font-bold text-slate-100 flex items-center tracking-wide">
                <Activity className="mr-3 text-indigo-400" size={32} /> Counterfactual Trajectory Simulation
              </h2>
              <button onClick={() => setCounterfactualData(null)} className="text-slate-400 hover:text-white bg-slate-800 p-2 rounded-full transition-colors">
                ✕
              </button>
            </div>
            
            <p className="text-slate-400 mb-6">
              Projecting 60 seconds into the future based on current state <span className="font-bold text-white">({counterfactualData.current_state})</span> using the ICU Early Warning Model.
            </p>

            <div className="bg-slate-950 p-6 rounded-2xl border border-slate-800 flex-1 min-h-[400px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                  <XAxis dataKey="step" stroke="#94a3b8" tick={{fill: '#94a3b8'}} type="number" domain={[0, 'dataMax']} />
                  <YAxis stroke="#94a3b8" tick={{fill: '#94a3b8'}} domain={[0, 100]} label={{ value: 'Risk %', angle: -90, position: 'insideLeft', fill: '#94a3b8' }} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.5rem', color: '#f8fafc' }}
                    itemStyle={{ fontWeight: 'bold' }}
                  />
                  <Legend wrapperStyle={{ paddingTop: '20px' }} />
                  
                  {Object.entries(counterfactualData.trajectories).map(([key, traj]: [string, any]) => (
                    <Line 
                      key={key}
                      type="monotone"
                      name={traj.label}
                      data={traj.risk.map((r: number, i: number) => ({ step: i, risk: r }))}
                      dataKey="risk"
                      stroke={traj.color}
                      strokeWidth={3}
                      dot={false}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Consult Modal */}
      {consultData && (
        <div className="absolute inset-0 bg-slate-950/90 z-50 flex items-center justify-center p-8 backdrop-blur-md">
          <div className="bg-slate-900 border border-slate-700 rounded-3xl w-full max-w-5xl max-h-[90vh] overflow-y-auto p-8 shadow-2xl flex flex-col">
            <div className="flex justify-between items-center mb-8 flex-none">
              <h2 className="text-2xl font-bold text-slate-100 flex items-center tracking-wide">
                <Users className="mr-3 text-purple-400" size={32} /> Multi-Agent Medical Board
              </h2>
              <button onClick={() => setConsultData(null)} className="text-slate-400 hover:text-white bg-slate-800 p-2 rounded-full transition-colors">
                ✕
              </button>
            </div>
            
            <div className="grid grid-cols-2 gap-6 mb-6 flex-none">
              <div className="bg-slate-950/50 p-6 rounded-2xl border border-rose-900/40 relative overflow-hidden">
                <div className="absolute top-0 left-0 w-1 h-full bg-rose-500/50"></div>
                <h3 className="text-rose-400 font-bold mb-3 flex items-center text-lg"><HeartPulse className="mr-2" size={20}/> Virtual Cardiologist</h3>
                <p className="text-sm text-slate-300 font-serif leading-relaxed whitespace-pre-wrap">{consultData.cardiologist}</p>
              </div>
              <div className="bg-slate-950/50 p-6 rounded-2xl border border-cyan-900/40 relative overflow-hidden">
                <div className="absolute top-0 left-0 w-1 h-full bg-cyan-500/50"></div>
                <h3 className="text-cyan-400 font-bold mb-3 flex items-center text-lg"><Wind className="mr-2" size={20}/> Virtual Pulmonologist</h3>
                <p className="text-sm text-slate-300 font-serif leading-relaxed whitespace-pre-wrap">{consultData.pulmonologist}</p>
              </div>
            </div>

            <div className="bg-purple-900/20 p-6 rounded-2xl border border-purple-500/30 relative flex-1">
              <div className="absolute top-0 left-0 w-1 h-full bg-purple-500/50 rounded-l-2xl"></div>
              <h3 className="text-purple-400 font-bold text-xl mb-4 flex items-center"><User className="mr-2" size={24}/> Chief Resident Synthesis</h3>
              <p className="text-base text-slate-200 font-serif leading-relaxed whitespace-pre-wrap">{consultData.chief_resident}</p>
            </div>
            
            {/* RAG Citations */}
            {consultData.citations && consultData.citations.length > 0 && (
              <div className="mt-6 bg-slate-950 p-4 rounded-xl border border-slate-800">
                <h4 className="text-[10px] uppercase text-slate-500 font-bold mb-2 flex items-center">
                  <Activity size={12} className="mr-1 text-emerald-400" /> Grounded In Clinical Protocols (RAG)
                </h4>
                <div className="flex gap-2 flex-wrap">
                  {consultData.citations.map((cite: string, idx: number) => (
                    <span key={idx} className="bg-emerald-900/30 text-emerald-400 text-xs px-3 py-1 rounded-full border border-emerald-800/50">
                      {cite}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  );
}

// Authentic ICU Strip Card Component
function ICUStripCard({ title, value, unit, color, series, minScale, maxScale }: { title: string, value: number, unit: string, color: string, series: any, minScale: number, maxScale: number }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  
  const colorMap: Record<string, { bg: string, text: string, chart: string }> = {
    green: { bg: 'bg-green-950/20', text: 'text-green-500', chart: '#22c55e' },
    cyan: { bg: 'bg-cyan-950/20', text: 'text-cyan-400', chart: '#22d3ee' },
    white: { bg: 'bg-slate-800/30', text: 'text-slate-200', chart: '#f1f5f9' },
    orange: { bg: 'bg-orange-950/20', text: 'text-orange-500', chart: '#f97316' },
  };

  const style = colorMap[color];

  useEffect(() => {
    if (canvasRef.current && series) {
      const chart = new SmoothieChart({
        millisPerPixel: 15, // Fast scroll for ECG feel
        grid: { strokeStyle: 'transparent', fillStyle: 'transparent', borderVisible: false },
        labels: { disabled: true },
        minValue: minScale,
        maxValue: maxScale,
        responsive: true
      });
      
      // Removed fillStyle entirely for a pure neon line look
      chart.addTimeSeries(series, { 
        strokeStyle: style.chart, 
        lineWidth: 2.5 
      });
      
      chart.streamTo(canvasRef.current, 1000);
      
      return () => {
         chart.stop();
      };
    }
  }, [series, style.chart, minScale, maxScale]);

  return (
    <div className="flex h-24 overflow-hidden group">
      {/* Waveform area (Left) */}
      <div className="flex-[2] relative border border-slate-900 bg-black rounded-l-xl">
        <canvas ref={canvasRef} className="w-full h-full" style={{ display: 'block' }}></canvas>
        <div className={`absolute top-2 left-3 ${style.text} text-xs font-bold tracking-widest opacity-80`}>
          {title}
        </div>
      </div>
      
      {/* Numbers area (Right) */}
      <div className={`flex-1 flex flex-col justify-center items-end p-4 border-y border-r border-slate-900 rounded-r-xl ${style.bg}`}>
        <div className={`text-4xl font-black font-mono tracking-tighter ${style.text}`}>
          {value.toFixed(1)}
        </div>
        <div className={`text-[10px] font-bold uppercase mt-1 ${style.text} opacity-60 tracking-widest`}>
          {unit}
        </div>
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
