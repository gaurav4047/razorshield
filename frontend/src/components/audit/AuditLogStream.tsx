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
        return <Badge variant="outline" className="border-blue-500/30 bg-blue-500/10 text-blue-300 text-[10px] font-mono font-bold uppercase">DIAGNOSE</Badge>;
      case "policy_gate":
        return <Badge variant="outline" className="border-amber-500/30 bg-amber-500/10 text-amber-300 text-[10px] font-mono font-bold uppercase">POLICY_GATE</Badge>;
      case "execute":
        return <Badge variant="outline" className="border-indigo-500/30 bg-indigo-500/10 text-indigo-300 text-[10px] font-mono font-bold uppercase">EXECUTE</Badge>;
      case "audit":
        return <Badge variant="outline" className="border-emerald-500/30 bg-emerald-500/10 text-emerald-300 text-[10px] font-mono font-bold uppercase">AUDIT</Badge>;
      default:
        return <Badge variant="outline" className="border-slate-700 bg-slate-800 text-slate-300 text-[10px] font-mono font-bold uppercase">{stage}</Badge>;
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
            className="border-amber-500/30 bg-amber-500/10 text-amber-300 text-[10px] font-semibold px-2 py-0.5 max-w-[130px] truncate"
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
            className="border-blue-500/30 bg-blue-500/10 text-blue-300 text-[10px] font-semibold px-2 py-0.5 max-w-[130px] truncate"
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
            className="border-indigo-500/30 bg-indigo-500/10 text-indigo-300 text-[10px] font-semibold px-2 py-0.5 max-w-[130px] truncate"
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
      return "border-l-4 border-l-emerald-500 bg-emerald-950/20";
    }
    if (stage === "policy_gate" || action.includes("halt") || action.includes("dispute") || action.includes("approval")) {
      return "border-l-4 border-l-amber-500 bg-amber-950/20";
    }
    return "border-l-4 border-l-blue-500 bg-slate-900/80";
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/90 shadow-2xl backdrop-blur-xl overflow-hidden flex flex-col h-[780px]">
      {/* Stream Header */}
      <div className="border-b border-slate-800 bg-slate-950/70 backdrop-blur-md p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20 shadow-inner">
              <Activity className="h-5 w-5" />
            </div>
            <div>
              <span className="text-sm font-bold uppercase tracking-wider text-white block">
                Live Audit Stream
              </span>
              <span className="text-xs text-slate-400 font-medium">Real-time pipeline telemetry</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Badge className="border-blue-500/30 bg-blue-500/15 text-blue-300 font-semibold text-xs px-2.5 py-0.5 rounded-full shadow-xs">
              {filteredLogs.length} Events
            </Badge>
            <div className="flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-300">
              <span className="relative flex h-2 w-2">
                {isConnected && (
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                )}
                <span className={`relative inline-flex rounded-full h-2 w-2 ${isConnected ? "bg-emerald-500" : "bg-amber-500"}`}></span>
              </span>
              <span className="text-[11px] font-mono tracking-wider">{isConnected ? "LIVE STREAM" : "CONNECTING"}</span>
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
                className={`group cursor-pointer rounded-xl border border-slate-800 bg-slate-900/70 backdrop-blur-sm p-4 shadow-sm transition-all hover:border-blue-500/40 hover:bg-slate-800/80 ${getAccentBorder(log)}`}
              >
                <div className="flex items-center justify-between text-xs text-slate-400 pb-2 border-b border-slate-800">
                  <span className="font-mono text-slate-300 font-bold flex items-center gap-1.5 text-[11px]">
                    <Clock className="h-3 w-3 text-slate-500" />
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                  <div className="flex items-center gap-1.5">
                    {getStageBadge(log.stage)}
                    {getCounterpartyBadge(log)}
                  </div>
                </div>

                <div className="mt-2.5 flex items-center justify-between">
                  <p className="font-mono text-xs sm:text-sm font-bold text-white group-hover:text-blue-300 transition-colors">
                    {log.final_action}
                  </p>
                  <ArrowUpRight className="h-3.5 w-3.5 text-slate-500 group-hover:text-blue-400 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
                </div>

                <p className="mt-1 text-xs text-slate-400 leading-relaxed line-clamp-2 font-normal">
                  {log.reason}
                </p>

                {log.gross_amount_paise && (
                  <div className="mt-2.5 flex items-center justify-between rounded-lg bg-emerald-500/10 px-3 py-1.5 text-xs text-emerald-300 font-mono font-bold border border-emerald-500/20">
                    <span className="font-sans text-[11px] font-semibold text-emerald-400 flex items-center gap-1.5">
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                      Confirmed Settlement:
                    </span>
                    <span className="text-xs font-black">{formatPaiseToRupees(log.gross_amount_paise)}</span>
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="p-16 text-center text-xs text-slate-500 space-y-2">
              <Radio className="h-7 w-7 mx-auto text-slate-600 animate-pulse" />
              <p className="font-semibold text-slate-400">Listening for incoming pipeline audit events...</p>
              <p className="text-[11px] text-slate-500">Events from policy evaluations and webhooks broadcast here live.</p>
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