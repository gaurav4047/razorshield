interface SystemicPatternCalloutProps {
  batchId?: string | null;
  patternDescription?: string | null;
  affectedCount?: number | null;
}

export default function SystemicPatternCallout({
  patternDescription,
  affectedCount,
}: SystemicPatternCalloutProps) {
  if (!patternDescription) return null;

  return (
    <div className="mt-4 rounded-lg border-2 border-indigo-500 bg-indigo-50/70 p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="rounded bg-indigo-600 px-2 py-0.5 text-xs font-bold uppercase tracking-wider text-white">
            Systemic Pattern Detected
          </span>
          {affectedCount && (
            <span className="text-xs font-semibold text-indigo-700">
              {affectedCount} cases affected
            </span>
          )}
        </div>
      </div>
      <p className="mt-2 text-sm font-medium text-indigo-950">{patternDescription}</p>
    </div>
  );
}
