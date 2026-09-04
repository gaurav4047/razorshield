import { useState, useEffect } from "react";
import ModuleA from "./ModuleA";
import ModuleB from "./ModuleB";
import ModuleC from "./ModuleC";
import BatchSummary from "@/components/batch/BatchSummary";
import SystemicPatternCallout from "@/components/batch/SystemicPatternCallout";
import { useBatches, useRunBatch, useBatchSummary } from "@/api/useBatchSummary";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
  RefreshCw, 
  CreditCard, 
  Building2, 
  ShoppingCart,
  ArrowLeft,
  Layers,
  BadgeCheck
} from "lucide-react";

interface DashboardProps {
  onBackToLanding?: () => void;
}

export default function Dashboard({ onBackToLanding }: DashboardProps) {
  const [activeTab, setActiveTab] = useState<"A" | "B" | "C">("A");
  const [isScrolled, setIsScrolled] = useState(false);
  const { data: batches } = useBatches();
  const [selectedBatchId, setSelectedBatchId] = useState<string | null>(null);
  const runBatchMutation = useRunBatch((newBatchId) => {
    setSelectedBatchId(newBatchId);
  });

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const currentBatchId = selectedBatchId || batches?.[0]?.id || null;
  const { data: summary } = useBatchSummary(currentBatchId);

  const countA = summary?.modules?.A?.cases ?? 0;
  const countB = summary?.modules?.B?.cases ?? 0;
  const countC = summary?.modules?.C?.cases ?? 0;

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-900 flex flex-col font-sans antialiased selection:bg-blue-600 selection:text-white">
      {/* 1. Header Navigation */}
      <header 
        className={`sticky top-0 z-40 px-6 lg:px-12 transition-all duration-300 ${
          isScrolled 
            ? "border-b border-slate-200/80 bg-white/80 backdrop-blur-xl shadow-xs py-3.5 sm:py-4" 
            : "border-b border-slate-200/50 bg-white/60 backdrop-blur-md py-4 sm:py-5"
        }`}
      >
        <div className="mx-auto flex max-w-[1720px] items-center justify-between gap-4">
          
          {/* Brand Identity */}
          <div className="flex items-center gap-3.5 select-none">
            <img 
              src="/logo.png" 
              alt="ReClaim" 
              className="h-11 w-11 rounded-xl object-contain bg-white p-1 shadow-xs border border-slate-200" 
            />
            <div>
              <div className="flex items-center gap-2.5">
                <span className="text-2xl font-extrabold tracking-tight text-[#0c2340]">
                  Re<span className="text-[#0066ff]">Claim</span>
                </span>
                <Badge className="border-blue-200/80 bg-blue-50 text-[#0066ff] text-xs font-bold px-3 py-0.5 rounded-full shadow-xs">
                  Operations Console
                </Badge>
              </div>
              <p className="text-xs sm:text-sm text-slate-500 font-medium">
                Autonomous Recovery for Indian Commerce
              </p>
            </div>
          </div>

          {/* Right Header Actions */}
          <div className="flex flex-wrap items-center gap-3.5">
            {onBackToLanding && (
              <Button
                variant="outline"
                onClick={onBackToLanding}
                className="border-slate-200/80 bg-white/70 backdrop-blur-sm hover:bg-white hover:border-slate-300 text-slate-700 hover:text-slate-900 text-sm font-bold h-11 px-4 rounded-xl shadow-2xs gap-2 transition-all active:scale-98"
              >
                <ArrowLeft className="h-4 w-4 text-slate-500" />
                <span>Product Overview</span>
              </Button>
            )}

            {/* Batch Selector */}
            {batches && batches.length > 0 && (
              <div className="flex items-center gap-2">
                <div className="relative">
                  <select
                    value={currentBatchId || ""}
                    onChange={(e) => setSelectedBatchId(e.target.value)}
                    className="h-11 rounded-xl border border-slate-200/80 bg-white/70 backdrop-blur-sm hover:bg-white focus:bg-white px-3.5 pr-8 text-xs sm:text-sm font-bold text-slate-800 focus:border-[#0066ff] focus:outline-none focus:ring-2 focus:ring-blue-500/20 shadow-2xs appearance-none cursor-pointer transition-all"
                  >
                    {batches.map((b) => (
                      <option key={b.id} value={b.id}>
                        {b.label} ({new Date(b.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })})
                      </option>
                    ))}
                  </select>
                  <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-400">
                    <Layers className="h-3.5 w-3.5" />
                  </div>
                </div>
              </div>
            )}

            {/* Run Batch Button */}
            <Button
              onClick={() => runBatchMutation.mutate()}
              disabled={runBatchMutation.isPending}
              className="bg-[#0066ff] text-white hover:bg-[#0052cc] text-xs sm:text-sm font-bold gap-2 h-11 px-5 rounded-xl shadow-md shadow-blue-500/20 hover:shadow-lg hover:shadow-blue-500/30 transition-all active:scale-98"
            >
              <RefreshCw className={`h-4 w-4 ${runBatchMutation.isPending ? "animate-spin" : ""}`} />
              <span>{runBatchMutation.isPending ? "Generating 135 Cases..." : "Run Synthetic Scenario"}</span>
            </Button>
          </div>

        </div>
      </header>

      {/* Main Dashboard Container */}
      <main className="mx-auto w-full max-w-[1720px] flex-1 px-6 lg:px-12 py-8 space-y-8">
        
        {/* 2. Top KPI Stat Bar */}
        <BatchSummary batchId={currentBatchId} />

        {/* 3. Systemic Anomaly Callout Banner (Contextual per active module tab) */}
        <SystemicPatternCallout batchId={currentBatchId} activeModule={activeTab} />

        {/* 4. Module Queue Tabs */}
        <Tabs value={activeTab} onValueChange={(val) => setActiveTab(val as "A" | "B" | "C")} className="space-y-6">
          <div className="flex items-center justify-between border-b border-slate-200/90 pb-3">
            <TabsList className="bg-slate-100 p-1.5 rounded-2xl border border-slate-200/80 shadow-inner h-auto">
              <TabsTrigger
                value="A"
                className="data-[state=active]:bg-white data-[state=active]:text-[#0066ff] data-[state=active]:shadow-sm data-[state=active]:ring-2 data-[state=active]:ring-blue-500/20 text-xs sm:text-sm font-bold gap-2.5 px-6 py-3 rounded-xl transition-all"
              >
                <CreditCard className="h-4 w-4" />
                <span>Module A: Payments &amp; Mandates</span>
                <Badge variant="outline" className="ml-1.5 border-slate-200 bg-slate-50 text-slate-700 text-xs px-2.5 py-0.5 font-mono font-bold">
                  {countA}
                </Badge>
              </TabsTrigger>

              <TabsTrigger
                value="B"
                className="data-[state=active]:bg-white data-[state=active]:text-amber-800 data-[state=active]:shadow-sm data-[state=active]:ring-2 data-[state=active]:ring-amber-500/20 text-xs sm:text-sm font-bold gap-2.5 px-6 py-3 rounded-xl transition-all"
              >
                <Building2 className="h-4 w-4" />
                <span>Module B: B2B Invoices &amp; MSMED</span>
                <Badge variant="outline" className="ml-1.5 border-slate-200 bg-slate-50 text-slate-700 text-xs px-2.5 py-0.5 font-mono font-bold">
                  {countB}
                </Badge>
              </TabsTrigger>

              <TabsTrigger
                value="C"
                className="data-[state=active]:bg-white data-[state=active]:text-indigo-800 data-[state=active]:shadow-sm data-[state=active]:ring-2 data-[state=active]:ring-indigo-500/20 text-xs sm:text-sm font-bold gap-2.5 px-6 py-3 rounded-xl transition-all"
              >
                <ShoppingCart className="h-4 w-4" />
                <span>Module C: Abandoned Checkout</span>
                <Badge variant="outline" className="ml-1.5 border-slate-200 bg-slate-50 text-slate-700 text-xs px-2.5 py-0.5 font-mono font-bold">
                  {countC}
                </Badge>
              </TabsTrigger>
            </TabsList>
          </div>

          <div key={activeTab} className="animate-in fade-in duration-300 slide-in-from-bottom-2">
            <TabsContent value="A" className="mt-0 focus-visible:outline-none">
              <ModuleA batchId={currentBatchId} />
            </TabsContent>

            <TabsContent value="B" className="mt-0 focus-visible:outline-none">
              <ModuleB batchId={currentBatchId} />
            </TabsContent>

            <TabsContent value="C" className="mt-0 focus-visible:outline-none">
              <ModuleC batchId={currentBatchId} />
            </TabsContent>
          </div>
        </Tabs>
      </main>

      {/* Footer */}
      <footer className="mt-auto border-t border-slate-200 bg-white px-6 lg:px-12 py-7 text-sm sm:text-base text-slate-500 font-medium">
        <div className="mx-auto flex max-w-[1720px] flex-col sm:flex-row items-center justify-between gap-4">
          <p>
            &copy; 2026 ReClaim &bull; Track 03 Submission
          </p>
          <p className="flex items-center gap-2 text-slate-600">
            <BadgeCheck className="h-5 w-5 text-[#0066ff]" />
            <span>Real Razorpay Sandbox API Verified &bull; Zero Mock Gateway Responses</span>
          </p>
        </div>
      </footer>
    </div>
  );
}