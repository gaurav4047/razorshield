import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Sparkles, BrainCircuit, Check } from "lucide-react";


interface AiVsRuleDisagreementProps {
  ruleSuggestedAction: string | null;
  finalAction: string;
  aiReasoningText: string | null;
}

export default function AiVsRuleDisagreement({
  ruleSuggestedAction,
  finalAction,
  aiReasoningText,
}: AiVsRuleDisagreementProps) {
  if (!ruleSuggestedAction || ruleSuggestedAction === finalAction) {
    return null;
  }

  return (
    <Card className="border-indigo-300 bg-gradient-to-br from-indigo-50/70 via-white to-blue-50/40 shadow-sm overflow-hidden">
      <CardContent className="p-4">
        <div className="flex items-center justify-between border-b border-indigo-100 pb-2.5">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded bg-indigo-600 text-white">
              <BrainCircuit className="h-3.5 w-3.5" />
            </div>
            <span className="text-xs font-bold uppercase tracking-wider text-indigo-950">
              AI Override: Naive Rule Divergence
            </span>
          </div>
          <Badge className="border-indigo-300 bg-indigo-100 text-indigo-900 text-[10px] font-semibold gap-1">
            <Sparkles className="h-3 w-3 text-indigo-600" />
            Active Override
          </Badge>
        </div>

        {/* Before vs After Comparison */}
        <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
          {/* Struck-Through Naive Rule */}
          <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
            <p className="text-[11px] font-semibold uppercase text-slate-500">
              Naive Rule Recommendation
            </p>
            <p className="mt-1 font-mono text-sm text-slate-400 line-through decoration-rose-500 decoration-2">
              {ruleSuggestedAction}
            </p>
            <p className="mt-1 text-[11px] text-slate-400">
              Deterministic default without case history context
            </p>
          </div>

          {/* Final Action Executed */}
          <div className="rounded-md border border-emerald-200 bg-emerald-50/50 p-3">
            <div className="flex items-center justify-between">
              <p className="text-[11px] font-semibold uppercase text-emerald-800">
                AI Intervened Recommendation
              </p>
              <Check className="h-3.5 w-3.5 text-emerald-600" />
            </div>
            <p className="mt-1 font-mono text-sm font-bold text-emerald-900">
              {finalAction}
            </p>
            <p className="mt-1 text-[11px] text-emerald-700 font-medium">
              Validated &amp; Approved by Policy Gate
            </p>
          </div>
        </div>

        {/* AI Reasoning Text */}
        {aiReasoningText && (
          <div className="mt-3 rounded-md border border-indigo-200/80 bg-white p-3 shadow-xs">
            <div className="flex items-center gap-1.5 text-xs font-bold text-indigo-950">
              <Sparkles className="h-3.5 w-3.5 text-indigo-600" />
              <span>AI Reasoning &amp; Synthesis</span>
            </div>
            <p className="mt-1 text-xs leading-relaxed text-slate-700 italic bg-slate-50 p-2.5 rounded border border-slate-100">
              "{aiReasoningText}"
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

