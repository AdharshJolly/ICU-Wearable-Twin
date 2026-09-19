import { Activity } from 'lucide-react';

interface ExplainabilityEngineProps {
  reasons: string[];
}

export function ExplainabilityEngine({ reasons }: ExplainabilityEngineProps) {
  return (
    <div className="bg-slate-900 rounded-2xl border border-slate-800 p-5 flex-1 flex flex-col">
      <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">Explainability Engine</h3>
      <div className="flex-1 overflow-y-auto">
          {reasons.length > 0 ? (
              <ul className="space-y-2">
                  {reasons.map((r, i) => (
                      <li key={i} className="text-sm text-red-300 bg-red-950/40 p-2 rounded border border-red-900/50">
                          • {r}
                      </li>
                  ))}
              </ul>
          ) : (
              <div className="h-full flex items-center justify-center border-2 border-dashed border-slate-800 rounded-xl bg-slate-900/50">
                  <div className="text-center p-4 text-slate-500 text-sm">
                      <Activity className="mx-auto mb-2 opacity-50" size={24} />
                      No anomalies detected.
                  </div>
              </div>
          )}
      </div>
    </div>
  );
}
