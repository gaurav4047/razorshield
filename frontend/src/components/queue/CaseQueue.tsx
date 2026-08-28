import { useState } from "react";
import { useCases } from "@/api/useCases";
import CaseQueueRow from "./CaseQueueRow";
import DecisionPacket from "@/components/decision-packet/DecisionPacket";

interface CaseQueueProps {
  module: "A" | "B" | "C";
  batchId?: string | null;
}

export default function CaseQueue({ module }: CaseQueueProps) {
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const { data: cases, isLoading } = useCases(module);

  if (isLoading) {
    return <div className="p-8 text-center text-sm text-slate-500">Loading cases...</div>;
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 px-4 py-3">
        <h2 className="text-sm font-semibold text-slate-800">
          {module === "A" && "Payment & Mandate Failure Cases"}
          {module === "B" && "B2B Invoices & Receivables"}
          {module === "C" && "Abandoned Checkout Orders"}
        </h2>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-600">
          <thead className="border-b border-slate-200 bg-slate-50 text-xs font-semibold uppercase text-slate-500">
            <tr>
              {module === "A" && (
                <>
                  <th className="px-4 py-3">Method</th>
                  <th className="px-4 py-3">Amount</th>
                  <th className="px-4 py-3">Root Cause</th>
                  <th className="px-4 py-3">Fault Attribution</th>
                  <th className="px-4 py-3">Status</th>
                </>
              )}
              {module === "B" && (
                <>
                  <th className="px-4 py-3">Invoice #</th>
                  <th className="px-4 py-3">Buyer</th>
                  <th className="px-4 py-3">Amount</th>
                  <th className="px-4 py-3">Rung</th>
                  <th className="px-4 py-3">Status</th>
                </>
              )}
              {module === "C" && (
                <>
                  <th className="px-4 py-3">Customer</th>
                  <th className="px-4 py-3">Amount</th>
                  <th className="px-4 py-3">Created</th>
                  <th className="px-4 py-3">Status</th>
                </>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {cases && cases.length > 0 ? (
              cases.map((item: any) => (
                <CaseQueueRow
                  key={item.id}
                  module={module}
                  item={item}
                  onClick={() => setSelectedCaseId(item.id)}
                />
              ))
            ) : (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-sm text-slate-400">
                  No cases found in this batch.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {selectedCaseId && (
        <DecisionPacket
          module={module}
          caseId={selectedCaseId}
          onClose={() => setSelectedCaseId(null)}
        />
      )}
    </div>
  );
}
