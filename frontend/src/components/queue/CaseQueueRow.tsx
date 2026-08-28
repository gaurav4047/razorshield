import { formatPaiseToRupees } from "@/lib/utils";

interface CaseQueueRowProps {
  module: "A" | "B" | "C";
  item: any;
  onClick: () => void;
}

export default function CaseQueueRow({ module, item, onClick }: CaseQueueRowProps) {
  return (
    <tr
      onClick={onClick}
      className="cursor-pointer hover:bg-slate-50 transition-colors"
    >
      {module === "A" && (
        <>
          <td className="px-4 py-3 font-medium uppercase text-slate-900">{item.method}</td>
          <td className="px-4 py-3 font-semibold text-slate-900">{formatPaiseToRupees(item.amount_paise)}</td>
          <td className="px-4 py-3 font-mono text-xs text-slate-600">{item.classified_root_cause || "pending diagnosis"}</td>
          <td className="px-4 py-3">
            <span
              className={`inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ${
                item.fault_attribution === "customer_fault"
                  ? "bg-amber-100 text-amber-800"
                  : item.fault_attribution === "infrastructure_fault"
                  ? "bg-blue-100 text-blue-800"
                  : "bg-slate-100 text-slate-600"
              }`}
            >
              {item.fault_attribution}
            </span>
          </td>
          <td className="px-4 py-3">
            <span className="inline-flex rounded bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
              {item.status}
            </span>
          </td>
        </>
      )}

      {module === "B" && (
        <>
          <td className="px-4 py-3 font-mono text-xs font-bold text-slate-900">{item.invoice_number}</td>
          <td className="px-4 py-3 font-medium text-slate-800">{item.buyer_name}</td>
          <td className="px-4 py-3 font-semibold text-slate-900">{formatPaiseToRupees(item.amount_paise)}</td>
          <td className="px-4 py-3">
            <span className="inline-flex items-center gap-1 rounded bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-700">
              Rung {item.current_rung} / 4
            </span>
          </td>
          <td className="px-4 py-3">
            <span className="inline-flex rounded bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
              {item.status}
            </span>
          </td>
        </>
      )}

      {module === "C" && (
        <>
          <td className="px-4 py-3 font-medium text-slate-800">{item.customer_name}</td>
          <td className="px-4 py-3 font-semibold text-slate-900">{formatPaiseToRupees(item.amount_paise)}</td>
          <td className="px-4 py-3 text-xs text-slate-500">{new Date(item.order_created_at).toLocaleTimeString()}</td>
          <td className="px-4 py-3">
            <span className="inline-flex rounded bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
              {item.status}
            </span>
          </td>
        </>
      )}
    </tr>
  );
}
