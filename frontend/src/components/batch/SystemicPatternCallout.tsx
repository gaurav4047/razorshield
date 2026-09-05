import { useBatchPattern } from "@/api/useBatchSummary";
import { Badge } from "@/components/ui/badge";
import { Sparkles, Activity, Clock, ArrowRight, ArrowUpRight } from "lucide-react";

interface SystemicPatternCalloutProps {
  batchId?: string | null;
  patternDescription?: string | null;
  affectedCount?: number | null;
  activeModule?: "A" | "B" | "C";
}

export default function SystemicPatternCallout({
  batchId,
  patternDescription: overrideDesc,
  activeModule = "A",
}: SystemicPatternCalloutProps) {
  const { data: patternData, isLoading } = useBatchPattern(batchId || null, activeModule);

  const finding = patternData?.findings?.[0];

  // While loading, render smooth skeleton so banner does not flash or vanish on refresh
  if (isLoading && !finding) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 shadow-xl space-y-4 animate-pulse">
        <div className="flex items-center gap-3.5">
          <div className="h-10 w-10 rounded-xl bg-slate-800"></div>
          <div className="space-y-2 flex-1">
            <div className="h-4 w-64 bg-slate-800 rounded"></div>
            <div className="h-3 w-40 bg-slate-800/60 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!finding) {
    return null;
  }

  const displayTitle = finding.title || "Systemic Anomaly Detected (AI Synthesis)";
  const displayBadgeLabel = finding.badge_label || "Gemini 3.6 + Deterministic Baseline";
  const displayDesc = overrideDesc || finding.narration;
  const statPrimary = finding.stat_badge_primary || `${finding.bucket_count}/${finding.total_cases_in_scope || finding.total_count} Affected (${((finding.observed_share || 0) * 100).toFixed(1)}%)`;
  const statSecondary = finding.stat_badge_secondary || (finding.excess_ratio ? `${finding.excess_ratio}x Baseline Anomaly` : "");
  const ruleTitle = finding.rule_enforcement_title || "Rule Enforcement:";
  const ruleDetail = finding.rule_enforcement_detail || finding.grouping_description;
  const ruleOutcome = finding.rule_enforcement_outcome || "Policy Enforced";

  return (
    <div className="rounded-2xl border border-blue-500/30 bg-gradient-to-br from-blue-950/40 via-slate-900/90 to-slate-950 p-6 shadow-2xl backdrop-blur-xl space-y-5 transition-all duration-300 relative overflow-hidden">
      <div className="absolute top-0 right-0 -mt-10 -mr-10 w-48 h-48 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white shadow-lg shadow-blue-500/25 border border-blue-400/30">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="text-base sm:text-lg font-bold uppercase tracking-wider text-white">
                {displayTitle}
              </span>
              <Badge className="border-blue-400/30 bg-blue-500/15 text-blue-300 text-xs font-semibold px-3 py-0.5 rounded-full shadow-xs backdrop-blur-md">
                {displayBadgeLabel}
              </Badge>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content: 2-Column Responsive Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-stretch">
        
        {/* Left Column (8 cols): AI Synthesis Narrative & Enforcement */}
        <div className="lg:col-span-8 rounded-xl border border-slate-800 bg-slate-900/70 backdrop-blur-md p-5 shadow-sm flex flex-col justify-between space-y-4">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <Clock className="h-4 w-4" />
            </div>
            <p className="text-sm sm:text-base text-slate-200 font-medium leading-relaxed">
              {displayDesc}
            </p>
          </div>

          <div className="pt-3 border-t border-slate-800 flex flex-wrap items-center gap-2 text-xs sm:text-sm font-semibold">
            <span className="text-blue-400 font-bold uppercase tracking-wider text-xs">{ruleTitle}</span>
            <span className="text-slate-300 font-normal">{ruleDetail}</span>
            <ArrowRight className="h-3.5 w-3.5 text-slate-500 shrink-0" />
            <span className="text-emerald-400 font-bold">{ruleOutcome}</span>
          </div>
        </div>

        {/* Right Column (4 cols): Dedicated Telemetry Metric Cards */}
        <div className="lg:col-span-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-3">
          
          {/* Metric 1 */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/70 backdrop-blur-md p-4 shadow-sm flex items-center justify-between">
            <div className="space-y-0.5">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
                Observed Cluster
              </span>
              <span className="font-mono text-lg sm:text-xl font-bold text-white block">
                {statPrimary}
              </span>
            </div>
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Activity className="h-5 w-5" />
            </div>
          </div>

          {/* Metric 2 */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/70 backdrop-blur-md p-4 shadow-sm flex items-center justify-between">
            <div className="space-y-0.5">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
                Baseline Multiplier
              </span>
              <span className="font-mono text-lg sm:text-xl font-bold text-amber-400 block">
                {statSecondary}
              </span>
            </div>
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <ArrowUpRight className="h-5 w-5" />
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}