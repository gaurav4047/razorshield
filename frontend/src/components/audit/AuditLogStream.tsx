import { useState } from "react";
import { useAuditStream } from "@/api/useAuditStream";
import { CaseType } from "@/types/api";
import { formatPaiseToRupees } from "@/lib/utils";
import DecisionPacket from "@/components/decision-packet/DecisionPacket";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Activity, Radio, ArrowUpRight, Clock, CheckCircle2 } from "lucide-react";

interface AuditLogStreamProps {
  batchId: string | null;
  caseType?: CaseType;
}

export default function AuditLogStream({ batchId, caseType }: AuditLogStreamProps) {
  const [selectedCase, setSelectedCase] = useState<{ module: "A" | "B" | "C"; caseId: string } | null>(null);
  const { logs, isConnected } = useAuditStream(batchId, caseType);

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
        return <Badge variant="outline" className="border-blue-200 bg-blue-50 text-[#0066ff] text-[11px] font-mono font-bold uppercase">DIAGNOSE</Badge>;
      case "policy_gate":
        return <Badge variant="outline" className="border-amber-200 bg-amber-50 text-amber-900 text-[11px] font-mono font-bold uppercase">POLICY_GATE</Badge>;
      case "execute":
        return <Badge variant="outline" className="border-indigo-200 bg-indigo-50 text-indigo-700 text-[11px] font-mono font-bold uppercase">EXECUTE</Badge>;
      case "audit":
        return <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-800 text-[11px] font-mono font-bold uppercase">AUDIT</Badge>;
      default:
        return <Badge variant="outline" className="text-slate-600 text-[11px] font-mono font-bold uppercase">{stage}</Badge>;
    }
  };

  const getCounterpartyBadge = (log: any) => {
    const rawName = log.counterparty_name || "";
    // Clean corporate suffixes (Pvt Ltd, LLP, etc.) to keep badge compact and readable
    const cleanName = rawName
      ? rawName.replace(/\s+(Pvt|Ltd|LLP|Inc|Corp|Private|Limited)\.?/gi, "").trim()
      : "";

    switch (log.case_type) {
      case "invoice": {
        const display = cleanName || log.case_reference || "B2B Buyer";
        return (
          <Badge
            variant="outline"
            className="border-amber-200 bg-amber-50 text-amber-900 text-[10px] font-bold px-2 py-0.5 max-w-[140px] truncate"
            title={rawName ? `${rawName} (${log.case_reference || "Invoice"})` : "B2B Invoice"}
          >
            {display}
          </Badge>
        );
      }
      case "abandoned_order": {
        const display = cleanName || "Cart Shopper";
        return (
          <Badge
            variant="outline"
            className="border-blue-200 bg-blue-50 text-[#0066ff] text-[10px] font-bold px-2 py-0.5 max-w-[140px] truncate"
            title={rawName || "Cart Shopper"}
          >
            {display}
          </Badge>
        );
      }
      case "payment_case": {
        const display = cleanName || "AutoPay Mandate";
        return (
          <Badge
            variant="outline"
            className="border-indigo-200 bg-indigo-50 text-indigo-800 text-[10px] font-bold px-2 py-0.5 max-w-[140px] truncate"
            title={log.case_reference || "Payment Mandate"}
          >
            {display}
          </Badge>
        );
      }
      default:
        return null;
    }
  };

  const getAccentBorder = (log: any) => {
    const action = (log.final_action || "").toLowerCase();
    const stage = (log.stage || "").toLowerCase();
    if (action.includes("recover") || action.includes("paid") || action.includes("settled")) {
      return "border-l-4 border-l-emerald-500";
    }
    if (stage === "policy_gate" || action.includes("halt") || action.includes("dispute") || action.includes("approval")) {
      return "border-l-4 border-l-amber-500";
    }
    return "border-l-4 border-l-[#0066ff]";
  };

  return (
    <div className="rounded-3xl border border-blue-300/90 bg-gradient-to-b from-blue-200/90 via-blue-100/80 to-indigo-100/90 shadow-xs overflow-hidden flex flex-col h-[780px]">
      {/* Stream Header */}
      <div className="border-b border-blue-200 bg-white/95 backdrop-blur-md p-5 sm:p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-[#0066ff] border border-blue-200/80 shadow-2xs">
              <Activity className="h-5 w-5" />
            </div>
            <div>
              <span className="text-base font-black uppercase tracking-wider text-[#0c2340] block">
                Live Audit Stream
              </span>
              <span className="text-xs text-slate-500 font-medium">Real-time pipeline telemetry</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Badge className="border-blue-200/80 bg-blue-50 text-[#0066ff] font-extrabold text-xs px-2.5 py-0.5 rounded-full shadow-2xs">
              {filteredLogs.length} Events
            </Badge>
            <div className="flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700 shadow-2xs">
              <span className="relative flex h-2 w-2">
                {isConnected && (
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                )}
                <span className={`relative inline-flex rounded-full h-2 w-2 ${isConnected ? "bg-emerald-500" : "bg-amber-500"}`}></span>
              </span>
              <span>{isConnected ? "ACTIVE" : "CONNECTING"}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Feed Area */}
      <ScrollArea className="flex-1 p-4 sm:p-5">
        <div className="space-y-3.5">
          {filteredLogs.length > 0 ? (
            filteredLogs.map((log) => (
              <div
                key={log.id}
                onClick={() => handleLogClick(log)}
                className={`group cursor-pointer rounded-2xl border border-blue-100/90 bg-white/95 backdrop-blur-sm p-4 sm:p-5 shadow-2xs transition-all hover:border-[#0066ff] hover:shadow-xs ${getAccentBorder(log)}`}
              >
                <div className="flex items-center justify-between text-xs text-slate-500 pb-2.5 border-b border-slate-100">
                  <span className="font-mono text-slate-700 font-bold flex items-center gap-1.5">
                    <Clock className="h-3.5 w-3.5 text-slate-400" />
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                  <div className="flex items-center gap-1.5">
                    {getStageBadge(log.stage)}
                    {getCounterpartyBadge(log)}
                  </div>
                </div>

                <div className="mt-3 flex items-center justify-between">
                  <p className="font-mono text-sm sm:text-base font-black text-[#0c2340] group-hover:text-[#0066ff] transition-colors">
                    {log.final_action}
                  </p>
                  <ArrowUpRight className="h-4 w-4 text-slate-300 group-hover:text-[#0066ff] group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
                </div>

                <p className="mt-1 text-xs sm:text-sm text-slate-600 leading-relaxed line-clamp-2 font-medium">
                  {log.reason}
                </p>

                {log.gross_amount_paise && (
                  <div className="mt-3 flex items-center justify-between rounded-xl bg-emerald-50/90 px-3.5 py-2 text-xs text-emerald-900 font-mono font-black border border-emerald-200/80 shadow-2xs">
                    <span className="font-sans font-bold text-emerald-800 flex items-center gap-1.5">
                      <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                      Confirmed Settlement:
                    </span>
                    <span className="text-sm font-black">{formatPaiseToRupees(log.gross_amount_paise)}</span>
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="p-16 text-center text-xs sm:text-sm text-slate-400 space-y-2">
              <Radio className="h-8 w-8 mx-auto text-slate-300 animate-pulse" />
              <p className="font-semibold text-slate-500">Listening for incoming pipeline audit events...</p>
              <p className="text-xs text-slate-400">Events from policy evaluations and webhooks broadcast here live.</p>
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
    </div>
  );
}