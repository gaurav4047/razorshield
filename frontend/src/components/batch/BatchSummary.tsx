import { useBatchSummary } from "@/api/useBatchSummary";
import { formatPaiseToRupees } from "@/lib/utils";

interface BatchSummaryProps {
  batchId: string | null;
}

export default function BatchSummary({ batchId }: BatchSummaryProps) {
  const { data: summary, isLoading } = useBatchSummary(batchId);

  if (isLoading || !summary) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="h-24 animate-pulse rounded-lg bg-slate-200" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
      <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Total at Risk</p>
        <p className="mt-1 text-2xl font-bold text-slate-900">{formatPaiseToRupees(summary.total_at_risk_paise)}</p>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Gross Recovered</p>
        <p className="mt-1 text-2xl font-bold text-emerald-600">{formatPaiseToRupees(summary.gross_recovered_paise)}</p>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Net Recovered (after fee/GST)</p>
        <p className="mt-1 text-2xl font-bold text-emerald-700">{formatPaiseToRupees(summary.net_recovered_paise)}</p>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Recovery Rate</p>
        <p className="mt-1 text-2xl font-bold text-blue-600">{summary.recovery_rate_pct.toFixed(1)}%</p>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Unrecovered Exceptions</p>
        <p className="mt-1 text-2xl font-bold text-rose-600">{summary.exception_count}</p>
      </div>
    </div>
  );
}
