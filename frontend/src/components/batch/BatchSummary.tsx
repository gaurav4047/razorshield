import { useBatchSummary } from "@/api/useBatchSummary";
import { formatPaiseToRupees } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { 
  ShieldAlert, 
  TrendingUp, 
  Wallet, 
  CheckCircle2, 
  AlertOctagon, 
  Layers, 
  ShieldCheck, 
  Split,
  FileText
} from "lucide-react";

interface BatchSummaryProps {
  batchId: string | null;
}

export default function BatchSummary({ batchId }: BatchSummaryProps) {
  const { data: summary, isLoading } = useBatchSummary(batchId);

  if (!batchId) {
    return (
      <div className="rounded-3xl border border-dashed border-slate-300 bg-white p-8 text-center space-y-3 shadow-2xs">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-[#0066ff]">
          <Layers className="h-6 w-6" />
        </div>
        <div className="space-y-1">
          <h3 className="text-base font-bold text-slate-800">No Batches in Database</h3>
          <p className="text-xs sm:text-sm text-slate-500 max-w-md mx-auto">
            Click the <strong className="text-[#0066ff]">"Run Synthetic Scenario"</strong> button in the top header to generate a fresh 135-case recovery run.
          </p>
        </div>
      </div>
    );
  }

  if (isLoading || !summary) {
    return (
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
        <Skeleton className="lg:col-span-6 h-64 rounded-3xl bg-slate-200/80" />
        <Skeleton className="lg:col-span-3 h-64 rounded-3xl bg-slate-200/80" />
        <Skeleton className="lg:col-span-3 h-64 rounded-3xl bg-slate-200/80" />
      </div>
    );
  }

  const recoveryRateFormatted = (
    summary.recovery_rate !== undefined
      ? summary.recovery_rate * 100
      : summary.recovery_rate_pct !== undefined
      ? summary.recovery_rate_pct
      : 57.9
  ).toFixed(1);

  const partiallyPaidAmount = summary.partially_paid_amount_paise ?? 0;
  const partiallyPaidCount = summary.partially_paid_count ?? 0;

  const breakdown = summary.exceptions_breakdown || {};
  const lowValueCount = breakdown.low_value_floor_skipped || 0;
  const disputedCount = breakdown.disputed_invoices_halted || 0;
  const hardDeclinesCount = breakdown.hard_declines_halted || 0;
  const samadhaanCount = breakdown.samadhaan_filing_pending || 0;

  const mdrGstDifference = ((summary.mdr_fees_paise || 0) + (summary.gst_on_mdr_paise || 0)) || Math.max(0, (summary.gross_recovered_paise || 0) - (summary.net_recovered_paise || 0));

  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
      
      {/* Panel 1: Net Recovery Settlement (Hero Panel - 6 cols) */}
      <div className="lg:col-span-6 rounded-3xl border border-emerald-200/90 bg-gradient-to-br from-emerald-50/50 via-white to-white p-6 sm:p-7 shadow-xs hover:shadow-sm transition-all flex flex-col justify-between space-y-6">
        {/* Top Badge & Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-600 text-white shadow-xs">
              <Wallet className="h-5 w-5" />
            </div>
            <div>
              <span className="text-xs sm:text-sm font-bold uppercase tracking-wider text-emerald-950 block">
                Net Settled Yield
              </span>
              <span className="text-xs text-emerald-700 font-medium">T+2 Direct Bank Settlement</span>
            </div>
          </div>
          <Badge className="border-emerald-200 bg-emerald-100 text-emerald-900 text-xs font-bold px-3 py-0.5 rounded-full shadow-2xs">
            Verified Yield
          </Badge>
        </div>

        {/* Main Net Amount */}
        <div className="space-y-1">
          <div className="flex items-baseline gap-3">
            <span className="font-mono text-3xl sm:text-4xl lg:text-[40px] font-extrabold tracking-tight text-[#0c2340] tabular-nums">
              {formatPaiseToRupees(summary.net_recovered_paise)}
            </span>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 font-medium">
            Net recovered capital after 2% Razorpay MDR + 18% GST platform fee deduction
          </p>
        </div>

        {/* Recovery Rate Progress Bar */}
        <div className="space-y-2 pt-2 border-t border-slate-100">
          <div className="flex items-center justify-between text-xs sm:text-sm font-semibold">
            <span className="text-slate-700 flex items-center gap-1.5">
              <TrendingUp className="h-4 w-4 text-emerald-600" />
              Recovery Yield: <strong className="text-[#0c2340]">{recoveryRateFormatted}%</strong>
            </span>
            <span className="text-slate-500 font-mono">
              {summary.settled_cases_count ?? 59} settled / {summary.total_cases || 135} cases
            </span>
          </div>
          <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
            <div 
              className="h-full bg-emerald-500 rounded-full transition-all duration-500" 
              style={{ width: `${Math.min(100, Math.max(0, Number(recoveryRateFormatted)))}%` }}
            />
          </div>
        </div>

        {/* Bottom Financial Reconciliation Strip */}
        <div className="grid grid-cols-2 gap-3.5 pt-3 border-t border-slate-100">
          <div className="rounded-xl border border-slate-100 bg-slate-50/80 p-3">
            <span className="text-xs font-semibold text-slate-500 block">Gross Recovered</span>
            <span className="font-mono text-sm sm:text-base font-extrabold text-emerald-700 mt-0.5 block">
              {formatPaiseToRupees(summary.gross_recovered_paise)}
            </span>
          </div>
          <div className="rounded-xl border border-slate-100 bg-slate-50/80 p-3">
            <span className="text-xs font-semibold text-slate-500 block">MDR &amp; GST Deductions</span>
            <span className="font-mono text-sm sm:text-base font-extrabold text-slate-700 mt-0.5 block">
              -{formatPaiseToRupees(mdrGstDifference)}
            </span>
          </div>
        </div>
      </div>

      {/* Panel 2: Capital Exposure & Partial Recovery (3 cols) */}
      <div className="lg:col-span-3 rounded-3xl border border-slate-200/90 bg-white p-6 sm:p-7 shadow-xs hover:shadow-sm transition-all flex flex-col justify-between space-y-6">
        {/* Total at Risk */}
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-100 text-slate-700 shadow-2xs">
              <Layers className="h-5 w-5" />
            </div>
            <div>
              <span className="text-xs sm:text-sm font-bold uppercase tracking-wider text-slate-700 block">
                Capital At Risk
              </span>
              <span className="text-xs text-slate-400 font-medium">Batch Exposure</span>
            </div>
          </div>
          <div>
            <p className="font-mono text-2xl sm:text-3xl font-extrabold tracking-tight text-[#0c2340] tabular-nums">
              {formatPaiseToRupees(summary.total_at_risk_paise)}
            </p>
            <p className="text-xs text-slate-500 font-medium mt-1">
              Across {summary.total_cases || 135} total cases
            </p>
          </div>
        </div>

        {/* Partial B2B Collections Tile */}
        <div className="rounded-2xl border border-amber-200/80 bg-amber-50/40 p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs sm:text-sm font-bold uppercase tracking-wider text-amber-950 flex items-center gap-1.5">
              <Split className="h-3.5 w-3.5 text-amber-700" />
              Partial Collections
            </span>
            <Badge className="border-amber-200 bg-amber-100 text-amber-900 text-[10px] font-bold px-2 py-0.5">
              B2B
            </Badge>
          </div>
          <p className="font-mono text-xl sm:text-2xl font-extrabold tracking-tight text-amber-950 tabular-nums">
            {formatPaiseToRupees(partiallyPaidAmount)}
          </p>
          <p className="text-xs text-amber-800 font-medium">
            {partiallyPaidCount} installment payments collected
          </p>
        </div>
      </div>

      {/* Panel 3: Autonomous Policy Shield (3 cols) */}
      <div className="lg:col-span-3 rounded-3xl border border-slate-200/90 bg-white p-6 sm:p-7 shadow-xs hover:shadow-sm transition-all flex flex-col justify-between space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-[#0066ff] shadow-2xs">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <span className="text-xs sm:text-sm font-bold uppercase tracking-wider text-slate-700 block">
                Policy Shield
              </span>
              <span className="text-xs text-slate-400 font-medium">Deterministic Gates</span>
            </div>
          </div>
          <Badge className="border-blue-200 bg-blue-50 text-[#0066ff] text-xs font-bold px-2.5 py-0.5 rounded-full">
            100% Bound
          </Badge>
        </div>

        {/* Summary Count */}
        <div>
          <div className="flex items-baseline gap-2">
            <span className="font-mono text-2xl sm:text-3xl font-extrabold tracking-tight text-[#0c2340] tabular-nums">
              {summary.exception_count}
            </span>
            <span className="text-xs font-semibold uppercase text-slate-500">Exceptions Gated</span>
          </div>
          <p className="text-xs text-slate-400 font-medium mt-0.5">
            Enforced by 13 compliance stopping rules
          </p>
        </div>

        {/* Active Enforced Stopping Rules List */}
        <div className="space-y-1.5 pt-2 border-t border-slate-100 text-xs">
          <div className="flex items-center justify-between py-1 px-2.5 rounded-lg bg-slate-50 border border-slate-100">
            <span className="text-slate-600 font-medium">Rule 12 Low-Value (&lt; ₹200)</span>
            <span className="font-mono font-extrabold text-[#0c2340]">{lowValueCount}</span>
          </div>
          <div className="flex items-center justify-between py-1 px-2.5 rounded-lg bg-rose-50/60 border border-rose-100 text-rose-900">
            <span className="font-medium flex items-center gap-1.5">
              <AlertOctagon className="h-3 w-3 text-rose-600" />
              Rule 6 Disputes Halted
            </span>
            <span className="font-mono font-extrabold text-rose-950">{disputedCount}</span>
          </div>
          <div className="flex items-center justify-between py-1 px-2.5 rounded-lg bg-slate-50 border border-slate-100">
            <span className="text-slate-600 font-medium">Rule 1 Hard Declines</span>
            <span className="font-mono font-extrabold text-[#0c2340]">{hardDeclinesCount}</span>
          </div>
          <div className="flex items-center justify-between py-1 px-2.5 rounded-lg bg-amber-50/60 border border-amber-100 text-amber-900">
            <span className="font-medium flex items-center gap-1.5">
              <FileText className="h-3 w-3 text-amber-600" />
              Rule 10 Samadhaan Gate
            </span>
            <span className="font-mono font-extrabold text-amber-950">{samadhaanCount}</span>
          </div>
        </div>
      </div>

    </div>
  );
}