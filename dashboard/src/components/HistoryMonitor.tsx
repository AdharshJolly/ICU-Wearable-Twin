import React, { useEffect, useState } from 'react';
import { History, RefreshCw } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';

export default function HistoryMonitor({ patientId }: { patientId: string }) {
  const [historyData, setHistoryData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/patients/${patientId}/history`);
        const data = await res.json();
        if (data.history) {
          // Format times
          const formatted = data.history.map((d: any) => {
             const date = new Date(d.time);
             return {
                ...d,
                displayTime: `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`
             };
          });
          setHistoryData(formatted);
        }
      } catch (err) {
        console.error(err);
      }
      setLoading(false);
    };

    fetchHistory();
  }, [patientId]);

  return (
    <div className="clinical-panel flex flex-col h-full w-full relative overflow-hidden bg-black border-slate-700/50 shadow-[0_0_30px_rgba(0,0,0,0.8)] rounded-xl" aria-label="History Monitor" role="region">
      <div className="flex justify-between items-center px-4 py-3 border-b border-slate-800/80 bg-[#040814]">
        <h2 className="text-xs font-bold text-indigo-400 uppercase tracking-widest flex items-center gap-2">
          <History size={14} />
          RETROSPECTIVE TELEMETRY REVIEW
        </h2>
      </div>
      
      <div className="flex-1 relative bg-black p-4">
        {loading ? (
          <div className="flex h-full items-center justify-center text-slate-500 gap-2">
            <RefreshCw className="animate-spin w-5 h-5" /> Loading historical logs...
          </div>
        ) : historyData.length === 0 ? (
          <div className="flex h-full items-center justify-center text-slate-500">
            No historical data available for this patient.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={historyData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="displayTime" stroke="#64748b" fontSize={10} tickMargin={8} />
              <YAxis stroke="#64748b" fontSize={10} domain={[40, 180]} />
              <Tooltip 
                 contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px' }} 
                 itemStyle={{ fontSize: '12px', fontWeight: 'bold' }}
                 labelStyle={{ fontSize: '10px', color: '#94a3b8', marginBottom: '4px' }}
              />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              
              <Line type="monotone" dataKey="hr" stroke="#10b981" strokeWidth={2} dot={false} name="Heart Rate" />
              <Line type="monotone" dataKey="spo2" stroke="#06b6d4" strokeWidth={2} dot={false} name="SpO2" />
              <Line type="monotone" dataKey="sbp" stroke="#cbd5e1" strokeWidth={2} dot={false} name="Sys BP" />
              <Line type="monotone" dataKey="dbp" stroke="#64748b" strokeWidth={2} dot={false} name="Dia BP" />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
