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
    <div className="rounded-lg border-2 border-amber-400 bg-amber-50/60 p-4">
      <div className="flex items-center gap-2">
        <span className="rounded bg-amber-600 px-2 py-0.5 text-xs font-bold uppercase text-white">
          AI Overrode Naive Rule
        </span>
      </div>

      <div className="mt-3 flex items-center gap-4 text-sm">
        <div>
          <p className="text-xs text-slate-500">Default Rule Recommendation</p>
          <p className="font-mono text-slate-400 line-through">{ruleSuggestedAction}</p>
        </div>
        <span className="text-slate-400">→</span>
        <div>
          <p className="text-xs text-slate-500">Final Action Taken</p>
          <p className="font-mono font-bold text-slate-900">{finalAction}</p>
        </div>
      </div>

      {aiReasoningText && (
        <div className="mt-3 rounded border border-amber-200 bg-white p-3 text-xs text-slate-700">
          <p className="font-semibold text-slate-900">AI Reasoning:</p>
          <p className="mt-1">{aiReasoningText}</p>
        </div>
      )}
    </div>
  );
}
