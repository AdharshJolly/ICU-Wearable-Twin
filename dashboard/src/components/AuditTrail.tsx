import { Clock } from 'lucide-react';

export interface Log {
  time: string;
  type: string;
  message: string;
}

interface AuditTrailProps {
  logs: Log[];
}

export function AuditTrail({ logs }: AuditTrailProps) {
  return (
    <div className="bg-slate-900 rounded-2xl border border-slate-800 p-5 flex-[1.2] flex flex-col">
      <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center">
        <Clock size={16} className="mr-2" /> Audit Trail
      </h3>
      
      <div className="flex-1 overflow-y-auto pr-2 space-y-4">
        {logs.length === 0 ? (
            <div className="text-slate-600 text-sm italic">Waiting for events...</div>
        ) : (
            logs.map((log, i) => <LogItem key={i} time={log.time} type={log.type as any} message={log.message} />)
        )}
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
