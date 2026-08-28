import { useAuditStream } from "@/api/useAuditStream";
import { CaseType } from "@/types/api";

interface AuditLogStreamProps {
  batchId: string | null;
  caseType?: CaseType;
}

export default function AuditLogStream({ batchId, caseType }: AuditLogStreamProps) {
  const { logs, isConnected } = useAuditStream(batchId);

  const filteredLogs = caseType
    ? logs.filter((log) => log.case_type === caseType)
    : logs;

  return (
    <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
        <h2 className="text-sm font-semibold text-slate-800">Live Audit Stream</h2>
        <span
          className={`inline-flex items-center gap-1.5 text-xs ${
            isConnected ? "text-emerald-600" : "text-amber-600"
          }`}
        >
          <span className={`h-2 w-2 rounded-full ${isConnected ? "bg-emerald-500" : "bg-amber-500"}`} />
          {isConnected ? "Live" : "Connecting..."}
        </span>
      </div>

      <div className="max-h-[600px] overflow-y-auto divide-y divide-slate-100 p-2">
        {filteredLogs.length > 0 ? (
          filteredLogs.map((log) => (
            <div key={log.id} className="p-3 text-xs">
              <div className="flex items-center justify-between text-slate-500">
                <span className="font-mono">{new Date(log.timestamp).toLocaleTimeString()}</span>
                <span className="rounded bg-slate-100 px-1.5 py-0.5 font-semibold text-slate-700">{log.stage}</span>
              </div>
              <p className="mt-1 font-semibold text-slate-900">{log.final_action}</p>
              <p className="text-slate-600">{log.reason}</p>
            </div>
          ))
        ) : (
          <div className="p-8 text-center text-xs text-slate-400">
            No audit log events recorded yet.
          </div>
        )}
      </div>
    </div>
  );
}
