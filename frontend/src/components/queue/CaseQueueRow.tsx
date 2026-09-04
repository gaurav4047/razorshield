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
  // Method Pill Styling
  const getMethodBadge = (method: string) => {
    switch (method?.toLowerCase()) {
      case "upi":
        return <Badge variant="outline" className="border-indigo-200 bg-indigo-50/70 text-indigo-700 font-bold uppercase px-2.5 py-0.5 text-xs">UPI</Badge>;
      case "card":
        return <Badge variant="outline" className="border-blue-200 bg-blue-50/70 text-blue-700 font-bold uppercase px-2.5 py-0.5 text-xs">Card</Badge>;
      case "netbanking":
        return <Badge variant="outline" className="border-purple-200 bg-purple-50/70 text-purple-700 font-bold uppercase px-2.5 py-0.5 text-xs">Netbanking</Badge>;
      case "wallet":
        return <Badge variant="outline" className="border-amber-200 bg-amber-50/70 text-amber-800 font-bold uppercase px-2.5 py-0.5 text-xs">Wallet</Badge>;
      case "emi":
        return <Badge variant="outline" className="border-teal-200 bg-teal-50/70 text-teal-800 font-bold uppercase px-2.5 py-0.5 text-xs">EMI</Badge>;
      default:
        return <Badge variant="outline" className="text-slate-600 uppercase px-2.5 py-0.5 text-xs">{method || "Unknown"}</Badge>;
    }
  };

  // Status Badge Styling
  const getStatusBadge = (status: string) => {
    switch (status?.toLowerCase()) {
      case "recovered":
      case "paid":
        return (
          <Badge className="border-emerald-200 bg-emerald-100 text-emerald-800 font-bold gap-1 px-3 py-1 rounded-full text-xs shadow-2xs">
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
            {status}
          </Badge>
        );
      case "partially_paid":
        return (
          <Badge className="border-amber-200 bg-amber-100 text-amber-900 font-bold gap-1 px-3 py-1 rounded-full text-xs shadow-2xs">
            <Clock className="h-3.5 w-3.5 text-amber-600" />
            partially paid
          </Badge>
        );
      case "disputed":
        return (
          <Badge className="border-rose-200 bg-rose-100 text-rose-800 font-bold gap-1 px-3 py-1 rounded-full text-xs shadow-2xs">
            <ShieldAlert className="h-3.5 w-3.5 text-rose-600" />
            dispute halted
          </Badge>
        );
      case "pending_human_approval":
        return (
          <Badge className="border-amber-300 bg-amber-100 text-amber-900 font-bold gap-1 px-3 py-1 rounded-full text-xs shadow-2xs">
            <AlertTriangle className="h-3.5 w-3.5 text-amber-700" />
            approval required
          </Badge>
        );
      case "closed_unrecovered":
      case "written_off":
      case "skipped_low_value":
      case "expired_unrecovered":
        return (
          <Badge variant="outline" className="border-rose-200 bg-rose-50 text-rose-700 font-bold gap-1 px-3 py-1 rounded-full text-xs">
            <XCircle className="h-3.5 w-3.5 text-rose-500" />
            {status.replace(/_/g, " ")}
          </Badge>
        );
      case "retried":
      case "nudged":
      case "overdue":
        return (
          <Badge variant="outline" className="border-blue-200 bg-blue-50 text-[#0066ff] font-bold px-3 py-1 rounded-full text-xs">
            {status}
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" className="border-slate-200 bg-slate-50 text-slate-700 font-medium px-3 py-1 rounded-full text-xs">
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
            className={`flex h-6 w-6 items-center justify-center rounded-lg text-xs font-bold transition-all ${
              rung === currentRung
                ? rung === 4
                  ? "bg-rose-600 text-white shadow-sm ring-2 ring-rose-300"
                  : "bg-blue-600 text-white shadow-sm ring-2 ring-blue-200"
                : rung < currentRung
                ? "bg-slate-200 text-slate-700 font-semibold"
                : "bg-slate-100 text-slate-400 font-normal"
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
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-700 border border-indigo-200/80 shadow-2xs font-mono font-black text-xs">
          UPI
        </div>
      );
    }
    if (m.includes("card")) {
      return (
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-[#0066ff] border border-blue-200/80 shadow-2xs font-mono font-black text-xs">
          CARD
        </div>
      );
    }
    if (m.includes("net")) {
      return (
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-700 border border-emerald-200/80 shadow-2xs font-mono font-black text-xs">
          NET
        </div>
      );
    }
    return (
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-amber-50 text-amber-700 border border-amber-200/80 shadow-2xs font-mono font-black text-xs">
        {m.toUpperCase().slice(0, 3)}
      </div>
    );
  };

  // Module A: Root Cause Taxonomy Badge
  const renderTaxonomyBadgeA = (item: any) => {
    const raw = (item.classified_root_cause || item.failure_code || "transient_glitch").toLowerCase();
    if (raw === "u19" || raw.includes("npci")) {
      return (
        <span className="inline-flex items-center gap-1.5 font-mono text-xs font-bold text-purple-900 bg-purple-50 border border-purple-200/80 px-2.5 py-1 rounded-xl shadow-2xs">
          U19 • NPCI Window Block
        </span>
      );
    }
    if (raw === "91" || raw.includes("glitch") || raw.includes("timeout") || raw.includes("downtime")) {
      return (
        <span className="inline-flex items-center gap-1.5 font-mono text-xs font-bold text-violet-900 bg-violet-50 border border-violet-200/80 px-2.5 py-1 rounded-xl shadow-2xs">
          91 • Bank Switch Downtime
        </span>
      );
    }
    if (raw === "51" || raw.includes("insufficient")) {
      return (
        <span className="inline-flex items-center gap-1.5 font-mono text-xs font-bold text-indigo-900 bg-indigo-50 border border-indigo-200/80 px-2.5 py-1 rounded-xl shadow-2xs">
          51 • Limit Exceeded
        </span>
      );
    }
    if (raw === "54" || raw.includes("expired")) {
      return (
        <span className="inline-flex items-center gap-1.5 font-mono text-xs font-bold text-rose-900 bg-rose-50 border border-rose-200/80 px-2.5 py-1 rounded-xl shadow-2xs">
          54 • Card Expired
        </span>
      );
    }
    if (raw === "05" || raw.includes("decline")) {
      return (
        <span className="inline-flex items-center gap-1.5 font-mono text-xs font-bold text-amber-900 bg-amber-50 border border-amber-200/80 px-2.5 py-1 rounded-xl shadow-2xs">
          05 • Issuer Decline
        </span>
      );
    }
    return (
      <span className="inline-flex items-center font-mono text-xs font-bold text-slate-700 bg-slate-100/90 px-2.5 py-1 rounded-xl border border-slate-200/80 shadow-2xs">
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
      className="cursor-pointer hover:bg-blue-50/50 transition-colors group border-b border-slate-100/90"
    >
      {/* MODULE A: Payments & Mandates */}
      {module === "A" && (
        <>
          <TableCell className="font-medium py-4.5 pl-6">
            <div className="flex items-center gap-3">
              {renderMethodBadgeA(item.method)}
              <div>
                <span className="font-extrabold text-[#0c2340] text-sm block">
                  {item.method?.toUpperCase() || "Payment"}
                </span>
                <span className="text-[11px] text-slate-400 font-mono block">
                  ID: {String(item.id).slice(0, 8)}
                </span>
              </div>
            </div>
          </TableCell>
          <TableCell className="font-mono text-base font-black tabular-nums text-[#0c2340] py-4.5">
            {formatPaiseToRupees(item.amount_paise)}
          </TableCell>
          <TableCell className="py-4.5">
            {renderTaxonomyBadgeA(item)}
          </TableCell>
          <TableCell className="py-4.5">
            {getAttributionA(item) === "customer_fault" ? (
              <Badge variant="outline" className="border-indigo-200 bg-indigo-50 text-indigo-700 font-extrabold text-xs py-1 px-3 rounded-full shadow-2xs">
                Customer Fault
              </Badge>
            ) : (
              <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700 font-extrabold text-xs py-1 px-3 rounded-full shadow-2xs">
                Infra Fault
              </Badge>
            )}
          </TableCell>
          <TableCell className="py-4.5">
            {item.razorpay_payment_link_id &&
            !item.razorpay_payment_link_id.startsWith("plink_alt_") &&
            !item.razorpay_payment_link_id.startsWith("plink_inv_") &&
            !item.razorpay_payment_link_id.startsWith("plink_nudge_") ? (
              <span className="inline-flex items-center gap-1.5 font-mono text-xs text-emerald-700 font-extrabold bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200 shadow-2xs">
                <Zap className="h-3.5 w-3.5 text-emerald-600" />
                Active Link
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 text-xs text-[#0066ff] font-bold bg-blue-50 px-3 py-1 rounded-full border border-blue-200/80 shadow-2xs">
                <Link2 className="h-3 w-3 text-[#0066ff]" />
                Ready to Issue
              </span>
            )}
          </TableCell>
          <TableCell className="py-4.5">
            {getStatusBadge(item.status)}
          </TableCell>
          <TableCell className="text-right py-4.5 pr-6">
            <span className="inline-flex items-center gap-1 text-xs font-extrabold text-slate-400 group-hover:text-[#0066ff] transition-all">
              Inspect <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-1" />
            </span>
          </TableCell>
        </>
      )}

      {/* MODULE B: B2B Invoices */}
      {module === "B" && (
        <>
          <TableCell className="font-mono text-xs sm:text-sm font-extrabold text-[#0c2340] py-4.5 pl-6">
            <span className="bg-slate-100 px-2.5 py-1 rounded-lg border border-slate-200/80">
              {item.invoice_number}
            </span>
          </TableCell>
          <TableCell className="py-4.5">
            <div className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-amber-50 text-amber-800 border border-amber-200/60 shadow-2xs">
                <Building2 className="h-4.5 w-4.5" />
              </div>
              <div>
                <div className="font-extrabold text-slate-900 text-sm sm:text-base">{item.buyer_name}</div>
                <div className="flex items-center gap-2 mt-1">
                  {item.supplier_is_msme && (
                    <span className="text-[11px] font-extrabold text-amber-900 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-md">
                      MSME Sec 16
                    </span>
                  )}
                  {item.dispute_flag && (
                    <span className="text-[11px] font-extrabold text-rose-800 bg-rose-50 border border-rose-200 px-2 py-0.5 rounded-md">
                      Dispute Halted
                    </span>
                  )}
                </div>
              </div>
            </div>
          </TableCell>
          <TableCell className="font-mono tabular-nums py-4.5">
            <span className="font-black text-[#0c2340] text-base block">
              {formatPaiseToRupees(item.amount_paise)}
            </span>
            {item.amount_paid_paise > 0 && item.amount_paid_paise < item.amount_paise && (
              <div className="text-xs text-emerald-700 font-mono font-bold mt-0.5">
                Paid: {formatPaiseToRupees(item.amount_paid_paise)}
              </div>
            )}
            {item.supplier_is_msme && item.status === "overdue" && (
              <div className="text-xs text-amber-700 font-bold font-mono mt-0.5">
                +{formatPaiseToRupees(item.computed_interest_paise || Math.round(item.amount_paise * 0.0506))} interest
              </div>
            )}
          </TableCell>
          <TableCell className="py-4.5">
            {renderRungStepper(item.current_rung || 0)}
          </TableCell>
          <TableCell className="py-4.5">
            {getStatusBadge(item.status)}
          </TableCell>
          <TableCell className="text-right py-4.5 pr-6">
            <span className="inline-flex items-center gap-1 text-xs font-extrabold text-slate-400 group-hover:text-[#0066ff] transition-all">
              Inspect <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-1" />
            </span>
          </TableCell>
        </>
      )}

      {/* MODULE C: Abandoned Orders */}
      {module === "C" && (
        <>
          <TableCell className="py-4.5 pl-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-[#0066ff] font-extrabold text-sm border border-blue-200/60 shadow-2xs">
                <User className="h-5 w-5" />
              </div>
              <div>
                <div className="font-extrabold text-slate-900 text-sm sm:text-base">
                  {item.customer_name || item.customer_email?.split("@")[0] || "Customer"}
                </div>
                <div className="text-xs text-slate-500 font-mono mt-0.5">
                  {item.customer_email || item.customer_contact || "No contact info"}
                </div>
              </div>
            </div>
          </TableCell>
          <TableCell className="font-mono text-base font-black tabular-nums text-[#0c2340] py-4.5">
            {formatPaiseToRupees(item.amount_paise)}
          </TableCell>
          <TableCell className="text-xs sm:text-sm text-slate-600 font-medium py-4.5">
            <div className="flex items-center gap-1.5 font-mono">
              <Clock className="h-3.5 w-3.5 text-slate-400 shrink-0" />
              <span>
                {new Date(item.order_created_at).toLocaleDateString()} {new Date(item.order_created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          </TableCell>
          <TableCell className="py-4.5">
            {item.nudge_sent ? (
              <Badge variant="outline" className="border-blue-200 bg-blue-50 text-[#0066ff] font-bold text-xs py-1 px-3 rounded-full">
                1 Nudge Sent (Capped)
              </Badge>
            ) : item.amount_paise < 20000 ? (
              <Badge variant="outline" className="border-rose-200 bg-rose-50 text-rose-700 font-bold text-xs py-1 px-3 rounded-full">
                Floor Skipped (&lt; ₹200)
              </Badge>
            ) : (
              <span className="text-xs text-slate-400 font-medium bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-100">
                Pending check
              </span>
            )}
          </TableCell>
          <TableCell className="py-4.5">
            {getStatusBadge(item.status)}
          </TableCell>
          <TableCell className="text-right py-4.5 pr-6">
            <span className="inline-flex items-center gap-1 text-xs font-extrabold text-slate-400 group-hover:text-[#0066ff] transition-all">
              Inspect <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-1" />
            </span>
          </TableCell>
        </>
      )}
    </TableRow>
  );
}