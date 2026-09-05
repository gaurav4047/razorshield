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
    <div className="min-h-screen bg-[#070b12] text-slate-100 flex flex-col font-sans antialiased selection:bg-blue-600 selection:text-white">
      {/* 1. Header Navigation */}
      <header 
        className={`sticky top-0 z-40 px-6 lg:px-12 transition-all duration-300 ${
          isScrolled 
            ? "border-b border-slate-800 bg-slate-950/80 backdrop-blur-xl shadow-2xl py-3.5" 
            : "border-b border-slate-800/80 bg-slate-950/60 backdrop-blur-md py-4 sm:py-5"
        }`}
      >
        <div className="mx-auto flex max-w-[1720px] items-center justify-between gap-4">
          
          {/* Brand Identity */}
          <div className="flex items-center gap-3.5 select-none">
            <div className="h-11 w-11 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center text-white shadow-lg shadow-blue-500/25 border border-blue-400/40">
              <BadgeCheck className="h-6 w-6" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <span className="text-2xl font-black tracking-tight text-white font-sans">
                  Razor<span className="text-blue-500">Shield</span>
                </span>
                <Badge className="border-blue-500/30 bg-blue-500/15 text-blue-300 text-xs font-semibold px-2.5 py-0.5 rounded-full shadow-xs">
                  Autonomous Console
                </Badge>
              </div>
              <p className="text-xs text-slate-400 font-medium">
                Autonomous Revenue Recovery &amp; Gateway Defense
              </p>
            </div>
          </div>

          {/* Right Header Actions */}
          <div className="flex flex-wrap items-center gap-3">
            {onBackToLanding && (
              <Button
                variant="outline"
                onClick={onBackToLanding}
                className="border-slate-800 bg-slate-900/80 hover:bg-slate-850 hover:border-slate-700 text-slate-300 hover:text-white text-xs sm:text-sm font-semibold h-10 px-4 rounded-xl shadow-xs gap-2 transition-all active:scale-98"
              >
                <ArrowLeft className="h-4 w-4 text-slate-400" />
                <span>Interactive Overview</span>
              </Button>
            )}

            {/* Batch Selector */}
            {batches && batches.length > 0 && (
              <div className="flex items-center gap-2">
                <div className="relative">
                  <select
                    value={currentBatchId || ""}
                    onChange={(e) => setSelectedBatchId(e.target.value)}
                    className="h-10 rounded-xl border border-slate-700 bg-slate-900/90 hover:bg-slate-850 px-3.5 pr-8 text-xs sm:text-sm font-semibold text-slate-200 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 shadow-inner appearance-none cursor-pointer transition-all"
                  >
                    {batches.map((b) => (
                      <option key={b.id} value={b.id} className="bg-slate-900 text-slate-200">
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
              className="bg-blue-600 text-white hover:bg-blue-500 text-xs sm:text-sm font-bold gap-2 h-10 px-4.5 rounded-xl shadow-lg shadow-blue-600/30 hover:shadow-blue-500/40 transition-all active:scale-98 border border-blue-400/40"
            >
              <RefreshCw className={`h-4 w-4 ${runBatchMutation.isPending ? "animate-spin" : ""}`} />
              <span>{runBatchMutation.isPending ? "Executing Recovery Run..." : "Run Autonomous Scenario"}</span>
            </Button>
          </div>

        </div>
      </header>

      {/* Main Dashboard Container */}
      <main className="mx-auto w-full max-w-[1720px] flex-1 px-6 lg:px-12 py-8 space-y-7">
        
        {/* 2. Top KPI Stat Bar */}
        <BatchSummary batchId={currentBatchId} />

        {/* 3. Systemic Anomaly Callout Banner (Contextual per active module tab) */}
        <SystemicPatternCallout batchId={currentBatchId} activeModule={activeTab} />

        {/* 4. Module Queue Tabs */}
        <Tabs value={activeTab} onValueChange={(val) => setActiveTab(val as "A" | "B" | "C")} className="space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <TabsList className="bg-slate-900/90 p-1.5 rounded-2xl border border-slate-800 shadow-inner h-auto gap-1">
              <TabsTrigger
                value="A"
                className="data-[state=active]:bg-blue-600 data-[state=active]:text-white data-[state=active]:shadow-md data-[state=active]:border-blue-400/40 text-xs sm:text-sm font-semibold gap-2.5 px-5 py-2.5 rounded-xl transition-all text-slate-400 hover:text-slate-200"
              >
                <CreditCard className="h-4 w-4" />
                <span>Stream A: Mandates &amp; Payments</span>
                <Badge variant="outline" className="ml-1 border-slate-700 bg-slate-800 text-slate-300 text-xs px-2 py-0.5 font-mono font-bold">
                  {countA}
                </Badge>
              </TabsTrigger>

              <TabsTrigger
                value="B"
                className="data-[state=active]:bg-amber-600 data-[state=active]:text-white data-[state=active]:shadow-md data-[state=active]:border-amber-400/40 text-xs sm:text-sm font-semibold gap-2.5 px-5 py-2.5 rounded-xl transition-all text-slate-400 hover:text-slate-200"
              >
                <Building2 className="h-4 w-4" />
                <span>Stream B: MSMED B2B Receivables</span>
                <Badge variant="outline" className="ml-1 border-slate-700 bg-slate-800 text-slate-300 text-xs px-2 py-0.5 font-mono font-bold">
                  {countB}
                </Badge>
              </TabsTrigger>

              <TabsTrigger
                value="C"
                className="data-[state=active]:bg-indigo-600 data-[state=active]:text-white data-[state=active]:shadow-md data-[state=active]:border-indigo-400/40 text-xs sm:text-sm font-semibold gap-2.5 px-5 py-2.5 rounded-xl transition-all text-slate-400 hover:text-slate-200"
              >
                <ShoppingCart className="h-4 w-4" />
                <span>Stream C: Abandoned Checkout</span>
                <Badge variant="outline" className="ml-1 border-slate-700 bg-slate-800 text-slate-300 text-xs px-2 py-0.5 font-mono font-bold">
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
      <footer className="mt-auto border-t border-slate-800/80 bg-slate-950/80 px-6 lg:px-12 py-6 text-sm text-slate-400 font-medium">
        <div className="mx-auto flex max-w-[1720px] flex-col sm:flex-row items-center justify-between gap-4">
          <p>
            &copy; 2026 RazorShield &bull; Razorpay AI Buildathon Track 03
          </p>
          <p className="flex items-center gap-2 text-slate-300">
            <BadgeCheck className="h-5 w-5 text-blue-400" />
            <span>Real Razorpay Sandbox API Verified &bull; Zero Gateway Mock Responses</span>
          </p>
        </div>
      </footer>
    </div>
  );
}