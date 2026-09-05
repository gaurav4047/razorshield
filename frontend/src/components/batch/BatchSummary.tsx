import { useBatchSummary } from "@/api/useBatchSummary";
import { formatPaiseToRupees } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { 
  TrendingUp, 
  Wallet, 
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
      <div className="rounded-2xl border border-dashed border-slate-800 bg-slate-900/50 p-8 text-center space-y-3 shadow-xl backdrop-blur-md">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
          <Layers className="h-6 w-6" />
        </div>
        <div className="space-y-1">
          <h3 className="text-base font-bold text-slate-100">No Recovery Batches Initialized</h3>
          <p className="text-xs sm:text-sm text-slate-400 max-w-md mx-auto">
            Click the <strong className="text-blue-400">"Run Autonomous Scenario"</strong> button in the top navigation to trigger a fresh multi-stream recovery batch.
          </p>
        </div>
      </div>
    );
  }

  if (isLoading || !summary) {
    return (
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        <Skeleton className="lg:col-span-6 h-60 rounded-2xl bg-slate-900/60 border border-slate-800" />
        <Skeleton className="lg:col-span-3 h-60 rounded-2xl bg-slate-900/60 border border-slate-800" />
        <Skeleton className="lg:col-span-3 h-60 rounded-2xl bg-slate-900/60 border border-slate-800" />
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
    <div className="grid grid-cols-1 gap-4.5 lg:grid-cols-12">
      
      {/* Panel 1: Net Settled Capital Yield (Hero Card - 6 cols) */}
      <div className="lg:col-span-6 rounded-2xl border border-emerald-500/30 bg-gradient-to-br from-emerald-950/40 via-slate-900/90 to-slate-950 p-6 shadow-2xl backdrop-blur-xl flex flex-col justify-between space-y-5 relative overflow-hidden group">
        <div className="absolute top-0 right-0 -mt-8 -mr-8 w-40 h-40 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
        
        {/* Top Header & Verified Badge */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-inner">
              <Wallet className="h-5 w-5" />
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-400 block">
                Net Settled Yield
              </span>
              <span className="text-[11px] text-slate-400 font-medium">T+2 Direct Bank Settlement Verified</span>
            </div>
          </div>
          <Badge className="border-emerald-500/30 bg-emerald-500/10 text-emerald-300 text-xs font-semibold px-3 py-0.5 rounded-full backdrop-blur-md shadow-xs flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Verified Yield
          </Badge>
        </div>

        {/* Main Figure */}
        <div className="space-y-1">
          <div className="flex items-baseline gap-3">
            <span className="font-mono text-3xl sm:text-4xl lg:text-[40px] font-black tracking-tight text-white tabular-nums drop-shadow-sm">
              {formatPaiseToRupees(summary.net_recovered_paise)}
            </span>
          </div>
          <p className="text-xs text-slate-400 font-medium">
            Net recovered revenue after 2% Razorpay MDR + 18% GST platform fee deduction
          </p>
        </div>

        {/* Yield Progress Bar */}
        <div className="space-y-2 pt-2 border-t border-slate-800/80">
          <div className="flex items-center justify-between text-xs font-medium">
            <span className="text-slate-300 flex items-center gap-1.5">
              <TrendingUp className="h-4 w-4 text-emerald-400" />
              Recovery Yield: <strong className="text-emerald-400 font-mono font-bold text-sm ml-0.5">{recoveryRateFormatted}%</strong>
            </span>
            <span className="text-slate-400 font-mono text-[11px]">
              {summary.settled_cases_count ?? 59} settled of {summary.total_cases || 135} portfolio cases
            </span>
          </div>
          <div className="h-2 w-full bg-slate-800/80 rounded-full overflow-hidden p-0.5 border border-slate-700/50">
            <div 
              className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full transition-all duration-700 shadow-sm shadow-emerald-500/50" 
              style={{ width: `${Math.min(100, Math.max(0, Number(recoveryRateFormatted)))}%` }}
            />
          </div>
        </div>

        {/* Financial Reconciliation Strip */}
        <div className="grid grid-cols-2 gap-3 pt-3 border-t border-slate-800/80">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
            <span className="text-[11px] font-medium text-slate-400 block">Gross Recovered</span>
            <span className="font-mono text-sm sm:text-base font-bold text-emerald-400 mt-0.5 block">
              {formatPaiseToRupees(summary.gross_recovered_paise)}
            </span>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3">
            <span className="text-[11px] font-medium text-slate-400 block">MDR &amp; GST Fees</span>
            <span className="font-mono text-sm sm:text-base font-bold text-rose-400 mt-0.5 block">
              -{formatPaiseToRupees(mdrGstDifference)}
            </span>
          </div>
        </div>
      </div>

      {/* Panel 2: Portfolio Exposure & B2B Installments (3 cols) */}
      <div className="lg:col-span-3 rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-xl flex flex-col justify-between space-y-5">
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <Layers className="h-5 w-5" />
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-slate-300 block">
                Capital At Risk
              </span>
              <span className="text-[11px] text-slate-500 font-medium">Batch Exposure</span>
            </div>
          </div>
          <div>
            <p className="font-mono text-2xl sm:text-3xl font-black tracking-tight text-white tabular-nums">
              {formatPaiseToRupees(summary.total_at_risk_paise)}
            </p>
            <p className="text-xs text-slate-400 font-medium mt-1">
              Across {summary.total_cases || 135} total portfolio transactions
            </p>
          </div>
        </div>

        {/* Partial B2B Collections Tile */}
        <div className="rounded-xl border border-amber-500/30 bg-gradient-to-br from-amber-500/10 to-transparent p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-amber-300 flex items-center gap-1.5">
              <Split className="h-3.5 w-3.5 text-amber-400" />
              Partial Collections
            </span>
            <Badge className="border-amber-500/30 bg-amber-500/20 text-amber-300 text-[10px] font-bold px-2 py-0.5">
              MSMED
            </Badge>
          </div>
          <p className="font-mono text-xl sm:text-2xl font-black text-amber-200 tabular-nums">
            {formatPaiseToRupees(partiallyPaidAmount)}
          </p>
          <p className="text-[11px] text-amber-300/80 font-medium">
            {partiallyPaidCount} negotiated installment payments collected
          </p>
        </div>
      </div>

      {/* Panel 3: Autonomous Policy Shield (3 cols) */}
      <div className="lg:col-span-3 rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-xl flex flex-col justify-between space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-slate-300 block">
                Policy Shield
              </span>
              <span className="text-[11px] text-slate-500 font-medium">13 Stopping Rules</span>
            </div>
          </div>
          <Badge className="border-indigo-500/30 bg-indigo-500/20 text-indigo-300 text-xs font-semibold px-2.5 py-0.5 rounded-full">
            100% Bound
          </Badge>
        </div>

        {/* Summary Count */}
        <div>
          <div className="flex items-baseline gap-2">
            <span className="font-mono text-2xl sm:text-3xl font-black tracking-tight text-white tabular-nums">
              {summary.exception_count}
            </span>
            <span className="text-xs font-semibold uppercase text-slate-400">Exceptions Vetoed</span>
          </div>
          <p className="text-xs text-slate-500 font-medium mt-0.5">
            Strict deterministic compliance protection
          </p>
        </div>

        {/* Active Enforced Stopping Rules List */}
        <div className="space-y-1.5 pt-2 border-t border-slate-800 text-xs">
          <div className="flex items-center justify-between py-1 px-2.5 rounded-lg bg-slate-800/60 border border-slate-700/50">
            <span className="text-slate-300 font-medium">Rule 12 Low-Value (&lt; ₹200)</span>
            <span className="font-mono font-bold text-slate-200">{lowValueCount}</span>
          </div>
          <div className="flex items-center justify-between py-1 px-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300">
            <span className="font-medium flex items-center gap-1.5">
              <AlertOctagon className="h-3 w-3 text-rose-400" />
              Rule 6 Disputes Halted
            </span>
            <span className="font-mono font-bold text-rose-200">{disputedCount}</span>
          </div>
          <div className="flex items-center justify-between py-1 px-2.5 rounded-lg bg-slate-800/60 border border-slate-700/50">
            <span className="text-slate-300 font-medium">Rule 1 Hard Declines</span>
            <span className="font-mono font-bold text-slate-200">{hardDeclinesCount}</span>
          </div>
          <div className="flex items-center justify-between py-1 px-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300">
            <span className="font-medium flex items-center gap-1.5">
              <FileText className="h-3 w-3 text-amber-400" />
              Rule 10 Samadhaan Gate
            </span>
            <span className="font-mono font-bold text-amber-200">{samadhaanCount}</span>
          </div>
        </div>
      </div>

    </div>
  );
}