import re

file_path = "dashboard/src/app/patient/[id]/page.tsx"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add counterfactual state
state_code = """
  const [consultData, setConsultData] = useState<any>(null);
  const [isConsulting, setIsConsulting] = useState(false);
  const [counterfactualData, setCounterfactualData] = useState<any>(null);
  const [isSimulating, setIsSimulating] = useState(false);
"""
content = re.sub(
    r"const \[consultData, setConsultData\] = useState<any>\(null\);\s*const \[isConsulting, setIsConsulting\] = useState\(false\);",
    state_code.strip(),
    content
)

# 2. Add runCounterfactual function
func_code = """
  const requestConsult = async () => {
"""
new_func_code = """
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
"""
content = content.replace(func_code.strip(), new_func_code.strip())

# 3. Add metrics state update
metrics_code = """
        setMetrics({
          hr: data.hr,
          rr: data.rr,
          temp: data.temp,
          spo2: data.spo2
        });
"""
new_metrics_code = """
        setMetrics({
          hr: data.hr,
          rr: data.rr,
          temp: data.temp,
          spo2: data.spo2,
          sbp: data.sbp || 120,
          dbp: data.dbp || 80
        });
"""
content = content.replace(metrics_code.strip(), new_metrics_code.strip())

# 4. Add the button
btn_code = """
                <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 flex justify-between items-center">
                  <span>Explainability Engine</span>
                  <button 
                    onClick={requestConsult}
"""
new_btn_code = """
                <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 flex justify-between items-center">
                  <span>Explainability & Sim</span>
                  <div className="flex gap-2">
                  <button 
                    onClick={runCounterfactual}
                    disabled={isSimulating}
                    className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs px-3 py-1.5 rounded-lg flex items-center font-bold transition disabled:opacity-50"
                  >
                    {isSimulating ? <RefreshCw size={14} className="animate-spin mr-2" /> : <Activity size={14} className="mr-2" />}
                    {isSimulating ? "SIMULATING..." : "DIGITAL TWIN SIM"}
                  </button>
                  <button 
                    onClick={requestConsult}
"""
content = content.replace(btn_code.strip(), new_btn_code.strip())

# Close the flex gap-2 div
btn_close_code = """
                    {isConsulting ? "CONSULTING..." : "BOARD CONSULT"}
                  </button>
                </h3>
"""
new_btn_close_code = """
                    {isConsulting ? "CONSULTING..." : "BOARD CONSULT"}
                  </button>
                  </div>
                </h3>
"""
content = content.replace(btn_close_code.strip(), new_btn_close_code.strip())

# 5. Add Counterfactual Modal
modal_code = """
      {/* Consult Modal */}
"""
new_modal_code = """
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
"""
content = content.replace(modal_code.strip(), new_modal_code.strip())

# Also add the initial metrics state fix
init_metrics = """
  const [metrics, setMetrics] = useState({
    hr: 75,
    rr: 16,
    temp: 36.8,
    spo2: 98
  });
"""
new_init_metrics = """
  const [metrics, setMetrics] = useState({
    hr: 75,
    rr: 16,
    temp: 36.8,
    spo2: 98,
    sbp: 120,
    dbp: 80
  });
"""
content = content.replace(init_metrics.strip(), new_init_metrics.strip())

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Patched page.tsx")
