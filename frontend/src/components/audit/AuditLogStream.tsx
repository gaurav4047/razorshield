import { useState } from "react";
import { useAuditStream } from "@/api/useAuditStream";
import { CaseType } from "@/types/api";
import { formatPaiseToRupees } from "@/lib/utils";
import DecisionPacket from "@/components/decision-packet/DecisionPacket";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Activity, Radio } from "lucide-react";


interface AuditLogStreamProps {
  batchId: string | null;
  caseType?: CaseType;
}

export default function AuditLogStream({ batchId, caseType }: AuditLogStreamProps) {
  const [selectedCase, setSelectedCase] = useState<{ module: "A" | "B" | "C"; caseId: string } | null>(null);
  const { logs, isConnected } = useAuditStream(batchId);

  const filteredLogs = caseType
    ? logs.filter((log) => log.case_type === caseType)
    : logs;

  const handleLogClick = (log: any) => {
    let module: "A" | "B" | "C" = "A";
    if (log.case_type === "invoice") module = "B";
    else if (log.case_type === "abandoned_order") module = "C";
    setSelectedCase({ module, caseId: log.case_id });
  };

  const getStageBadge = (stage: string) => {
    switch (stage?.toLowerCase()) {
      case "diagnose":
        return <Badge variant="outline" className="border-blue-200 bg-blue-50 text-blue-700 text-[10px] font-mono uppercase">DIAGNOSE</Badge>;
      case "policy_gate":
        return <Badge variant="outline" className="border-amber-200 bg-amber-50 text-amber-800 text-[10px] font-mono uppercase">POLICY_GATE</Badge>;
      case "execute":
        return <Badge variant="outline" className="border-indigo-200 bg-indigo-50 text-indigo-700 text-[10px] font-mono uppercase">EXECUTE</Badge>;
      case "audit":
        return <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-800 text-[10px] font-mono uppercase">AUDIT</Badge>;
      default:
        return <Badge variant="outline" className="text-slate-600 text-[10px] font-mono uppercase">{stage}</Badge>;
    }
  };

  return (
    <Card className="border-slate-200/80 bg-white shadow-sm overflow-hidden flex flex-col h-[740px]">
      {/* Stream Header */}
      <CardHeader className="border-b border-slate-200/80 bg-slate-50/70 p-4 pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-blue-600" />
            <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-900">
              Live Immutable Audit Stream
            </CardTitle>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="relative flex h-2 w-2">
              {isConnected && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              )}
              <span className={`relative inline-flex rounded-full h-2 w-2 ${isConnected ? "bg-emerald-500" : "bg-amber-500"}`}></span>
            </span>
            <span className={`text-[11px] font-bold ${isConnected ? "text-emerald-700" : "text-amber-700"}`}>
              {isConnected ? "WEBSOCKET LIVE" : "CONNECTING..."}
            </span>
          </div>
        </div>
      </CardHeader>

      {/* Feed Area */}
      <ScrollArea className="flex-1 p-3">
        <div className="space-y-2.5">
          {filteredLogs.length > 0 ? (
            filteredLogs.map((log) => (
              <div
                key={log.id}
                onClick={() => handleLogClick(log)}
                className="group cursor-pointer rounded-lg border border-slate-200/70 bg-white p-3 shadow-2xs transition-all hover:border-blue-400 hover:bg-slate-50/80"
              >
                <div className="flex items-center justify-between text-[11px] text-slate-500 pb-1.5 border-b border-slate-100">
                  <span className="font-mono text-slate-600 font-semibold">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                  <div className="flex items-center gap-1">
                    {getStageBadge(log.stage)}
                    <span className="font-mono text-[10px] text-slate-400">
                      {log.case_type}
                    </span>
                  </div>
                </div>

                <p className="mt-2 font-mono text-xs font-bold text-slate-900 group-hover:text-blue-600 transition-colors">
                  {log.final_action}
                </p>

                <p className="mt-1 text-xs text-slate-600 leading-snug line-clamp-2">
                  {log.reason}
                </p>

                {log.gross_amount_paise && (
                  <div className="mt-2 flex items-center justify-between rounded bg-emerald-50/70 px-2 py-1 text-[11px] text-emerald-800 font-mono border border-emerald-100">
                    <span className="font-sans font-medium text-emerald-900">Confirmed Settlement:</span>
                    <span className="font-bold">{formatPaiseToRupees(log.gross_amount_paise)}</span>
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="p-12 text-center text-xs text-slate-400">
              <Radio className="h-6 w-6 mx-auto mb-2 text-slate-300 animate-pulse" />
              <p>Listening for incoming pipeline audit events...</p>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Selected Case Modal */}
      {selectedCase && (
        <DecisionPacket
          module={selectedCase.module}
          caseId={selectedCase.caseId}
          onClose={() => setSelectedCase(null)}
        />
      )}
    </Card>
  );
}

