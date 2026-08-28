import { useCaseDetail } from "@/api/useCases";
import { formatPaiseToRupees } from "@/lib/utils";
import AiVsRuleDisagreement from "./AiVsRuleDisagreement";
import InterestAccrualCounter from "@/components/receivables/InterestAccrualCounter";

interface DecisionPacketProps {
  module: "A" | "B" | "C";
  caseId: string;
  onClose: () => void;
}

export default function DecisionPacket({ module, caseId, onClose }: DecisionPacketProps) {
  const { data: caseDetail, isLoading } = useCaseDetail(module, caseId);

  if (isLoading || !caseDetail) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
        <div className="rounded-lg bg-white p-6 shadow-xl">Loading decision packet...</div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white p-6 shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-200 pb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Decision Packet</h2>
            <p className="text-xs text-slate-500">Case ID: {caseId}</p>
          </div>
          <button
            onClick={onClose}
            className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
          >
            Close
          </button>
        </div>

        <div className="mt-4 space-y-4">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <h3 className="text-xs font-semibold uppercase text-slate-500">Signal Input</h3>
            <div className="mt-2 text-sm text-slate-800">
              {"failure_raw_reason" in caseDetail && (
                <p><span className="font-medium">Raw Reason:</span> {caseDetail.failure_raw_reason}</p>
              )}
              {"invoice_number" in caseDetail && (
                <p><span className="font-medium">Invoice:</span> {caseDetail.invoice_number} - {caseDetail.buyer_name}</p>
              )}
              {"order_created_at" in caseDetail && (
                <p><span className="font-medium">Order Created:</span> {new Date(caseDetail.order_created_at).toLocaleString()}</p>
              )}
              <p><span className="font-medium">Amount:</span> {formatPaiseToRupees(caseDetail.amount_paise)}</p>
            </div>
          </div>

          {"supplier_is_msme" in caseDetail && caseDetail.supplier_is_msme && (
            <InterestAccrualCounter invoice={caseDetail as any} />
          )}

          <AiVsRuleDisagreement
            ruleSuggestedAction={null}
            finalAction={(caseDetail as any).status}
            aiReasoningText={null}
          />
        </div>
      </div>
    </div>
  );
}
