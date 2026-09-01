import { useState } from "react";
import ModuleA from "./ModuleA";
import ModuleB from "./ModuleB";
import ModuleC from "./ModuleC";
import BatchSummary from "@/components/batch/BatchSummary";
import SystemicPatternCallout from "@/components/batch/SystemicPatternCallout";
import { useBatches, useRunBatch } from "@/api/useBatchSummary";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
  Zap, 
  RefreshCw, 
  CreditCard, 
  Building2, 
  ShoppingCart
} from "lucide-react";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<"A" | "B" | "C">("A");
  const { data: batches } = useBatches();
  const [selectedBatchId, setSelectedBatchId] = useState<string | null>(null);
  const runBatchMutation = useRunBatch();

  const currentBatchId = selectedBatchId || batches?.[0]?.id || null;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col">
      {/* 1. Razorpay Navy Top Navigation Bar */}
      <header className="sticky top-0 z-40 border-b border-slate-800 bg-[#0c2340] px-6 py-3.5 text-white shadow-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded bg-blue-600 font-bold text-white shadow-xs">
              <Zap className="h-5 w-5 fill-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold tracking-tight text-white">
                  Razorpay AI Revenue Recovery
                </h1>
                <Badge className="border-blue-400/40 bg-blue-500/20 text-blue-200 text-[10px] font-semibold">
                  Autonomous Gateway Agent
                </Badge>
              </div>
              <p className="text-[11px] text-slate-300">
                Multi-Class Financial Recovery &bull; MSMED Act Section 16 Grounding &bull; 100% Deterministic Policy Gates
              </p>
            </div>
          </div>

          {/* Right Header Actions */}
          <div className="flex items-center gap-3">
            {/* Batch Selector */}
            {batches && batches.length > 0 && (
              <div className="flex items-center gap-1.5 text-xs text-slate-300">
                <span className="text-[11px] text-slate-400 font-medium uppercase tracking-wider">Batch:</span>
                <select
                  value={currentBatchId || ""}
                  onChange={(e) => setSelectedBatchId(e.target.value)}
                  className="rounded border border-slate-700 bg-slate-800/90 px-2.5 py-1 text-xs text-white focus:border-blue-500 focus:outline-none"
                >
                  {batches.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.label} ({new Date(b.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })})
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Run Batch Button */}
            <Button
              onClick={() => runBatchMutation.mutate()}
              disabled={runBatchMutation.isPending}
              className="bg-blue-600 text-white hover:bg-blue-500 text-xs font-semibold gap-1.5 h-8 px-3.5 shadow-sm"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${runBatchMutation.isPending ? "animate-spin" : ""}`} />
              {runBatchMutation.isPending ? "Generating 135-Case Batch..." : "Run Synthetic Scenario"}
            </Button>
          </div>
        </div>
      </header>

      {/* Main Dashboard Container */}
      <main className="mx-auto w-full max-w-7xl flex-1 p-6 space-y-6">
        {/* 2. Top KPI Stat Bar */}
        <BatchSummary batchId={currentBatchId} />

        {/* 3. Systemic Anomaly Callout Banner */}
        <SystemicPatternCallout batchId={currentBatchId} />

        {/* 4. Module Queue Tabs */}
        <Tabs value={activeTab} onValueChange={(val) => setActiveTab(val as "A" | "B" | "C")} className="space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <TabsList className="bg-slate-200/70 p-1 rounded-lg">
              <TabsTrigger
                value="A"
                className="data-[state=active]:bg-white data-[state=active]:text-slate-900 text-xs font-semibold gap-1.5 px-4 py-1.5"
              >
                <CreditCard className="h-3.5 w-3.5 text-blue-600" />
                <span>Module A: Payments &amp; Mandates</span>
                <Badge variant="outline" className="ml-1 border-slate-300 bg-slate-100 text-slate-700 text-[10px] px-1.5 py-0 font-mono">
                  60
                </Badge>
              </TabsTrigger>

              <TabsTrigger
                value="B"
                className="data-[state=active]:bg-white data-[state=active]:text-slate-900 text-xs font-semibold gap-1.5 px-4 py-1.5"
              >
                <Building2 className="h-3.5 w-3.5 text-amber-600" />
                <span>Module B: B2B Invoices &amp; MSMED</span>
                <Badge variant="outline" className="ml-1 border-slate-300 bg-slate-100 text-slate-700 text-[10px] px-1.5 py-0 font-mono">
                  50
                </Badge>
              </TabsTrigger>

              <TabsTrigger
                value="C"
                className="data-[state=active]:bg-white data-[state=active]:text-slate-900 text-xs font-semibold gap-1.5 px-4 py-1.5"
              >
                <ShoppingCart className="h-3.5 w-3.5 text-indigo-600" />
                <span>Module C: Abandoned Checkout</span>
                <Badge variant="outline" className="ml-1 border-slate-300 bg-slate-100 text-slate-700 text-[10px] px-1.5 py-0 font-mono">
                  25
                </Badge>
              </TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="A" className="mt-0 focus-visible:outline-none">
            <ModuleA batchId={currentBatchId} />
          </TabsContent>

          <TabsContent value="B" className="mt-0 focus-visible:outline-none">
            <ModuleB batchId={currentBatchId} />
          </TabsContent>

          <TabsContent value="C" className="mt-0 focus-visible:outline-none">
            <ModuleC batchId={currentBatchId} />
          </TabsContent>
        </Tabs>
      </main>

      {/* Footer */}
      <footer className="mt-auto border-t border-slate-200 bg-white px-6 py-4 text-xs text-slate-500">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-700">Razorpay AI Revenue Recovery</span>
            <span>&bull;</span>
            <span>Track 03 Submission</span>
          </div>
          <div className="flex items-center gap-4 text-slate-400">
            <span>FastAPI + PostgreSQL (Neon)</span>
            <span>&bull;</span>
            <span>LangGraph Multi-Agent Engine</span>
            <span>&bull;</span>
            <span>Razorpay Sandbox Verified</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

