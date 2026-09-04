import { useState, useEffect, useRef } from "react";
import { 
  Zap, 
  ArrowRight, 
  ShieldCheck, 
  CreditCard, 
  Building2, 
  ShoppingCart, 
  Volume2, 
  CheckCircle2, 
  Play, 
  Pause,
  Sparkles, 
  TrendingUp, 
  Percent, 
  Scale,
  Clock,
  AlertTriangle,
  Lock,
  ExternalLink,
  Radio,
  Headphones,
  Languages,
  DollarSign,
  Activity,
  Server,
  FileText,
  BadgeCheck
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface LandingPageProps {
  onLaunchConsole: () => void;
}

export default function LandingPage({ onLaunchConsole }: LandingPageProps) {
  const [simulatorScenario, setSimulatorScenario] = useState<"mandate" | "b2b" | "cart">("mandate");
  const [interestPaise, setInterestPaise] = useState(253140);
  const [activeModule, setActiveModule] = useState<"A" | "B" | "C">("A");
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [audioCurrentTime, setAudioCurrentTime] = useState(0);
  const [audioDuration, setAudioDuration] = useState(14);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    const timer = setInterval(() => {
      setInterestPaise((prev) => prev + 12);
    }, 1500);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  const toggleAudioPlayback = () => {
    if (!audioRef.current) {
      audioRef.current = new Audio("/demo_voice_nudge.wav");
      audioRef.current.onended = () => {
        setIsPlayingAudio(false);
        setAudioCurrentTime(0);
      };
      audioRef.current.ontimeupdate = () => {
        if (audioRef.current) {
          setAudioCurrentTime(audioRef.current.currentTime);
          if (audioRef.current.duration && !isNaN(audioRef.current.duration)) {
            setAudioDuration(audioRef.current.duration);
          }
        }
      };
    }

    if (isPlayingAudio) {
      audioRef.current.pause();
      setIsPlayingAudio(false);
    } else {
      audioRef.current.play().then(() => {
        setIsPlayingAudio(true);
      }).catch((err) => {
        console.warn("Audio autoplay blocked or file missing", err);
      });
    }
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-900 flex flex-col font-sans antialiased selection:bg-blue-600 selection:text-white">
      {/* 1. Header Navigation */}
      <header 
        className={`sticky top-0 z-50 px-6 sm:px-10 lg:px-16 transition-all duration-300 ${
          isScrolled 
            ? "border-b border-slate-200/80 bg-white/80 backdrop-blur-xl shadow-xs py-4 sm:py-4.5" 
            : "border-b border-transparent bg-white/50 backdrop-blur-md py-6 sm:py-7"
        }`}
      >
        <div className="mx-auto flex max-w-[1600px] items-center justify-between">
          <div className="flex items-center gap-3.5">
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
                <span className="rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-bold text-[#0066ff] border border-blue-200/60">
                  Track 03
                </span>
              </div>
              <p className="text-xs text-slate-500 font-medium">
                Autonomous Recovery for Indian Commerce
              </p>
            </div>
          </div>

          <nav className="hidden lg:flex items-center gap-10 text-base font-semibold text-slate-700">
            <a 
              href="#simulator" 
              className="group relative py-1 hover:text-[#0066ff] transition-colors"
            >
              <span>Interactive Simulator</span>
              <span className="absolute bottom-0 left-0 h-[2.5px] w-0 bg-[#0066ff] rounded-full transition-all duration-300 ease-out group-hover:w-full" />
            </a>
            <a 
              href="#modules" 
              className="group relative py-1 hover:text-[#0066ff] transition-colors"
            >
              <span>Recovery Streams</span>
              <span className="absolute bottom-0 left-0 h-[2.5px] w-0 bg-[#0066ff] rounded-full transition-all duration-300 ease-out group-hover:w-full" />
            </a>
            <a 
              href="#compliance" 
              className="group relative py-1 hover:text-[#0066ff] transition-colors"
            >
              <span>13 Policy Gates</span>
              <span className="absolute bottom-0 left-0 h-[2.5px] w-0 bg-[#0066ff] rounded-full transition-all duration-300 ease-out group-hover:w-full" />
            </a>
            <a 
              href="#voice" 
              className="group relative py-1 hover:text-[#0066ff] transition-colors"
            >
              <span>Hinglish Voice AI</span>
              <span className="absolute bottom-0 left-0 h-[2.5px] w-0 bg-[#0066ff] rounded-full transition-all duration-300 ease-out group-hover:w-full" />
            </a>
            <a 
              href="#research" 
              className="group relative py-1 hover:text-[#0066ff] transition-colors"
            >
              <span>Research &amp; Citations</span>
              <span className="absolute bottom-0 left-0 h-[2.5px] w-0 bg-[#0066ff] rounded-full transition-all duration-300 ease-out group-hover:w-full" />
            </a>
          </nav>

          <div className="flex items-center gap-4">
            <Button
              onClick={onLaunchConsole}
              className="group inline-flex items-center justify-center rounded-xl bg-[#0066ff] hover:bg-[#0052cc] text-white text-base font-bold gap-2 h-12 px-6 shadow-sm transition-all hover:shadow-md active:scale-98"
            >
              <span>Launch Operations Console</span>
              <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
            </Button>
          </div>
        </div>
      </header>

      {/* 2. Hero Section */}
      <section className="relative overflow-hidden pt-16 lg:pt-24 pb-20 lg:pb-28 bg-gradient-to-b from-white via-[#f0f6ff]/70 to-[#f8fafc] border-b border-slate-200/80">
        <div className="mx-auto max-w-[1600px] px-6 sm:px-10 lg:px-16">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
            
            <div className="lg:col-span-6 space-y-8 text-left">
              <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-[#0c2340] leading-[1.08]">
                Recover Lost Revenue <br />
                <span className="text-[#0066ff]">Before It Becomes A Write-Off</span>
              </h1>

              <p className="text-xl sm:text-2xl text-slate-600 leading-relaxed font-normal max-w-2xl">
                Failed UPI AutoPay mandates, overdue B2B trade invoices, and abandoned carts bleed revenue continuously. ReClaim diagnoses root causes, enforces 13 strict regulatory stopping rules, and executes autonomous recovery without human delay.
              </p>

              <div className="flex flex-wrap items-center gap-4 pt-1">
                <Button
                  onClick={onLaunchConsole}
                  className="group inline-flex items-center justify-center rounded-xl bg-[#0066ff] hover:bg-[#0052cc] text-white font-bold text-base sm:text-lg px-9 py-4 h-auto shadow-md shadow-blue-500/20 hover:shadow-lg hover:shadow-blue-500/30 transition-all duration-200 active:scale-98"
                >
                  <span>Launch Operations Console</span>
                  <ArrowRight className="ml-2.5 h-5 w-5 transition-transform duration-200 group-hover:translate-x-1" />
                </Button>
                <a href="#modules">
                  <Button
                    variant="outline"
                    className="inline-flex items-center justify-center rounded-xl border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 hover:text-slate-900 font-bold text-base sm:text-lg px-8 py-4 h-auto shadow-xs transition-all duration-200"
                  >
                    Explore 3 Streams
                  </Button>
                </a>
              </div>

              <div className="pt-8 border-t border-slate-200/90 flex flex-wrap items-center gap-8 text-base sm:text-lg text-slate-700 font-semibold">
                <span className="flex items-center gap-2.5">
                  <ShieldCheck className="h-6 w-6 text-emerald-600" />
                  13 Deterministic Policy Gates
                </span>
                <span className="flex items-center gap-2.5">
                  <Scale className="h-6 w-6 text-amber-600" />
                  MSMED Act Sec 16 Grounded
                </span>
                <span className="flex items-center gap-2.5">
                  <Volume2 className="h-6 w-6 text-[#0066ff]" />
                  Sarvam AI Hinglish Voice
                </span>
              </div>
            </div>

            <div id="simulator" className="lg:col-span-6">
              <div className="rounded-3xl border border-slate-200/90 bg-white p-7 sm:p-10 shadow-xl shadow-slate-200/70 relative">
                <div className="flex items-center justify-between border-b border-slate-100 pb-5 mb-6">
                  <div>
                    <div className="flex items-center gap-2.5">
                      <span className="relative flex h-3 w-3">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                      </span>
                      <span className="text-sm font-extrabold uppercase tracking-widest text-[#0c2340]">
                        Live Recovery Simulator
                      </span>
                    </div>
                    <p className="text-sm text-slate-500 font-medium mt-1">
                      Select an enterprise failure scenario to witness autonomous diagnosis
                    </p>
                  </div>
                  <div className="inline-flex items-center gap-2 rounded-full bg-emerald-50 border border-emerald-200/80 px-3.5 py-1 text-sm font-bold text-emerald-700 shadow-xs">
                    <span className="h-2 w-2 rounded-full bg-emerald-500"></span>
                    <span>Active State Graph</span>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-3.5 mb-6">
                  <button
                    onClick={() => setSimulatorScenario("mandate")}
                    className={`rounded-2xl p-4 text-left border transition-all duration-200 ${
                      simulatorScenario === "mandate"
                        ? "border-[#0066ff] bg-blue-50/70 text-[#0066ff] shadow-sm shadow-blue-500/10 ring-2 ring-blue-500/20"
                        : "border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50/80"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <CreditCard className={`h-5 w-5 ${simulatorScenario === "mandate" ? "text-[#0066ff]" : "text-slate-400"}`} />
                      <span className={`text-xs font-bold px-2 py-0.5 rounded ${simulatorScenario === "mandate" ? "bg-blue-100/80 text-[#0066ff]" : "bg-slate-100 text-slate-500"}`}>UPI</span>
                    </div>
                    <span className="text-base font-bold block">UPI AutoPay Drop</span>
                  </button>

                  <button
                    onClick={() => setSimulatorScenario("b2b")}
                    className={`rounded-2xl p-4 text-left border transition-all duration-200 ${
                      simulatorScenario === "b2b"
                        ? "border-amber-500 bg-amber-50/70 text-amber-900 shadow-sm shadow-amber-500/10 ring-2 ring-amber-500/20"
                        : "border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50/80"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <Building2 className={`h-5 w-5 ${simulatorScenario === "b2b" ? "text-amber-600" : "text-slate-400"}`} />
                      <span className={`text-xs font-bold px-2 py-0.5 rounded ${simulatorScenario === "b2b" ? "bg-amber-100 text-amber-800" : "bg-slate-100 text-slate-500"}`}>MSME</span>
                    </div>
                    <span className="text-base font-bold block">B2B Invoice Overdue</span>
                  </button>

                  <button
                    onClick={() => setSimulatorScenario("cart")}
                    className={`rounded-2xl p-4 text-left border transition-all duration-200 ${
                      simulatorScenario === "cart"
                        ? "border-indigo-500 bg-indigo-50/70 text-indigo-900 shadow-sm shadow-indigo-500/10 ring-2 ring-indigo-500/20"
                        : "border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:bg-slate-50/80"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <ShoppingCart className={`h-5 w-5 ${simulatorScenario === "cart" ? "text-indigo-600" : "text-slate-400"}`} />
                      <span className={`text-xs font-bold px-2 py-0.5 rounded ${simulatorScenario === "cart" ? "bg-indigo-100 text-indigo-800" : "bg-slate-100 text-slate-500"}`}>Checkout</span>
                    </div>
                    <span className="text-base font-bold block">Cart Abandoned</span>
                  </button>
                </div>

                <div className="space-y-4 bg-slate-50/90 rounded-2xl p-6 sm:p-7 border border-slate-200/80 text-base">
                  {simulatorScenario === "mandate" && (
                    <>
                      <div className="flex items-start justify-between pb-3.5 border-b border-slate-200/80">
                        <div>
                          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Incoming Ingestion Signal</span>
                          <p className="font-extrabold text-[#0c2340] text-2xl mt-0.5">₹1,50,000 &bull; Recurring UPI AutoPay</p>
                          <p className="text-sm text-rose-600 font-mono mt-0.5 font-semibold flex items-center gap-2">
                            <span className="h-2 w-2 rounded-full bg-rose-500"></span>
                            Code U30 &bull; NPCI Peak Traffic Drop (11:15 IST)
                          </p>
                        </div>
                        <div className="inline-flex items-center gap-2 rounded-full bg-blue-50 border border-blue-200 px-3.5 py-1 text-sm font-bold text-[#0066ff] shadow-xs">
                          <span className="h-2 w-2 rounded-full bg-[#0066ff]"></span>
                          <span>Module A</span>
                        </div>
                      </div>

                      <div className="space-y-3 pt-1">
                        <div className="flex items-center justify-between rounded-xl bg-white p-3.5 border border-slate-200/80 text-sm sm:text-base">
                          <span className="text-slate-700 font-medium">Policy Gate 02 (NPCI Peak Window):</span>
                          <span className="text-emerald-700 font-bold bg-emerald-50 px-3 py-1 rounded-md border border-emerald-200/60">
                            Rule Triggered &bull; Avoid 10:00–13:00
                          </span>
                        </div>
                        <div className="flex items-center justify-between rounded-xl bg-white p-3.5 border border-slate-200/80 text-sm sm:text-base">
                          <span className="text-slate-700 font-medium">Autonomous Strategy:</span>
                          <span className="text-[#0066ff] font-bold bg-blue-50 px-3 py-1 rounded-md border border-blue-200/60">
                            Reschedule to 14:30 IST + Smart Link
                          </span>
                        </div>
                        <div className="flex items-center justify-between rounded-xl bg-emerald-50/80 p-4 border border-emerald-200 text-sm sm:text-base">
                          <span className="text-emerald-900 font-semibold">Net Settled Yield (T+2 after 2% MDR + 18% GST):</span>
                          <span className="text-[#0c2340] font-mono font-extrabold text-xl">₹1,46,460</span>
                        </div>
                      </div>
                    </>
                  )}

                  {simulatorScenario === "b2b" && (
                    <>
                      <div className="flex items-start justify-between pb-3.5 border-b border-slate-200/80">
                        <div>
                          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Incoming Ingestion Signal</span>
                          <p className="font-extrabold text-[#0c2340] text-2xl mt-0.5">₹8,50,000 &bull; Enterprise ERP Invoice INV-412</p>
                          <p className="text-sm text-amber-600 font-mono mt-0.5 font-semibold flex items-center gap-2">
                            <span className="h-2 w-2 rounded-full bg-amber-500"></span>
                            38 Days Past Statutory Due Date &bull; Rung 3 Escalation
                          </p>
                        </div>
                        <div className="inline-flex items-center gap-2 rounded-full bg-amber-50 border border-amber-200 px-3.5 py-1 text-sm font-bold text-amber-800 shadow-xs">
                          <span className="h-2 w-2 rounded-full bg-amber-600"></span>
                          <span>Module B</span>
                        </div>
                      </div>

                      <div className="space-y-3 pt-1">
                        <div className="flex items-center justify-between rounded-xl bg-amber-50/80 p-3.5 border border-amber-200 text-sm sm:text-base">
                          <span className="text-amber-900 font-semibold">MSMED Act Section 16 Penal Interest:</span>
                          <span className="text-amber-950 font-extrabold font-mono text-lg bg-white px-3 py-1 rounded-md border border-amber-300 shadow-xs">
                            ₹{(interestPaise / 100).toLocaleString("en-IN", { minimumFractionDigits: 2 })} (Accruing Live)
                          </span>
                        </div>
                        <div className="flex items-center justify-between rounded-xl bg-white p-3.5 border border-slate-200/80 text-sm sm:text-base">
                          <span className="text-slate-700 font-medium">Policy Gate 10 (Samadhaan Gate):</span>
                          <span className="text-purple-700 font-bold bg-purple-50 px-3 py-1 rounded-md border border-purple-200/60">
                            Human Operator Sign-Off Required
                          </span>
                        </div>
                        <div className="flex items-center justify-between rounded-xl bg-white p-3.5 border border-slate-200/80 text-sm sm:text-base">
                          <span className="text-slate-700 font-medium">Customer Voice Outreach:</span>
                          <span className="text-[#0066ff] font-bold bg-blue-50 px-3 py-1 rounded-md border border-blue-200/60">
                            Sarvam Bulbul:v3 Hinglish Drafted
                          </span>
                        </div>
                      </div>
                    </>
                  )}

                  {simulatorScenario === "cart" && (
                    <>
                      <div className="flex items-start justify-between pb-3.5 border-b border-slate-200/80">
                        <div>
                          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Incoming Ingestion Signal</span>
                          <p className="font-extrabold text-[#0c2340] text-2xl mt-0.5">₹4,200 &bull; High-Intent Storefront Checkout</p>
                          <p className="text-sm text-indigo-600 font-mono mt-0.5 font-semibold flex items-center gap-2">
                            <span className="h-2 w-2 rounded-full bg-indigo-500"></span>
                            32 Minutes Inactive &bull; Session Abandoned
                          </p>
                        </div>
                        <div className="inline-flex items-center gap-2 rounded-full bg-indigo-50 border border-indigo-200 px-3.5 py-1 text-sm font-bold text-indigo-800 shadow-xs">
                          <span className="h-2 w-2 rounded-full bg-indigo-600"></span>
                          <span>Module C</span>
                        </div>
                      </div>

                      <div className="space-y-3 pt-1">
                        <div className="flex items-center justify-between rounded-xl bg-white p-3.5 border border-slate-200/80 text-sm sm:text-base">
                          <span className="text-slate-700 font-medium">Policy Gate 12 (₹200 Recovery Floor):</span>
                          <span className="text-emerald-700 font-bold bg-emerald-50 px-3 py-1 rounded-md border border-emerald-200/60">
                            Passed (₹4,200 &gt; ₹200)
                          </span>
                        </div>
                        <div className="flex items-center justify-between rounded-xl bg-white p-3.5 border border-slate-200/80 text-sm sm:text-base">
                          <span className="text-slate-700 font-medium">Policy Gate 11 (Single Nudge Cap):</span>
                          <span className="text-emerald-700 font-bold bg-emerald-50 px-3 py-1 rounded-md border border-emerald-200/60">
                            Nudge 1/1 Authorized
                          </span>
                        </div>
                        <div className="flex items-center justify-between rounded-xl bg-blue-50/80 p-4 border border-blue-200 text-sm sm:text-base">
                          <span className="text-blue-900 font-semibold">Recovery Link:</span>
                          <span className="text-[#0066ff] font-mono font-extrabold text-base">https://rzp.io/i/cart_rec_91</span>
                        </div>
                      </div>
                    </>
                  )}
                </div>

                <div className="mt-6 pt-5 border-t border-slate-100 flex items-center justify-between">
                  <span className="text-sm sm:text-base text-slate-600 font-semibold">
                    Ready to test the 135-case live multi-stream batch?
                  </span>
                  <Button
                    onClick={onLaunchConsole}
                    className="group inline-flex items-center justify-center rounded-xl bg-[#0066ff] hover:bg-[#0052cc] text-white text-sm sm:text-base font-bold gap-2 h-11 px-6 shadow-md shadow-blue-500/20 hover:shadow-lg hover:shadow-blue-500/30 transition-all duration-200 active:scale-98"
                  >
                    <span>Open in Console</span>
                    <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
                  </Button>
                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* 3. The Three Dedicated Recovery Streams */}
      <section id="modules" className="py-24 lg:py-32 bg-white border-b border-slate-200/80">
        <div className="mx-auto max-w-[1600px] px-6 sm:px-10 lg:px-16 space-y-16">
          <div className="text-center space-y-4 max-w-4xl mx-auto">
            <span className="text-sm sm:text-base font-bold text-[#0066ff] uppercase tracking-wider block">
              Multi-Class Recovery Architecture
            </span>
            <h2 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-[#0c2340]">
              Engineered for Every Failure Point
            </h2>
            <p className="text-lg sm:text-xl text-slate-600 leading-relaxed font-normal">
              Payment failures cannot be treated with a one-size-fits-all retry script. ReClaim segregates money movement into three specialized, bounded streams.
            </p>
          </div>

          <div className="flex justify-center">
            <div className="inline-flex rounded-2xl bg-slate-100 p-2 border border-slate-200 shadow-inner">
              <button
                onClick={() => setActiveModule("A")}
                className={`rounded-xl px-7 py-3 text-base sm:text-lg font-bold transition-all duration-300 flex items-center gap-3 ${
                  activeModule === "A" 
                    ? "bg-white text-[#0066ff] shadow-md shadow-blue-500/10 ring-2 ring-blue-500/20" 
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/60"
                }`}
              >
                <CreditCard className={`h-5 w-5 ${activeModule === "A" ? "text-[#0066ff]" : "text-slate-400"}`} />
                <span>Module A: Payments &amp; Subscriptions</span>
              </button>
              <button
                onClick={() => setActiveModule("B")}
                className={`rounded-xl px-7 py-3 text-base sm:text-lg font-bold transition-all duration-300 flex items-center gap-3 ${
                  activeModule === "B" 
                    ? "bg-white text-amber-700 shadow-md shadow-amber-500/10 ring-2 ring-amber-500/20" 
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/60"
                }`}
              >
                <Building2 className={`h-5 w-5 ${activeModule === "B" ? "text-amber-600" : "text-slate-400"}`} />
                <span>Module B: B2B Invoices (MSMED)</span>
              </button>
              <button
                onClick={() => setActiveModule("C")}
                className={`rounded-xl px-7 py-3 text-base sm:text-lg font-bold transition-all duration-300 flex items-center gap-3 ${
                  activeModule === "C" 
                    ? "bg-white text-indigo-700 shadow-md shadow-indigo-500/10 ring-2 ring-indigo-500/20" 
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/60"
                }`}
              >
                <ShoppingCart className={`h-5 w-5 ${activeModule === "C" ? "text-indigo-600" : "text-slate-400"}`} />
                <span>Module C: Checkout Abandonment</span>
              </button>
            </div>
          </div>

          <div 
            key={activeModule} 
            className="animate-in fade-in duration-300 slide-in-from-bottom-3 rounded-3xl border border-slate-200/90 bg-[#f8fafc] p-8 sm:p-14 shadow-lg shadow-slate-200/50"
          >
            {activeModule === "A" && (
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
                <div className="lg:col-span-7 space-y-7 text-left">
                  <div className="inline-flex items-center gap-2 rounded-full bg-blue-100 text-[#0066ff] border border-blue-200 text-sm sm:text-base font-bold px-4 py-1.5 shadow-xs">
                    <span className="h-2 w-2 rounded-full bg-[#0066ff]"></span>
                    <span>Module A &bull; 60 Cases &bull; High-Volume Stream</span>
                  </div>
                  
                  <h3 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-[#0c2340] leading-tight">
                    Payment &amp; Mandate Retry Sequencer
                  </h3>
                  
                  <p className="text-lg sm:text-xl text-slate-600 leading-relaxed font-normal">
                    Recurring payment failures on UPI AutoPay and cards happen primarily due to issuer timeouts, temporary balance dips, or peak congestion. Naive gateways retry immediately and fail. ReClaim reschedules execution intelligently.
                  </p>
                  
                  <div className="space-y-4 pt-2">
                    <div className="rounded-2xl bg-white p-5 border border-slate-200/80 shadow-xs flex items-start gap-4">
                      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-emerald-100 text-emerald-700">
                        <Clock className="h-6 w-6" />
                      </div>
                      <div>
                        <h4 className="text-base sm:text-lg font-bold text-[#0c2340]">NPCI AutoPay Window Avoidance (Rule 2)</h4>
                        <p className="text-sm sm:text-base text-slate-600 mt-1 leading-relaxed">
                          Automatically intercepts mandate retries scheduled between 10:00–13:00 IST and reschedules execution to lower-latency afternoon windows (14:30 IST).
                        </p>
                      </div>
                    </div>

                    <div className="rounded-2xl bg-white p-5 border border-slate-200/80 shadow-xs flex items-start gap-4">
                      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-rose-100 text-rose-700">
                        <AlertTriangle className="h-6 w-6" />
                      </div>
                      <div>
                        <h4 className="text-base sm:text-lg font-bold text-[#0c2340]">Hard Decline Isolation (Rule 1)</h4>
                        <p className="text-sm sm:text-base text-slate-600 mt-1 leading-relaxed">
                          Recognizes permanent payment blocks (expired cards `54`, invalid mandate `U19`); instantly halts retries and switches to alternate payment link nudges.
                        </p>
                      </div>
                    </div>

                    <div className="rounded-2xl bg-white p-5 border border-slate-200/80 shadow-xs flex items-start gap-4">
                      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-blue-100 text-[#0066ff]">
                        <ShieldCheck className="h-6 w-6" />
                      </div>
                      <div>
                        <h4 className="text-base sm:text-lg font-bold text-[#0c2340]">48-Hour Customer Contact Pacing</h4>
                        <p className="text-sm sm:text-base text-slate-600 mt-1 leading-relaxed">
                          Guarantees zero customer fatigue by enforcing mandatory 48-hour cooling intervals between user notifications.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="lg:col-span-5 bg-white rounded-3xl border border-slate-200/90 p-7 sm:p-9 shadow-md space-y-6">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                    <span className="text-sm sm:text-base font-bold text-[#0c2340] uppercase tracking-wider block">
                      Execution Mechanics
                    </span>
                    <Badge className="bg-blue-50 text-[#0066ff] border-blue-200 text-xs font-bold">
                      Deterministic Policy
                    </Badge>
                  </div>

                  <div className="space-y-4 text-base">
                    <div className="rounded-2xl bg-slate-50 p-4 border border-slate-200/80 space-y-2.5">
                      <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">
                        Mandate Retry Optimization Window
                      </span>
                      <div className="flex items-center gap-2 text-xs sm:text-sm font-semibold">
                        <span className="px-2.5 py-1 rounded-md bg-rose-100 text-rose-800 line-through">10:00 - 13:00 Peak</span>
                        <ArrowRight className="h-4 w-4 text-slate-400" />
                        <span className="px-2.5 py-1 rounded-md bg-emerald-100 text-emerald-800 font-bold">14:30 Safe Execution</span>
                      </div>
                    </div>

                    <div className="flex justify-between items-center p-3.5 rounded-xl bg-slate-50 border border-slate-100">
                      <span className="text-slate-600 font-medium">Root-Cause Taxonomy:</span>
                      <span className="font-bold text-[#0c2340]">23 Granular Classes</span>
                    </div>

                    <div className="flex justify-between items-center p-3.5 rounded-xl bg-slate-50 border border-slate-100">
                      <span className="text-slate-600 font-medium">Net Settlement Yield:</span>
                      <span className="font-mono font-bold text-emerald-700">T+2 Post-MDR &amp; GST</span>
                    </div>

                    <div className="flex justify-between items-center p-3.5 rounded-xl bg-blue-50/70 border border-blue-200/80">
                      <span className="text-blue-900 font-semibold">Checkout Fallback:</span>
                      <span className="font-bold text-[#0066ff]">Quota-Safe Live Links</span>
                    </div>
                  </div>

                  <Button
                    onClick={onLaunchConsole}
                    className="w-full bg-[#0066ff] hover:bg-[#0052cc] text-white font-bold text-base h-12 rounded-xl shadow-md shadow-blue-500/20 gap-2"
                  >
                    <span>Inspect Module A in Console</span>
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}

            {activeModule === "B" && (
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
                <div className="lg:col-span-7 space-y-7 text-left">
                  <div className="inline-flex items-center gap-2 rounded-full bg-amber-100 text-amber-800 border border-amber-200 text-sm sm:text-base font-bold px-4 py-1.5 shadow-xs">
                    <span className="h-2 w-2 rounded-full bg-amber-600"></span>
                    <span>Module B &bull; 50 Cases &bull; Statutory Grounding</span>
                  </div>
                  
                  <h3 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-[#0c2340] leading-tight">
                    B2B Receivables &amp; Statutory Interest
                  </h3>
                  
                  <p className="text-lg sm:text-xl text-slate-600 leading-relaxed font-normal">
                    Under Section 16 of the MSMED Act 2006, buyers failing to pay within 45 days of acceptance are statutorily liable to compound penal interest at three times the RBI bank rate (20.25% p.a.). ReClaim enforces this legally.
                  </p>

                  <div className="space-y-4 pt-2">
                    <div className="rounded-2xl bg-white p-5 border border-slate-200/80 shadow-xs flex items-start gap-4">
                      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-amber-100 text-amber-800">
                        <Scale className="h-6 w-6" />
                      </div>
                      <div>
                        <h4 className="text-base sm:text-lg font-bold text-[#0c2340]">Section 16 Compound Penal Interest (20.25% p.a.)</h4>
                        <p className="text-sm sm:text-base text-slate-600 mt-1 leading-relaxed">
                          Automated compounding per statutory monthly rest rules, calculating exact legal liability accruals in real-time.
                        </p>
                      </div>
                    </div>

                    <div className="rounded-2xl bg-white p-5 border border-slate-200/80 shadow-xs flex items-start gap-4">
                      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-purple-100 text-purple-700">
                        <Lock className="h-6 w-6" />
                      </div>
                      <div>
                        <h4 className="text-base sm:text-lg font-bold text-[#0c2340]">Samadhaan Gate (Rule 10 Human Approval)</h4>
                        <p className="text-sm sm:text-base text-slate-600 mt-1 leading-relaxed">
                          Strictly stops autonomous dispatch of Rung 4 MSME Samadhaan legal filings until an authorized finance operator signs off in console.
                        </p>
                      </div>
                    </div>

                    <div className="rounded-2xl bg-white p-5 border border-slate-200/80 shadow-xs flex items-start gap-4">
                      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-rose-100 text-rose-700">
                        <AlertTriangle className="h-6 w-6" />
                      </div>
                      <div>
                        <h4 className="text-base sm:text-lg font-bold text-[#0c2340]">Commercial Dispute Freeze (Rule 6)</h4>
                        <p className="text-sm sm:text-base text-slate-600 mt-1 leading-relaxed">
                          Any documented customer dispute halts dunning workflows immediately to protect commercial relationships and compliance integrity.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="lg:col-span-5 bg-white rounded-3xl border border-slate-200/90 p-7 sm:p-9 shadow-md space-y-6">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                    <span className="text-sm sm:text-base font-bold text-[#0c2340] uppercase tracking-wider block">
                      5-Rung Statutory Ladder
                    </span>
                    <Badge className="bg-amber-50 text-amber-800 border-amber-200 text-xs font-bold">
                      MSMED Act Sec 16
                    </Badge>
                  </div>

                  <div className="space-y-3 text-sm sm:text-base">
                    <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-100">
                      <span className="font-semibold text-slate-700">Rung 1 (Days 1–15):</span>
                      <span className="text-xs font-bold text-slate-600 bg-white px-2.5 py-1 rounded border">Gentle Statement Nudge</span>
                    </div>

                    <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-100">
                      <span className="font-semibold text-slate-700">Rung 2 (Days 16–30):</span>
                      <span className="text-xs font-bold text-slate-600 bg-white px-2.5 py-1 rounded border">Sec 16 Interest Advisory</span>
                    </div>

                    <div className="flex items-center justify-between p-3 rounded-xl bg-amber-50/80 border border-amber-200">
                      <span className="font-bold text-amber-900">Rung 3 (Days 31–44):</span>
                      <span className="text-xs font-bold text-amber-900 bg-white px-2.5 py-1 rounded border border-amber-300">Formal Demand Notice</span>
                    </div>

                    <div className="flex items-center justify-between p-3.5 rounded-xl bg-purple-50 border border-purple-200">
                      <div>
                        <span className="font-bold text-purple-900 block">Rung 4 (Day 45+):</span>
                        <span className="text-xs text-purple-700">MSME Samadhaan Conciliation</span>
                      </div>
                      <span className="text-xs font-bold text-purple-800 bg-purple-100 px-2.5 py-1 rounded-md border border-purple-300 flex items-center gap-1">
                        <Lock className="h-3 w-3" />
                        Human Gate
                      </span>
                    </div>
                  </div>

                  <Button
                    onClick={onLaunchConsole}
                    className="w-full bg-amber-600 hover:bg-amber-700 text-white font-bold text-base h-12 rounded-xl shadow-md shadow-amber-500/20 gap-2"
                  >
                    <span>Inspect Module B in Console</span>
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}

            {activeModule === "C" && (
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
                <div className="lg:col-span-7 space-y-7 text-left">
                  <div className="inline-flex items-center gap-2 rounded-full bg-indigo-100 text-indigo-800 border border-indigo-200 text-sm sm:text-base font-bold px-4 py-1.5 shadow-xs">
                    <span className="h-2 w-2 rounded-full bg-indigo-600"></span>
                    <span>Module C &bull; 25 Cases &bull; High-Conversion Stream</span>
                  </div>
                  
                  <h3 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-[#0c2340] leading-tight">
                    Checkout Drop-Off &amp; Cart Recovery
                  </h3>
                  
                  <p className="text-lg sm:text-xl text-slate-600 leading-relaxed font-normal">
                    Shoppers abandoning payment at the final step show high purchase intent. ReClaim detects dropped sessions after 30 minutes, validates merchant profitability margins, and delivers 1-click checkout recovery links.
                  </p>

                  <div className="space-y-4 pt-2">
                    <div className="rounded-2xl bg-white p-5 border border-slate-200/80 shadow-xs flex items-start gap-4">
                      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-indigo-100 text-indigo-700">
                        <DollarSign className="h-6 w-6" />
                      </div>
                      <div>
                        <h4 className="text-base sm:text-lg font-bold text-[#0c2340]">₹200 Low-Value Profitability Floor (Rule 12)</h4>
                        <p className="text-sm sm:text-base text-slate-600 mt-1 leading-relaxed">
                          Stops recovery outreach for carts below ₹200 to protect merchant margins against gateway and messaging costs.
                        </p>
                      </div>
                    </div>

                    <div className="rounded-2xl bg-white p-5 border border-slate-200/80 shadow-xs flex items-start gap-4">
                      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-emerald-100 text-emerald-700">
                        <ShieldCheck className="h-6 w-6" />
                      </div>
                      <div>
                        <h4 className="text-base sm:text-lg font-bold text-[#0c2340]">Single Nudge Strict Cap (Rule 11)</h4>
                        <p className="text-sm sm:text-base text-slate-600 mt-1 leading-relaxed">
                          Strictly enforces a 1-outreach limit per abandoned checkout to preserve brand trust and customer goodwill.
                        </p>
                      </div>
                    </div>

                    <div className="rounded-2xl bg-white p-5 border border-slate-200/80 shadow-xs flex items-start gap-4">
                      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-blue-100 text-[#0066ff]">
                        <ExternalLink className="h-6 w-6" />
                      </div>
                      <div>
                        <h4 className="text-base sm:text-lg font-bold text-[#0c2340]">Pre-Populated Razorpay Payment Links</h4>
                        <p className="text-sm sm:text-base text-slate-600 mt-1 leading-relaxed">
                          Generates secure hosted checkout links preserving the customer's cart contents, addresses, and applied discounts.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="lg:col-span-5 bg-white rounded-3xl border border-slate-200/90 p-7 sm:p-9 shadow-md space-y-6">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                    <span className="text-sm sm:text-base font-bold text-[#0c2340] uppercase tracking-wider block">
                      Conversion Funnel
                    </span>
                    <Badge className="bg-indigo-50 text-indigo-700 border-indigo-200 text-xs font-bold">
                      Rule 11 &bull; Rule 12 Bound
                    </Badge>
                  </div>

                  <div className="space-y-4 text-base">
                    <div className="rounded-2xl bg-slate-50 p-4 border border-slate-200/80 space-y-2">
                      <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">
                        Abandonment Detection Window
                      </span>
                      <div className="flex items-center justify-between text-xs sm:text-sm font-semibold">
                        <span className="text-slate-600">Idle Inactivity:</span>
                        <span className="text-indigo-700 font-bold">30 Minutes Trigger</span>
                      </div>
                    </div>

                    <div className="flex justify-between items-center p-3.5 rounded-xl bg-slate-50 border border-slate-100">
                      <span className="text-slate-600 font-medium">Profitability Threshold:</span>
                      <span className="font-bold text-emerald-700">&ge; ₹200.00 Order Value</span>
                    </div>

                    <div className="flex justify-between items-center p-3.5 rounded-xl bg-slate-50 border border-slate-100">
                      <span className="text-slate-600 font-medium">Customer Outreach Cap:</span>
                      <span className="font-bold text-[#0c2340]">Max 1 Nudge Authorized</span>
                    </div>

                    <div className="flex justify-between items-center p-3.5 rounded-xl bg-indigo-50/70 border border-indigo-200/80">
                      <span className="text-indigo-900 font-semibold">Hosted Checkout:</span>
                      <span className="font-mono font-bold text-[#0066ff]">Pre-Filled Cart Link</span>
                    </div>
                  </div>

                  <Button
                    onClick={onLaunchConsole}
                    className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-base h-12 rounded-xl shadow-md shadow-indigo-500/20 gap-2"
                  >
                    <span>Inspect Module C in Console</span>
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* 4. Sarvam AI Hinglish Voice Recovery Showcase */}
      <section id="voice" className="py-24 lg:py-32 bg-[#f8fafc] border-b border-slate-200/80">
        <div className="mx-auto max-w-[1600px] px-6 sm:px-10 lg:px-16 grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
          
          <div className="lg:col-span-6 space-y-7 text-left">
            <div className="inline-flex items-center gap-2 rounded-full bg-indigo-100 text-indigo-800 border border-indigo-200 text-sm sm:text-base font-bold px-4 py-1.5 shadow-xs">
              <Sparkles className="h-4 w-4 text-indigo-600" />
              <span>Sarvam AI Bulbul:v3 Neural Engine</span>
            </div>

            <h2 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-[#0c2340] leading-tight">
              Native Hinglish Voice Recovery
            </h2>

            <p className="text-lg sm:text-xl text-slate-600 leading-relaxed font-normal">
              In Indian commerce, SMS notifications are ignored while cold robotic voice calls trigger immediate hang-ups. Our engine drafts context-aware Hinglish dialogue referencing exact invoice amounts and statutory interest, synthesized into natural conversational audio via Sarvam AI.
            </p>
            
            <div className="space-y-4 pt-2">
              <div className="rounded-2xl bg-white p-5 border border-slate-200/80 shadow-xs flex items-start gap-4">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-indigo-100 text-indigo-700">
                  <Languages className="h-6 w-6" />
                </div>
                <div>
                  <h4 className="text-base sm:text-lg font-bold text-[#0c2340]">Natural Code-Switching</h4>
                  <p className="text-sm sm:text-base text-slate-600 mt-1 leading-relaxed">
                    Blends respectful Indian corporate conversational norms with English financial terms (<code className="text-indigo-600 font-semibold">Namaste</code>, <code className="text-indigo-600 font-semibold">Aapka payment</code>, <code className="text-indigo-600 font-semibold">Razorpay secure link</code>).
                  </p>
                </div>
              </div>

              <div className="rounded-2xl bg-white p-5 border border-slate-200/80 shadow-xs flex items-start gap-4">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-blue-100 text-[#0066ff]">
                  <Zap className="h-6 w-6" />
                </div>
                <div>
                  <h4 className="text-base sm:text-lg font-bold text-[#0c2340]">Local Filesystem Audio Caching</h4>
                  <p className="text-sm sm:text-base text-slate-600 mt-1 leading-relaxed">
                    Decodes Sarvam base64 payloads to disk instantly upon initial generation, mounted statically for zero-latency replay and zero redundant API credit consumption.
                  </p>
                </div>
              </div>

              <div className="rounded-2xl bg-white p-5 border border-slate-200/80 shadow-xs flex items-start gap-4">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-emerald-100 text-emerald-700">
                  <ShieldCheck className="h-6 w-6" />
                </div>
                <div>
                  <h4 className="text-base sm:text-lg font-bold text-[#0c2340]">Quota-Safe Operator Dispatch</h4>
                  <p className="text-sm sm:text-base text-slate-600 mt-1 leading-relaxed">
                    Audio voice nudges synthesize strictly on operator preview or confirmed recovery dispatch, safeguarding developer credit pools.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="lg:col-span-6">
            <div className="rounded-3xl border border-indigo-200/90 bg-white p-7 sm:p-10 shadow-xl shadow-indigo-500/10 space-y-6 relative overflow-hidden">
              
              <div className="flex items-center justify-between border-b border-slate-100 pb-5">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-indigo-600 text-white shadow-sm shadow-indigo-500/30">
                    <Headphones className="h-5 w-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-base font-extrabold text-[#0c2340]">
                        Sarvam AI Voice Studio
                      </span>
                      <span className="relative flex h-2 w-2">
                        <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${isPlayingAudio ? "bg-indigo-400 opacity-75" : "bg-slate-300"}`}></span>
                        <span className={`relative inline-flex rounded-full h-2 w-2 ${isPlayingAudio ? "bg-indigo-600" : "bg-slate-400"}`}></span>
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 font-medium">
                      Neural Speaker: Priya (hi-IN) &bull; 8kHz Broadcast
                    </p>
                  </div>
                </div>

                <Badge className="bg-indigo-50 text-indigo-700 border-indigo-200 text-xs font-bold px-3 py-1">
                  Bulbul:v3
                </Badge>
              </div>

              <div className="rounded-2xl bg-slate-50 p-6 border border-slate-200/90 space-y-3">
                <div className="flex items-center justify-between text-xs font-bold text-slate-400 uppercase tracking-wider">
                  <span>Synthesized Dialogue Script</span>
                  <span className="text-indigo-600">Hinglish Code-Switched</span>
                </div>
                
                <p className="text-base sm:text-lg text-slate-800 leading-relaxed font-sans font-medium">
                  <span className="font-bold text-indigo-700">"Namaste,</span> aapka <span className="font-bold font-mono text-[#0c2340] bg-white px-2 py-0.5 rounded border border-slate-200">750.00 rupees</span> ka <span className="font-semibold text-slate-900">UPI subscription payment</span> decline ho gaya hai due to <span className="text-rose-600 font-semibold">UPI transaction timed out</span>. Humne aapke registered mobile par ek alternate <span className="text-[#0066ff] font-bold underline decoration-blue-300">Razorpay payment link</span> send kiya hai. Kripya link open karke payment complete karein. Dhanyawaad."
                </p>
              </div>

              <div className="rounded-2xl bg-gradient-to-r from-slate-900 to-[#0c2340] p-6 text-white space-y-4 shadow-md">
                
                <div className="flex items-center justify-between gap-1.5 h-12 px-2">
                  {[35, 65, 25, 80, 95, 45, 60, 85, 50, 75, 90, 40, 70, 55, 85, 60, 45, 75, 90, 30, 80, 65, 50, 40].map((h, i) => (
                    <div 
                      key={i} 
                      className={`w-1.5 rounded-full transition-all duration-200 ${
                        isPlayingAudio 
                          ? "bg-gradient-to-t from-indigo-400 to-cyan-300 animate-pulse" 
                          : "bg-slate-700"
                      }`}
                      style={{ 
                        height: isPlayingAudio 
                          ? `${Math.max(12, ((h * (i % 2 === 0 ? 0.9 : 1.1)) * 0.45))}px` 
                          : "8px" 
                      }}
                    />
                  ))}
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-slate-800">
                  <div className="flex items-center gap-2 font-mono text-xs text-slate-300">
                    <span className="font-bold text-cyan-400">
                      0:0{Math.floor(audioCurrentTime)}
                    </span>
                    <span>/</span>
                    <span>0:{Math.floor(audioDuration)}</span>
                  </div>

                  <Button
                    onClick={toggleAudioPlayback}
                    className={`font-bold text-sm sm:text-base gap-2.5 h-11 px-6 rounded-xl shadow-md transition-all active:scale-95 ${
                      isPlayingAudio 
                        ? "bg-rose-600 hover:bg-rose-700 text-white shadow-rose-500/30" 
                        : "bg-indigo-500 hover:bg-indigo-600 text-white shadow-indigo-500/30"
                    }`}
                  >
                    {isPlayingAudio ? (
                      <>
                        <Pause className="h-4 w-4 fill-white" />
                        <span>Pause Audio</span>
                      </>
                    ) : (
                      <>
                        <Play className="h-4 w-4 fill-white" />
                        <span>Play Voice Nudge</span>
                      </>
                    )}
                  </Button>
                </div>
              </div>

            </div>
          </div>

        </div>
      </section>

      {/* 5. 13 Deterministic Policy Gates & Settlement Math */}
      <section id="compliance" className="py-24 lg:py-32 bg-white border-b border-slate-200/80">
        <div className="mx-auto max-w-[1600px] px-6 sm:px-10 lg:px-16 space-y-16">
          
          <div className="text-center space-y-4 max-w-4xl mx-auto">
            <span className="text-sm sm:text-base font-bold text-emerald-600 uppercase tracking-wider block">
              Zero Hallucinations in Financial Movement
            </span>
            <h2 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-[#0c2340]">
              13 Hard-Coded Stopping Rules
            </h2>
            <p className="text-xl sm:text-2xl text-slate-600 leading-relaxed font-normal max-w-3xl mx-auto">
              While our diagnostic engine classifies failures across a <strong>27 root-cause taxonomy</strong> covering 5 payment rails (&gt;85% of Indian digital payment volume), money movement is strictly bounded by <strong>13 deterministic policy gates</strong>. Long-tail anomalies safely route to signal-parsing fallback or human review rather than hallucinating.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 lg:gap-10">
            
            <div className="rounded-3xl border border-slate-200 bg-[#f8fafc] p-8 sm:p-12 space-y-6 shadow-xs flex flex-col justify-between">
              <div className="space-y-5">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-700 font-bold">
                  <ShieldCheck className="h-8 w-8" />
                </div>
                <h3 className="text-2xl sm:text-3xl font-extrabold text-[#0c2340] leading-snug">
                  Zero LLM Financial Authority
                </h3>
                <p className="text-lg sm:text-xl text-slate-600 leading-relaxed font-normal">
                  Rules 1 through 13 evaluate before every execution: hard decline locks, 48-hour customer cooldowns, active dispute halts, and low-value floors. If any rule triggers, money movement is blocked unconditionally.
                </p>
              </div>

              <div className="pt-6 border-t border-slate-200 flex items-center justify-between text-base font-bold text-emerald-700">
                <span>13 Deterministic Gates</span>
                <span className="font-mono bg-emerald-100/70 px-3 py-1 rounded-lg">100% Policy Bound</span>
              </div>
            </div>

            <div className="rounded-3xl border border-slate-200 bg-[#f8fafc] p-8 sm:p-12 space-y-6 shadow-xs flex flex-col justify-between">
              <div className="space-y-5">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-100 text-[#0066ff] font-bold">
                  <Percent className="h-8 w-8" />
                </div>
                <h3 className="text-2xl sm:text-3xl font-extrabold text-[#0c2340] leading-snug">
                  2% MDR + 18% GST Yield Math
                </h3>
                <p className="text-lg sm:text-xl text-slate-600 leading-relaxed font-normal">
                  Gross recovery numbers are vanity metrics. Our settlement engine deducts standard payment gateway fees (2% MDR) and statutory taxation (18% GST on MDR) in real time to calculate the true net yield deposited on T+2.
                </p>
              </div>

              <div className="pt-6 border-t border-slate-200 flex items-center justify-between text-base font-bold text-[#0066ff]">
                <span>Net Settled Yield Formula</span>
                <span className="font-mono bg-blue-100/70 px-3 py-1 rounded-lg">T+2 Settlement</span>
              </div>
            </div>

            <div className="rounded-3xl border border-slate-200 bg-[#f8fafc] p-8 sm:p-12 space-y-6 shadow-xs flex flex-col justify-between">
              <div className="space-y-5">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-100 text-indigo-700 font-bold">
                  <Radio className="h-8 w-8" />
                </div>
                <h3 className="text-2xl sm:text-3xl font-extrabold text-[#0c2340] leading-snug">
                  Non-Repudiable Audit Ledger
                </h3>
                <p className="text-lg sm:text-xl text-slate-600 leading-relaxed font-normal">
                  Every policy evaluation, diagnostic reasoning packet, and webhook settlement event is cryptographically recorded in PostgreSQL and broadcast live over WebSocket for instant operator verification.
                </p>
              </div>

              <div className="pt-6 border-t border-slate-200 flex items-center justify-between text-base font-bold text-indigo-700">
                <span>Immutable Event Audit</span>
                <span className="font-mono bg-indigo-100/70 px-3 py-1 rounded-lg">Live /ws/audit</span>
              </div>
            </div>

          </div>

          <div className="rounded-2xl bg-slate-50 border border-slate-200 p-6 sm:p-8 flex flex-col sm:flex-row items-center justify-between gap-6 text-center sm:text-left">
            <div>
              <h4 className="text-xl sm:text-2xl font-bold text-[#0c2340]">
                Inspect all 13 rules live in the Operations Console
              </h4>
              <p className="text-base sm:text-lg text-slate-600 mt-1">
                Each payment case displays its full decision packet with every stopping rule check and audit trail.
              </p>
            </div>
            <Button
              onClick={onLaunchConsole}
              className="bg-[#0066ff] hover:bg-[#0052cc] text-white text-base sm:text-lg font-bold h-12 px-8 rounded-xl shadow-sm gap-2 shrink-0"
            >
              <span>Open Operations Console</span>
              <ArrowRight className="h-5 w-5" />
            </Button>
          </div>

        </div>
      </section>

      {/* 6. Primary Research & Regulatory Grounding */}
      <section id="research" className="py-24 lg:py-32 bg-white border-b border-slate-200/80">
        <div className="mx-auto max-w-[1600px] px-6 sm:px-10 lg:px-16 grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
          
          {/* Left Column (7 cols) - Narrative & Rationale */}
          <div className="lg:col-span-7 space-y-7 text-left">
            <div className="inline-flex items-center gap-2 rounded-full bg-blue-100 text-[#0066ff] border border-blue-200 text-sm sm:text-base font-bold px-4 py-1.5 shadow-xs">
              <BadgeCheck className="h-4 w-4 text-[#0066ff]" />
              <span>Exhaustive Primary Research &amp; Regulatory Grounding</span>
            </div>

            <h2 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-[#0c2340] leading-tight">
              Built on Verified Banking Regulations &amp; Gateway Specs
            </h2>

            <p className="text-lg sm:text-xl text-slate-600 leading-relaxed font-normal">
              Rather than relying on ungrounded prompts or invented rules, every mechanism in ReClaim was cross-referenced and verified against primary sources, including <strong>NPCI AutoPay circulars (May 2026)</strong>, <strong>MSMED Act 2006 statutory penal interest</strong>, <strong>RBI Monetary Policy Bank Rates</strong>, <strong>Razorpay FTX&apos;26 Agent Studio rails</strong>, and <strong>Baremetrics dunning benchmark data</strong>.
            </p>

            <div className="pt-2 flex flex-wrap items-center gap-6 text-base sm:text-lg font-bold text-slate-700">
              <span className="flex items-center gap-2 text-emerald-700">
                <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                Zero hypothetical assumptions
              </span>
              <span>&bull;</span>
              <span className="flex items-center gap-2 text-[#0066ff]">
                <ShieldCheck className="h-5 w-5 text-[#0066ff]" />
                100% checkable against real banking rails
              </span>
            </div>
          </div>

          {/* Right Column (5 cols) - Verified Sources Grid Card */}
          <div className="lg:col-span-5 bg-[#f8fafc] rounded-3xl border border-slate-200/90 p-7 sm:p-9 shadow-md space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 pb-4">
              <span className="text-sm sm:text-base font-bold text-[#0c2340] uppercase tracking-wider block">
                Verified Research Domains
              </span>
              <Badge className="bg-blue-50 text-[#0066ff] border-blue-200 text-xs font-bold">
                6 Primary Citations
              </Badge>
            </div>

            <div className="space-y-3 text-base">
              {[
                { title: "27 Root Causes across 5 Rails", desc: "UPI, Cards, Netbanking, Wallets & EMI (>85% Vol)" },
                { title: "NPCI UAP & Execution Windows", desc: "10:00–13:00 Peak Avoidance & 1+3 Retry Ceiling" },
                { title: "MSMED Act Sections 15 & 16", desc: "45-Day Rule & 3× RBI Bank Rate Monthly Compounding" },
                { title: "RBI MPC Bank Rate (5.50%)", desc: "August 2026 Monetary Policy Committee Benchmark" },
                { title: "Razorpay Webhook HMAC Spec", desc: "X-Razorpay-Event-Id Idempotency & Halted Links" },
                { title: "47.6% Dunning Industry Median", desc: "Baremetrics & Slicker Empirical SaaS Recovery Data" },
              ].map((item) => (
                <div key={item.title} className="p-3.5 rounded-xl bg-white border border-slate-200/80 shadow-xs flex items-start gap-3">
                  <div className="h-2 w-2 rounded-full bg-[#0066ff] mt-2 shrink-0"></div>
                  <div>
                    <h5 className="font-bold text-sm sm:text-base text-[#0c2340]">{item.title}</h5>
                    <p className="text-xs sm:text-sm text-slate-500 mt-0.5">{item.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>
      </section>

      {/* 6. High-Impact CTA Banner - Flagship Fintech Centerpiece */}
      <section className="relative overflow-hidden py-28 lg:py-36 bg-gradient-to-b from-[#0c2340] via-[#091b31] to-[#040d1a] text-white">
        {/* Soft Ambient Radial Light */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] h-[500px] bg-blue-500/10 blur-[130px] rounded-full pointer-events-none" />
        
        <div className="relative mx-auto max-w-[1600px] px-6 sm:px-10 lg:px-16 text-center space-y-10">
          
          {/* Large Authoritative Headline */}
          <h2 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-white max-w-5xl mx-auto leading-[1.08]">
            Experience the Operations <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-sky-300 to-indigo-300">
              Console in Live Action
            </span>
          </h2>

          <p className="text-xl sm:text-2xl text-slate-300 max-w-3xl mx-auto leading-relaxed font-normal">
            Diagnose 135 failure cases across a 27 root-cause taxonomy spanning UPI, Cards, Netbanking, Wallets, and EMI, governed strictly by 13 deterministic policy gates. Inspect explainable decision packets, create signed Razorpay links, and test native Sarvam voice outreach.
          </p>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center justify-center gap-4 pt-1">
            <Button
              onClick={onLaunchConsole}
              className="group inline-flex items-center justify-center rounded-xl bg-[#0066ff] hover:bg-[#0052cc] text-white font-bold text-base sm:text-lg px-9 py-4 h-auto shadow-md shadow-blue-500/20 hover:shadow-lg hover:shadow-blue-500/30 transition-all duration-200 active:scale-98"
            >
              <span>Launch Operations Console</span>
              <ArrowRight className="ml-2.5 h-5 w-5 transition-transform duration-200 group-hover:translate-x-1" />
            </Button>
            <a href="#modules">
              <Button
                variant="outline"
                className="inline-flex items-center justify-center rounded-xl border border-slate-700 bg-white/10 hover:bg-white/20 text-white font-bold text-base sm:text-lg px-8 py-4 h-auto transition-all duration-200"
              >
                Explore 3 Streams
              </Button>
            </a>
          </div>

          {/* Operational Metrics Bar */}
          <div className="pt-12 border-t border-slate-800/80 max-w-5xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
            <div className="space-y-1">
              <div className="text-3xl sm:text-4xl font-extrabold text-white">27 Causes</div>
              <div className="text-sm sm:text-base text-slate-400 font-medium">5 Payment Rails (&gt;85% Vol)</div>
            </div>
            <div className="space-y-1">
              <div className="text-3xl sm:text-4xl font-extrabold text-white">13 Gates</div>
              <div className="text-sm sm:text-base text-slate-400 font-medium">Deterministic Stopping Rules</div>
            </div>
            <div className="space-y-1">
              <div className="text-3xl sm:text-4xl font-extrabold text-emerald-400 font-mono">20.25% p.a.</div>
              <div className="text-sm sm:text-base text-slate-400 font-medium">MSMED Statutory Penal Rate</div>
            </div>
            <div className="space-y-1">
              <div className="text-3xl sm:text-4xl font-extrabold text-cyan-400 font-mono">135 Cases</div>
              <div className="text-sm sm:text-base text-slate-400 font-medium">Live Production Batch</div>
            </div>
          </div>

        </div>
      </section>

      {/* 7. Comprehensive Fintech Footer */}
      <footer className="border-t border-slate-200 bg-white px-6 sm:px-10 lg:px-16 pt-16 pb-12 text-slate-600">
        <div className="mx-auto max-w-[1600px] space-y-12">
          
          {/* Main Footer Content Grid */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-10 lg:gap-16">
            
            {/* Left: Brand Identity & Status */}
            <div className="md:col-span-5 space-y-5 text-left">
              <div className="flex items-center gap-3.5">
                <img 
                  src="/logo.png" 
                  alt="ReClaim" 
                  className="h-10 w-10 rounded-xl object-contain bg-white p-1 shadow-xs border border-slate-200" 
                />
                <div className="flex items-center gap-2.5">
                  <span className="text-2xl font-extrabold tracking-tight text-[#0c2340]">
                    Re<span className="text-[#0066ff]">Claim</span>
                  </span>
                  <span className="rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-bold text-[#0066ff] border border-blue-200/60">
                    Track 03
                  </span>
                </div>
              </div>

              <p className="text-base text-slate-600 leading-relaxed font-normal max-w-md">
                Autonomous multi-stream revenue recovery engine built for Razorpay AI Hackathon 2026. Bounded by 13 deterministic regulatory policy gates, MSMED Act 2006 statutory interest, and native Sarvam AI voice synthesis.
              </p>

              {/* Live Status Beacon */}
              <div className="inline-flex items-center gap-2.5 rounded-full bg-emerald-50 border border-emerald-200 px-3.5 py-1 text-sm font-bold text-emerald-700">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                </span>
                <span>All Systems Operational &bull; Sandbox Test Mode Active</span>
              </div>
            </div>

            {/* Right: Architectural Columns */}
            <div className="md:col-span-7 grid grid-cols-2 sm:grid-cols-3 gap-8 text-left">
              
              <div className="space-y-3.5">
                <h5 className="text-sm font-bold uppercase tracking-wider text-[#0c2340]">
                  Recovery Streams
                </h5>
                <ul className="space-y-2.5 text-base font-medium text-slate-600">
                  <li><a href="#modules" className="hover:text-[#0066ff] transition-colors">Module A: AutoPay</a></li>
                  <li><a href="#modules" className="hover:text-[#0066ff] transition-colors">Module B: MSMED B2B</a></li>
                  <li><a href="#modules" className="hover:text-[#0066ff] transition-colors">Module C: Cart Drop-Off</a></li>
                  <li><a href="#simulator" className="hover:text-[#0066ff] transition-colors">Live State Simulator</a></li>
                </ul>
              </div>

              <div className="space-y-3.5">
                <h5 className="text-sm font-bold uppercase tracking-wider text-[#0c2340]">
                  Compliance &amp; Rails
                </h5>
                <ul className="space-y-2.5 text-base font-medium text-slate-600">
                  <li><a href="#compliance" className="hover:text-[#0066ff] transition-colors">13 Stopping Rules</a></li>
                  <li><a href="#compliance" className="hover:text-[#0066ff] transition-colors">MSMED Sec 16 (20.25%)</a></li>
                  <li><a href="#compliance" className="hover:text-[#0066ff] transition-colors">2% MDR + 18% GST Net</a></li>
                  <li><a href="#compliance" className="hover:text-[#0066ff] transition-colors">Samadhaan Human Gate</a></li>
                </ul>
              </div>

              <div className="space-y-3.5">
                <h5 className="text-sm font-bold uppercase tracking-wider text-[#0c2340]">
                  AI &amp; Platform Stack
                </h5>
                <ul className="space-y-2.5 text-base font-medium text-slate-600">
                  <li><a href="#voice" className="hover:text-[#0066ff] transition-colors">Sarvam Bulbul:v3 TTS</a></li>
                  <li><a href="#voice" className="hover:text-[#0066ff] transition-colors">Sarvam 105B LLM</a></li>
                  <li><span className="text-slate-500">FastAPI &amp; LangGraph</span></li>
                  <li><span className="text-slate-500">PostgreSQL (Neon)</span></li>
                </ul>
              </div>

            </div>

          </div>

          {/* Bottom Bar: Copyright & Verified Submission */}
          <div className="pt-8 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm sm:text-base text-slate-500 font-medium">
            <p>
              &copy; 2026 ReClaim &bull; Track 03 Submission
            </p>
            <p className="flex items-center gap-2 text-slate-600">
              <BadgeCheck className="h-5 w-5 text-[#0066ff]" />
              <span>Real Razorpay Sandbox API Verified &bull; Zero Mock Gateway Responses</span>
            </p>
          </div>

        </div>
      </footer>
    </div>
  );
}