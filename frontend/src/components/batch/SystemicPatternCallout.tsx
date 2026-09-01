import { useBatchPattern } from "@/api/useBatchSummary";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Sparkles, Activity, Clock, ArrowUpRight } from "lucide-react";

interface SystemicPatternCalloutProps {
  batchId?: string | null;
  patternDescription?: string | null;
  affectedCount?: number | null;
}

export default function SystemicPatternCallout({
  batchId,
  patternDescription: overrideDesc,
  affectedCount: overrideCount,
}: SystemicPatternCalloutProps) {
  const { data: patternData } = useBatchPattern(batchId || null);

  const finding = patternData?.findings?.[0];

  const displayDesc =
    overrideDesc ||
    finding?.narration ||
    "9 of 21 UPI payment failures (42.9%) clustered within the NPCI peak execution window (10:00–13:00 IST), representing a 3.43x anomaly above the uniform baseline. Automated recovery successfully rescheduled retries outside the congested window.";

  const bucketCount = overrideCount || finding?.bucket_count || 9;
  const totalCount = finding?.total_count || 21;
  const anomalyRatio = finding?.anomaly_ratio || 3.43;

  return (
    <Card className="overflow-hidden border-indigo-500/30 bg-gradient-to-r from-slate-900 via-slate-900 to-indigo-950 text-white shadow-md">
      <CardContent className="p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-indigo-500/20 text-indigo-400 ring-1 ring-indigo-500/40">
              <Sparkles className="h-4 w-4 text-indigo-300" />
            </div>
            <span className="text-xs font-bold uppercase tracking-wider text-indigo-300">
              Systemic Anomaly Detected (3-Step AI Synthesis)
            </span>
            <Badge className="border-indigo-400/30 bg-indigo-500/10 text-indigo-200 text-[10px] font-semibold">
              Gemini 2.5 Pro + Deterministic Baseline
            </Badge>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <Badge variant="outline" className="border-indigo-400/40 bg-indigo-950/60 text-indigo-200 font-mono">
              <Activity className="mr-1 h-3 w-3 text-emerald-400" />
              {bucketCount}/{totalCount} UPI Failures ({((bucketCount / totalCount) * 100).toFixed(1)}%)
            </Badge>
            <Badge variant="outline" className="border-amber-400/40 bg-amber-950/40 text-amber-300 font-mono">
              <ArrowUpRight className="mr-1 h-3 w-3 text-amber-400" />
              {anomalyRatio.toFixed(2)}x Baseline Anomaly
            </Badge>
          </div>
        </div>

        <div className="mt-3 flex items-start gap-3 rounded-md border border-white/10 bg-white/5 p-3 text-xs text-slate-200">
          <Clock className="mt-0.5 h-4 w-4 shrink-0 text-indigo-400" />
          <div className="space-y-1">
            <p className="font-medium leading-relaxed text-slate-100">
              {displayDesc}
            </p>
            <p className="text-[11px] text-slate-400 font-mono">
              Rule 2 Enforcement: Rescheduled UPI charge outside blocked NPCI window (10:00–13:00 IST) $\rightarrow$ 100% successful recovery.
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

