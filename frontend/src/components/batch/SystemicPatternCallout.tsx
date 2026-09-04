import { useBatchPattern } from "@/api/useBatchSummary";
import { Badge } from "@/components/ui/badge";
import { Sparkles, Activity, Clock, ArrowRight, ArrowUpRight, ShieldCheck } from "lucide-react";

interface SystemicPatternCalloutProps {
  batchId?: string | null;
  patternDescription?: string | null;
  affectedCount?: number | null;
  activeModule?: "A" | "B" | "C";
}

export default function SystemicPatternCallout({
  batchId,
  patternDescription: overrideDesc,
  affectedCount: overrideCount,
  activeModule = "A",
}: SystemicPatternCalloutProps) {
  const { data: patternData, isLoading } = useBatchPattern(batchId || null, activeModule);

  const finding = patternData?.findings?.[0];

  // While loading, render smooth skeleton so banner does not flash or vanish on refresh
  if (isLoading && !finding) {
    return (
      <div className="rounded-3xl border border-blue-200/60 bg-blue-50/50 p-6 sm:p-7 shadow-xs space-y-4 animate-pulse">
        <div className="flex items-center gap-3.5">
          <div className="h-11 w-11 rounded-2xl bg-blue-200/70"></div>
          <div className="space-y-2 flex-1">
            <div className="h-4 w-64 bg-blue-200/70 rounded"></div>
            <div className="h-3 w-40 bg-blue-100 rounded"></div>
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
    <div className="rounded-3xl border border-blue-300/90 bg-gradient-to-br from-blue-200/90 via-blue-100/80 to-indigo-100/90 p-6 sm:p-7 shadow-xs space-y-5 transition-all duration-300">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#0066ff] text-white shadow-sm shadow-blue-500/25">
            <Sparkles className="h-6 w-6" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="text-base sm:text-lg font-black uppercase tracking-wider text-[#0c2340]">
                {displayTitle}
              </span>
              <Badge className="border-blue-200/80 bg-white/90 text-[#0066ff] text-xs sm:text-sm font-bold px-3 py-0.5 rounded-full shadow-2xs">
                {displayBadgeLabel}
              </Badge>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content: 2-Column Responsive Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
        
        {/* Left Column (8 cols): AI Synthesis Narrative & Enforcement */}
        <div className="lg:col-span-8 rounded-2xl border border-blue-100/90 bg-white/95 backdrop-blur-sm p-6 sm:p-7 shadow-xs flex flex-col justify-between space-y-5">
          <div className="flex items-start gap-3.5">
            <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-[#0066ff]">
              <Clock className="h-4.5 w-4.5" />
            </div>
            <p className="text-base sm:text-lg lg:text-[18px] text-slate-800 font-semibold leading-relaxed">
              {displayDesc}
            </p>
          </div>

          <div className="pt-3.5 border-t border-slate-100 flex flex-wrap items-center gap-2 text-xs sm:text-sm font-semibold text-slate-700">
            <span className="text-[#0066ff] font-extrabold uppercase tracking-wide">{ruleTitle}</span>
            <span className="text-slate-700 font-medium">{ruleDetail}</span>
            <ArrowRight className="h-4 w-4 text-slate-400 shrink-0" />
            <span className="text-emerald-700 font-extrabold">{ruleOutcome}</span>
          </div>
        </div>

        {/* Right Column (4 cols): Dedicated Telemetry Metric Cards */}
        <div className="lg:col-span-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-3.5">
          
          {/* Metric 1 */}
          <div className="rounded-2xl border border-blue-100/90 bg-white/95 backdrop-blur-sm p-4 sm:p-5 shadow-xs flex items-center justify-between hover:shadow-sm transition-all">
            <div className="space-y-0.5">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500 block">
                Observed Cluster
              </span>
              <span className="font-mono text-xl sm:text-2xl font-black text-[#0c2340] block">
                {statPrimary}
              </span>
            </div>
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600 shadow-2xs">
              <Activity className="h-5 w-5" />
            </div>
          </div>

          {/* Metric 2 */}
          <div className="rounded-2xl border border-blue-100/90 bg-white/95 backdrop-blur-sm p-4 sm:p-5 shadow-xs flex items-center justify-between hover:shadow-sm transition-all">
            <div className="space-y-0.5">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500 block">
                Baseline Multiplier
              </span>
              <span className="font-mono text-xl sm:text-2xl font-black text-amber-600 block">
                {statSecondary}
              </span>
            </div>
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-amber-50 text-amber-600 shadow-2xs">
              <ArrowUpRight className="h-5 w-5" />
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}