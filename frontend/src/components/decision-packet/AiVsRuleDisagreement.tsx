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
    return (
      <div className="rounded-2xl border border-slate-200/90 bg-white p-5 sm:p-6 shadow-xs space-y-3.5">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <span className="text-xs sm:text-sm font-black uppercase tracking-wider text-[#0c2340] flex items-center gap-2.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-100 text-[#0066ff]">
              <BrainCircuit className="h-4 w-4" />
            </div>
            AI &amp; Gateway Rule Consensus
          </span>
          <Badge className="border-emerald-200 bg-emerald-100 text-emerald-800 text-xs font-bold px-3 py-1 rounded-full shadow-2xs flex items-center gap-1.5">
            <Check className="h-3.5 w-3.5 text-emerald-600" />
            Gateway Aligned
          </Badge>
        </div>

        <div className="rounded-xl border border-blue-100 bg-blue-50/50 p-4">
          <p className="text-xs sm:text-sm text-slate-700 leading-relaxed font-medium">
            Deterministic rule engine and Gemini AI reasoning layer are in full consensus on:{" "}
            <strong className="text-[#0c2340] font-black font-mono text-sm sm:text-base ml-1">{finalAction}</strong>
          </p>
          <p className="text-xs text-slate-500 mt-1 font-normal">
            No conflicting payment signals or policy overrides detected for this account.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-indigo-300/90 bg-white p-5 sm:p-6 shadow-xs space-y-4">
      <div className="flex items-center justify-between border-b border-indigo-100 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-600 text-white">
            <BrainCircuit className="h-4 w-4" />
          </div>
          <span className="text-xs sm:text-sm font-black uppercase tracking-wider text-indigo-950">
            AI Override: Naive Rule Divergence
          </span>
        </div>
        <Badge className="border-indigo-300 bg-indigo-100 text-indigo-900 text-xs font-bold gap-1 px-2.5 py-0.5 rounded-full shadow-2xs">
          <Sparkles className="h-3 w-3 text-indigo-600" />
          Active Override
        </Badge>
      </div>

      {/* Before vs After Comparison */}
      <div className="grid grid-cols-1 gap-3.5 sm:grid-cols-2">
        {/* Struck-Through Naive Rule */}
        <div className="rounded-xl border border-slate-200/90 bg-slate-50/80 p-4">
          <p className="text-xs font-bold uppercase text-slate-500">
            Naive Rule Recommendation
          </p>
          <p className="mt-1.5 font-mono text-base font-bold text-slate-400 line-through decoration-rose-500 decoration-2">
            {ruleSuggestedAction}
          </p>
          <p className="mt-1 text-xs text-slate-400">
            Deterministic default without case history context
          </p>
        </div>

        {/* Final Action Executed */}
        <div className="rounded-xl border border-emerald-200 bg-emerald-50/60 p-4">
          <div className="flex items-center justify-between">
            <p className="text-xs font-bold uppercase text-emerald-800">
              AI Intervened Recommendation
            </p>
            <Check className="h-4 w-4 text-emerald-600" />
          </div>
          <p className="mt-1.5 font-mono text-base font-black text-emerald-900">
            {finalAction}
          </p>
          <p className="mt-1 text-xs text-emerald-700 font-medium">
            Validated &amp; Approved by Policy Gate
          </p>
        </div>
      </div>

      {/* AI Reasoning Text */}
      {aiReasoningText && (
        <div className="rounded-xl border border-indigo-200/80 bg-indigo-50/40 p-4 shadow-2xs">
          <div className="flex items-center gap-1.5 text-xs font-bold text-indigo-950">
            <Sparkles className="h-3.5 w-3.5 text-indigo-600" />
            <span>AI Reasoning &amp; Synthesis</span>
          </div>
          <p className="mt-1.5 text-xs sm:text-sm leading-relaxed text-slate-700 italic bg-white p-3 rounded-lg border border-indigo-100 font-medium">
            "{aiReasoningText}"
          </p>
        </div>
      )}
    </div>
  );
}

