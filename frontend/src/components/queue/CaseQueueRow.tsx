import { formatPaiseToRupees } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { TableRow, TableCell } from "@/components/ui/table";
import { 
  Zap, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  ShieldAlert,
  ArrowRight,
  User,
  Building2,
  Link2
} from "lucide-react";

interface CaseQueueRowProps {
  module: "A" | "B" | "C";
  item: any;
  onClick: () => void;
}

export default function CaseQueueRow({ module, item, onClick }: CaseQueueRowProps) {
  // Status Badge Styling
  const getStatusBadge = (status: string) => {
    switch (status?.toLowerCase()) {
      case "recovered":
      case "paid":
        return (
          <Badge className="border-emerald-500/30 bg-emerald-500/15 text-emerald-300 font-semibold gap-1 px-3 py-0.5 rounded-full text-xs">
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
            {status}
          </Badge>
        );
      case "partially_paid":
        return (
          <Badge className="border-amber-500/30 bg-amber-500/15 text-amber-300 font-semibold gap-1 px-3 py-0.5 rounded-full text-xs">
            <Clock className="h-3.5 w-3.5 text-amber-400" />
            partially paid
          </Badge>
        );
      case "disputed":
        return (
          <Badge className="border-rose-500/30 bg-rose-500/15 text-rose-300 font-semibold gap-1 px-3 py-0.5 rounded-full text-xs">
            <ShieldAlert className="h-3.5 w-3.5 text-rose-400" />
            dispute halted
          </Badge>
        );
      case "pending_human_approval":
        return (
          <Badge className="border-amber-500/30 bg-amber-500/15 text-amber-300 font-semibold gap-1 px-3 py-0.5 rounded-full text-xs">
            <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />
            approval required
          </Badge>
        );
      case "closed_unrecovered":
      case "written_off":
      case "skipped_low_value":
      case "expired_unrecovered":
        return (
          <Badge variant="outline" className="border-rose-500/30 bg-rose-950/30 text-rose-400 font-medium gap-1 px-3 py-0.5 rounded-full text-xs">
            <XCircle className="h-3.5 w-3.5 text-rose-400" />
            {status.replace(/_/g, " ")}
          </Badge>
        );
      case "retried":
      case "nudged":
      case "overdue":
        return (
          <Badge variant="outline" className="border-blue-500/30 bg-blue-500/10 text-blue-300 font-semibold px-3 py-0.5 rounded-full text-xs">
            {status}
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" className="border-slate-700 bg-slate-800 text-slate-300 font-medium px-3 py-0.5 rounded-full text-xs">
            {status}
          </Badge>
        );
    }
  };

  // 5-Rung Visual Stepper
  const renderRungStepper = (currentRung: number) => {
    return (
      <div className="flex items-center gap-1.5">
        {[0, 1, 2, 3, 4].map((rung) => (
          <div
            key={rung}
            className={`flex h-6 w-6 items-center justify-center rounded-md text-xs font-mono font-bold transition-all ${
              rung === currentRung
                ? rung === 4
                  ? "bg-rose-600 text-white shadow-md shadow-rose-600/30 ring-2 ring-rose-400/50"
                  : "bg-blue-600 text-white shadow-md shadow-blue-600/30 ring-2 ring-blue-400/50"
                : rung < currentRung
                ? "bg-slate-800 text-slate-300 font-medium border border-slate-700"
                : "bg-slate-900 text-slate-600 font-normal border border-slate-800"
            }`}
          >
            {rung}
          </div>
        ))}
      </div>
    );
  };

  // Module A: Method Icon Styling
  const renderMethodBadgeA = (method: string) => {
    const m = (method || "PAY").toLowerCase();
    if (m.includes("upi")) {
      return (
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-indigo-500/15 text-indigo-300 border border-indigo-500/30 shadow-inner font-mono font-bold text-xs">
          UPI
        </div>
      );
    }
    if (m.includes("card")) {
      return (
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-500/15 text-blue-300 border border-blue-500/30 shadow-inner font-mono font-bold text-xs">
          CARD
        </div>
      );
    }
    if (m.includes("net")) {
      return (
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 shadow-inner font-mono font-bold text-xs">
          NET
        </div>
      );
    }
    return (
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-amber-500/15 text-amber-300 border border-amber-500/30 shadow-inner font-mono font-bold text-xs">
        {m.toUpperCase().slice(0, 3)}
      </div>
    );
  };

  // Module A: Root Cause Taxonomy Badge
  const renderTaxonomyBadgeA = (item: any) => {
    const raw = (item.classified_root_cause || item.failure_code || "transient_glitch").toLowerCase();
    if (raw === "u19" || raw.includes("npci")) {
      return (
        <span className="inline-flex items-center gap-1.5 font-mono text-xs font-semibold text-purple-300 bg-purple-500/10 border border-purple-500/30 px-2.5 py-0.5 rounded-lg shadow-xs">
          U19 • NPCI Window Block
        </span>
      );
    }
    if (raw === "91" || raw.includes("glitch") || raw.includes("timeout") || raw.includes("downtime")) {
      return (
        <span className="inline-flex items-center gap-1.5 font-mono text-xs font-semibold text-violet-300 bg-violet-500/10 border border-violet-500/30 px-2.5 py-0.5 rounded-lg shadow-xs">
          91 • Bank Switch Downtime
        </span>
      );
    }
    if (raw === "51" || raw.includes("insufficient")) {
      return (
        <span className="inline-flex items-center gap-1.5 font-mono text-xs font-semibold text-indigo-300 bg-indigo-500/10 border border-indigo-500/30 px-2.5 py-0.5 rounded-lg shadow-xs">
          51 • Limit Exceeded
        </span>
      );
    }
    if (raw === "54" || raw.includes("expired")) {
      return (
        <span className="inline-flex items-center gap-1.5 font-mono text-xs font-semibold text-rose-300 bg-rose-500/10 border border-rose-500/30 px-2.5 py-0.5 rounded-lg shadow-xs">
          54 • Card Expired
        </span>
      );
    }
    if (raw === "05" || raw.includes("decline")) {
      return (
        <span className="inline-flex items-center gap-1.5 font-mono text-xs font-semibold text-amber-300 bg-amber-500/10 border border-amber-500/30 px-2.5 py-0.5 rounded-lg shadow-xs">
          05 • Issuer Decline
        </span>
      );
    }
    return (
      <span className="inline-flex items-center font-mono text-xs font-semibold text-slate-300 bg-slate-800/80 px-2.5 py-0.5 rounded-lg border border-slate-700/60 shadow-xs">
        {raw}
      </span>
    );
  };

  // Module A: Deterministic / Inferred Attribution
  const getAttributionA = (item: any) => {
    if (item.fault_attribution === "customer_fault") return "customer_fault";
    if (item.fault_attribution === "infrastructure_fault") return "infrastructure_fault";
    const cause = (item.classified_root_cause || item.failure_code || "").toLowerCase();
    if (["u19", "transient_glitch", "91", "96", "timeout", "downtime", "npci", "infra", "gateway"].some(k => cause.includes(k))) {
      return "infrastructure_fault";
    }
    return "customer_fault";
  };

  return (
    <TableRow
      onClick={onClick}
      className="cursor-pointer hover:bg-slate-800/50 transition-colors group border-b border-slate-800/80"
    >
      {/* MODULE A: Payments & Mandates */}
      {module === "A" && (
        <>
          <TableCell className="font-medium py-3.5 pl-6">
            <div className="flex items-center gap-3">
              {renderMethodBadgeA(item.method)}
              <div>
                <span className="font-bold text-slate-100 text-sm block">
                  {item.method?.toUpperCase() || "Payment"}
                </span>
                <span className="text-[11px] text-slate-500 font-mono block">
                  ID: {String(item.id).slice(0, 8)}
                </span>
              </div>
            </div>
          </TableCell>
          <TableCell className="font-mono text-sm sm:text-base font-black tabular-nums text-white py-3.5">
            {formatPaiseToRupees(item.amount_paise)}
          </TableCell>
          <TableCell className="py-3.5">
            {renderTaxonomyBadgeA(item)}
          </TableCell>
          <TableCell className="py-3.5">
            {getAttributionA(item) === "customer_fault" ? (
              <Badge variant="outline" className="border-indigo-500/30 bg-indigo-500/10 text-indigo-300 font-semibold text-xs py-0.5 px-2.5 rounded-full">
                Customer Fault
              </Badge>
            ) : (
              <Badge variant="outline" className="border-emerald-500/30 bg-emerald-500/10 text-emerald-300 font-semibold text-xs py-0.5 px-2.5 rounded-full">
                Infra Fault
              </Badge>
            )}
          </TableCell>
          <TableCell className="py-3.5">
            {item.razorpay_payment_link_id &&
            !item.razorpay_payment_link_id.startsWith("plink_alt_") &&
            !item.razorpay_payment_link_id.startsWith("plink_inv_") &&
            !item.razorpay_payment_link_id.startsWith("plink_nudge_") ? (
              <span className="inline-flex items-center gap-1.5 font-mono text-xs text-emerald-300 font-bold bg-emerald-500/15 px-2.5 py-0.5 rounded-full border border-emerald-500/30">
                <Zap className="h-3 w-3 text-emerald-400" />
                Active Link
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 text-xs text-blue-300 font-medium bg-blue-500/10 px-2.5 py-0.5 rounded-full border border-blue-500/30">
                <Link2 className="h-3 w-3 text-blue-400" />
                Ready to Issue
              </span>
            )}
          </TableCell>
          <TableCell className="py-3.5">
            {getStatusBadge(item.status)}
          </TableCell>
          <TableCell className="text-right py-3.5 pr-6">
            <span className="inline-flex items-center gap-1 text-xs font-bold text-slate-500 group-hover:text-blue-400 transition-all">
              Inspect <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-1" />
            </span>
          </TableCell>
        </>
      )}

      {/* MODULE B: B2B Invoices */}
      {module === "B" && (
        <>
          <TableCell className="font-mono text-xs sm:text-sm font-bold text-slate-200 py-3.5 pl-6">
            <span className="bg-slate-800/80 px-2.5 py-1 rounded-md border border-slate-700/60">
              {item.invoice_number}
            </span>
          </TableCell>
          <TableCell className="py-3.5">
            <div className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
                <Building2 className="h-4.5 w-4.5" />
              </div>
              <div>
                <div className="font-bold text-slate-100 text-sm">{item.buyer_name}</div>
                <div className="flex items-center gap-2 mt-1">
                  {item.supplier_is_msme && (
                    <span className="text-[10px] font-bold text-amber-300 bg-amber-500/15 border border-amber-500/30 px-2 py-0.5 rounded-md">
                      MSME Sec 16
                    </span>
                  )}
                  {item.dispute_flag && (
                    <span className="text-[10px] font-bold text-rose-300 bg-rose-500/15 border border-rose-500/30 px-2 py-0.5 rounded-md">
                      Dispute Halted
                    </span>
                  )}
                </div>
              </div>
            </div>
          </TableCell>
          <TableCell className="font-mono tabular-nums py-3.5">
            <span className="font-black text-white text-base block">
              {formatPaiseToRupees(item.amount_paise)}
            </span>
            {item.amount_paid_paise > 0 && item.amount_paid_paise < item.amount_paise && (
              <div className="text-xs text-emerald-400 font-mono font-bold mt-0.5">
                Paid: {formatPaiseToRupees(item.amount_paid_paise)}
              </div>
            )}
            {item.supplier_is_msme && item.status === "overdue" && (
              <div className="text-xs text-amber-400 font-bold font-mono mt-0.5">
                +{formatPaiseToRupees(item.computed_interest_paise || Math.round(item.amount_paise * 0.0506))} interest
              </div>
            )}
          </TableCell>
          <TableCell className="py-3.5">
            {renderRungStepper(item.current_rung || 0)}
          </TableCell>
          <TableCell className="py-3.5">
            {getStatusBadge(item.status)}
          </TableCell>
          <TableCell className="text-right py-3.5 pr-6">
            <span className="inline-flex items-center gap-1 text-xs font-bold text-slate-500 group-hover:text-blue-400 transition-all">
              Inspect <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-1" />
            </span>
          </TableCell>
        </>
      )}

      {/* MODULE C: Abandoned Orders */}
      {module === "C" && (
        <>
          <TableCell className="py-3.5 pl-6">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-500/10 text-blue-400 font-bold text-xs border border-blue-500/20">
                <User className="h-4.5 w-4.5" />
              </div>
              <div>
                <div className="font-bold text-slate-100 text-sm">
                  {item.customer_name || item.customer_email?.split("@")[0] || "Customer"}
                </div>
                <div className="text-[11px] text-slate-500 font-mono mt-0.5">
                  {item.customer_email || item.customer_contact || "No contact info"}
                </div>
              </div>
            </div>
          </TableCell>
          <TableCell className="font-mono text-sm sm:text-base font-black tabular-nums text-white py-3.5">
            {formatPaiseToRupees(item.amount_paise)}
          </TableCell>
          <TableCell className="text-xs text-slate-400 font-medium py-3.5">
            <div className="flex items-center gap-1.5 font-mono">
              <Clock className="h-3.5 w-3.5 text-slate-500 shrink-0" />
              <span>
                {new Date(item.order_created_at).toLocaleDateString()} {new Date(item.order_created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          </TableCell>
          <TableCell className="py-3.5">
            {item.nudge_sent ? (
              <Badge variant="outline" className="border-blue-500/30 bg-blue-500/10 text-blue-300 font-semibold text-xs py-0.5 px-2.5 rounded-full">
                1 Nudge Sent (Capped)
              </Badge>
            ) : item.amount_paise < 20000 ? (
              <Badge variant="outline" className="border-rose-500/30 bg-rose-500/10 text-rose-300 font-semibold text-xs py-0.5 px-2.5 rounded-full">
                Floor Skipped (&lt; ₹200)
              </Badge>
            ) : (
              <span className="text-xs text-slate-500 font-medium bg-slate-800/80 px-2.5 py-0.5 rounded-md border border-slate-700/50">
                Pending check
              </span>
            )}
          </TableCell>
          <TableCell className="py-3.5">
            {getStatusBadge(item.status)}
          </TableCell>
          <TableCell className="text-right py-3.5 pr-6">
            <span className="inline-flex items-center gap-1 text-xs font-bold text-slate-500 group-hover:text-blue-400 transition-all">
              Inspect <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-1" />
            </span>
          </TableCell>
        </>
      )}
    </TableRow>
  );
}