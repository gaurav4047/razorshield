import { formatPaiseToRupees } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { TableRow, TableCell } from "@/components/ui/table";
import { 
  Zap, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  ShieldAlert
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
        return <Badge variant="outline" className="border-indigo-200 bg-indigo-50/60 text-indigo-700 font-semibold uppercase">UPI</Badge>;
      case "card":
        return <Badge variant="outline" className="border-blue-200 bg-blue-50/60 text-blue-700 font-semibold uppercase">Card</Badge>;
      case "netbanking":
        return <Badge variant="outline" className="border-purple-200 bg-purple-50/60 text-purple-700 font-semibold uppercase">Netbanking</Badge>;
      case "wallet":
        return <Badge variant="outline" className="border-amber-200 bg-amber-50/60 text-amber-700 font-semibold uppercase">Wallet</Badge>;
      case "emi":
        return <Badge variant="outline" className="border-teal-200 bg-teal-50/60 text-teal-700 font-semibold uppercase">EMI</Badge>;
      default:
        return <Badge variant="outline" className="text-slate-600 uppercase">{method || "Unknown"}</Badge>;
    }
  };

  // Status Badge Styling
  const getStatusBadge = (status: string) => {
    switch (status?.toLowerCase()) {
      case "recovered":
      case "paid":
        return (
          <Badge className="border-emerald-200 bg-emerald-100 text-emerald-800 font-semibold gap-1">
            <CheckCircle2 className="h-3 w-3 text-emerald-600" />
            {status}
          </Badge>
        );
      case "partially_paid":
        return (
          <Badge className="border-amber-200 bg-amber-100 text-amber-800 font-semibold gap-1">
            <Clock className="h-3 w-3 text-amber-600" />
            partially paid
          </Badge>
        );
      case "disputed":
        return (
          <Badge className="border-rose-200 bg-rose-100 text-rose-800 font-semibold gap-1">
            <ShieldAlert className="h-3 w-3 text-rose-600" />
            dispute halted
          </Badge>
        );
      case "pending_human_approval":
        return (
          <Badge className="border-amber-300 bg-amber-100 text-amber-900 font-semibold gap-1">
            <AlertTriangle className="h-3 w-3 text-amber-700" />
            approval required
          </Badge>
        );
      case "closed_unrecovered":
      case "written_off":
      case "skipped_low_value":
        return (
          <Badge variant="outline" className="border-rose-200 bg-rose-50 text-rose-700 font-medium gap-1">
            <XCircle className="h-3 w-3 text-rose-500" />
            {status.replace("_", " ")}
          </Badge>
        );
      case "retried":
      case "nudged":
      case "overdue":
        return (
          <Badge variant="outline" className="border-blue-200 bg-blue-50 text-blue-700 font-medium">
            {status}
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" className="border-slate-200 bg-slate-50 text-slate-600 font-medium">
            {status}
          </Badge>
        );
    }
  };

  // 5-Rung Visual Stepper
  const renderRungStepper = (currentRung: number) => {
    return (
      <div className="flex items-center gap-1">
        {[0, 1, 2, 3, 4].map((rung) => (
          <div
            key={rung}
            className={`flex h-5 w-5 items-center justify-center rounded text-[10px] font-bold transition-all ${
              rung === currentRung
                ? rung === 4
                  ? "bg-rose-600 text-white ring-2 ring-rose-300"
                  : "bg-blue-600 text-white ring-2 ring-blue-200"
                : rung < currentRung
                ? "bg-slate-300 text-slate-700 font-medium"
                : "bg-slate-100 text-slate-400"
            }`}
          >
            {rung}
          </div>
        ))}
      </div>
    );
  };

  return (
    <TableRow
      onClick={onClick}
      className="cursor-pointer hover:bg-slate-50/80 transition-colors group"
    >
      {/* MODULE A: Payments & Mandates */}
      {module === "A" && (
        <>
          <TableCell className="font-medium">
            {getMethodBadge(item.method)}
          </TableCell>
          <TableCell className="font-mono font-semibold tabular-nums text-slate-900">
            {formatPaiseToRupees(item.amount_paise)}
          </TableCell>
          <TableCell className="text-xs">
            <span className="font-mono font-medium text-slate-700 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200">
              {item.classified_root_cause || item.failure_code || "transient_glitch"}
            </span>
          </TableCell>
          <TableCell>
            {item.fault_attribution === "customer_fault" ? (
              <Badge variant="outline" className="border-indigo-200 bg-indigo-50/80 text-indigo-700 font-semibold">
                Customer Fault
              </Badge>
            ) : item.fault_attribution === "infrastructure_fault" ? (
              <Badge variant="outline" className="border-emerald-200 bg-emerald-50/80 text-emerald-700 font-semibold">
                Infra Fault
              </Badge>
            ) : (
              <Badge variant="outline" className="text-slate-500">Unknown</Badge>
            )}
          </TableCell>
          <TableCell className="text-xs">
            {item.razorpay_payment_link_id &&
            !item.razorpay_payment_link_id.startsWith("plink_alt_") &&
            !item.razorpay_payment_link_id.startsWith("plink_inv_") &&
            !item.razorpay_payment_link_id.startsWith("plink_nudge_") ? (
              <span className="inline-flex items-center gap-1 font-mono text-[11px] text-emerald-700 font-semibold bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
                <Zap className="h-3 w-3 text-emerald-600" />
                Active Link
              </span>
            ) : (
              <span className="text-slate-400 font-mono text-[11px]">Ready to Generate</span>
            )}
          </TableCell>

          <TableCell className="text-right">
            {getStatusBadge(item.status)}
          </TableCell>
        </>
      )}

      {/* MODULE B: B2B Invoices */}
      {module === "B" && (
        <>
          <TableCell className="font-mono text-xs font-bold text-slate-900">
            {item.invoice_number}
          </TableCell>
          <TableCell>
            <div className="font-medium text-slate-900 text-sm">{item.buyer_name}</div>
            <div className="flex items-center gap-1.5 mt-0.5">
              {item.supplier_is_msme && (
                <span className="text-[10px] font-bold text-amber-700 bg-amber-50 border border-amber-200 px-1 rounded">
                  MSME Act Sec 16
                </span>
              )}
              {item.dispute_flag && (
                <span className="text-[10px] font-bold text-rose-700 bg-rose-50 border border-rose-200 px-1 rounded">
                  Disputed
                </span>
              )}
            </div>
          </TableCell>
          <TableCell className="font-mono tabular-nums">
            <span className="font-semibold text-slate-900 block">
              {formatPaiseToRupees(item.amount_paise)}
            </span>
            {item.amount_paid_paise > 0 && item.amount_paid_paise < item.amount_paise && (
              <div className="text-[10px] text-emerald-600 font-mono">
                Paid: {formatPaiseToRupees(item.amount_paid_paise)}
              </div>
            )}
            {item.supplier_is_msme && item.status === "overdue" && (
              <div className="text-[10px] text-amber-700 font-medium font-mono">
                +{formatPaiseToRupees(item.computed_interest_paise || Math.round(item.amount_paise * 0.0506))} interest
              </div>
            )}
          </TableCell>
          <TableCell>
            {renderRungStepper(item.current_rung || 0)}
          </TableCell>
          <TableCell className="text-right">
            {getStatusBadge(item.status)}
          </TableCell>
        </>
      )}


      {/* MODULE C: Abandoned Orders */}
      {module === "C" && (
        <>
          <TableCell>
            <div className="font-medium text-slate-900 text-sm">{item.customer_name}</div>
            <div className="text-xs text-slate-500">{item.customer_email || item.customer_contact}</div>
          </TableCell>
          <TableCell className="font-mono font-semibold tabular-nums text-slate-900">
            {formatPaiseToRupees(item.amount_paise)}
          </TableCell>
          <TableCell className="text-xs text-slate-500 font-mono">
            {new Date(item.order_created_at).toLocaleDateString()} {new Date(item.order_created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </TableCell>
          <TableCell>
            {item.nudge_sent ? (
              <Badge variant="outline" className="border-blue-200 bg-blue-50 text-blue-700 font-medium">
                1 Nudge Sent (Capped)
              </Badge>
            ) : item.amount_paise < 20000 ? (
              <Badge variant="outline" className="border-rose-200 bg-rose-50 text-rose-700 font-medium">
                Floor Skipped (&lt;₹200)
              </Badge>
            ) : (
              <span className="text-xs text-slate-400">Pending check</span>
            )}
          </TableCell>
          <TableCell className="text-right">
            {getStatusBadge(item.status)}
          </TableCell>
        </>
      )}
    </TableRow>
  );
}

