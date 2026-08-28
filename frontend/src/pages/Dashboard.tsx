import { useState } from "react";
import ModuleA from "./ModuleA";
import ModuleB from "./ModuleB";
import ModuleC from "./ModuleC";
import BatchSummaryCard from "@/components/batch/BatchSummary";
import SystemicPatternCallout from "@/components/batch/SystemicPatternCallout";
import { useBatches, useRunBatch } from "@/api/useBatchSummary";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<"A" | "B" | "C">("A");
  const { data: batches } = useBatches();
  const [selectedBatchId] = useState<string | null>(null);
  const runBatchMutation = useRunBatch();

  const currentBatchId = selectedBatchId || batches?.[0]?.id || null;

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <header className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Razorpay AI Revenue Recovery</h1>
          <p className="text-sm text-slate-500">Autonomous multi-class revenue recovery intelligence</p>
        </div>
        <button
          onClick={() => runBatchMutation.mutate()}
          disabled={runBatchMutation.isPending}
          className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {runBatchMutation.isPending ? "Generating..." : "Run recovery batch"}
        </button>
      </header>

      <BatchSummaryCard batchId={currentBatchId} />
      <SystemicPatternCallout batchId={currentBatchId} />

      <div className="mt-6">
        <div className="flex border-b border-slate-200">
          <button
            onClick={() => setActiveTab("A")}
            className={`px-4 py-2 text-sm font-medium ${
              activeTab === "A"
                ? "border-b-2 border-blue-600 text-blue-600"
                : "text-slate-500 hover:text-slate-700"
            }`}
          >
            Module A: Payments & Mandates
          </button>
          <button
            onClick={() => setActiveTab("B")}
            className={`px-4 py-2 text-sm font-medium ${
              activeTab === "B"
                ? "border-b-2 border-blue-600 text-blue-600"
                : "text-slate-500 hover:text-slate-700"
            }`}
          >
            Module B: B2B Receivables
          </button>
          <button
            onClick={() => setActiveTab("C")}
            className={`px-4 py-2 text-sm font-medium ${
              activeTab === "C"
                ? "border-b-2 border-blue-600 text-blue-600"
                : "text-slate-500 hover:text-slate-700"
            }`}
          >
            Module C: Checkout Abandonment
          </button>
        </div>

        <div className="mt-4">
          {activeTab === "A" && <ModuleA batchId={currentBatchId} />}
          {activeTab === "B" && <ModuleB batchId={currentBatchId} />}
          {activeTab === "C" && <ModuleC batchId={currentBatchId} />}
        </div>
      </div>
    </div>
  );
}
