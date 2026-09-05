import { useState } from "react";
import { 
  FileText, 
  Sparkles, 
  AlertCircle, 
  Copy, 
  Check, 
  ShieldAlert, 
  ShieldCheck, 
  Loader2 
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface B2BNoticeDraftCardProps {
  invoiceId: string;
  invoice: any;
}

interface DraftResult {
  invoice_number: string;
  buyer_name: string;
  current_rung: number;
  rung_tone: string;
  days_overdue: number;
  principal_amount_paise: number;
  computed_interest_paise: number;
  statutory_basis: string;
  register: string;
  message_text: string;
  cites_interest_figure: boolean;
  cooldown_active?: boolean;
  cooldown_days_remaining?: number;
  days_since_contact?: number;
}

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export default function B2BNoticeDraftCard({ invoiceId, invoice }: B2BNoticeDraftCardProps) {
  const [register, setRegister] = useState<string>("standard business English");
  const [draftResult, setDraftResult] = useState<DraftResult | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const status = invoice?.status;
  const disputeFlag = Boolean(invoice?.dispute_flag);
  const currentRung = invoice?.current_rung ?? 0;

  let blockedReason: string | null = null;
  if (status === "paid") {
    blockedReason = "Invoice Settled: Principal and dues cleared in full. Outbound collection halted.";
  } else if (status === "written_off") {
    blockedReason = "Invoice Written Off: Marked as bad debt. Automated drafting terminated.";
  } else if (disputeFlag) {
    blockedReason = "Rule 6 (Dispute Immediate Halt): Active buyer dispute. Automated contact strictly prohibited.";
  } else if (currentRung === 0) {
    blockedReason = "Rung 0: Invoice is within credit terms. Statutory reminder is not yet due.";
  } else if (currentRung === 4 || status === "pending_human_approval") {
    blockedReason = "Rule 10: Rung 4 legal filing requires operator approval before notice generation.";
  }

  const handleDraft = async () => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetch(
        `${API_BASE}/api/cases/invoices/${invoiceId}/draft-reminder?register=${encodeURIComponent(register)}`,
        { method: "POST" }
      );
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Server error (${res.status})`);
      }
      const data: DraftResult = await res.json();
      setDraftResult(data);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to draft statutory notice");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopy = () => {
    if (!draftResult?.message_text) return;
    navigator.clipboard.writeText(draftResult.message_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5 sm:p-6 shadow-xl space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <span className="text-xs sm:text-sm font-black uppercase tracking-wider text-white flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-600/80 text-white border border-indigo-400/30 shadow-xs">
            <FileText className="h-4 w-4" />
          </div>
          B2B Statutory Notice Drafting (Gemini AI Engine)
        </span>
        <Badge variant="outline" className="border-indigo-500/30 bg-indigo-500/15 text-indigo-300 text-xs font-semibold px-2.5 py-0.5 rounded-full">
          MSMED Section 15-16
        </Badge>
      </div>

      {blockedReason ? (
        <div className="rounded-xl border border-rose-500/30 bg-rose-950/40 p-4 space-y-1.5">
          <div className="flex items-center gap-2 text-rose-300 font-bold text-xs sm:text-sm">
            <ShieldAlert className="h-4 w-4 text-rose-400 shrink-0" />
            <span>Policy Gate Enforced</span>
          </div>
          <p className="text-xs sm:text-sm text-rose-300/90 font-medium leading-relaxed">
            {blockedReason}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 text-xs sm:text-sm">
            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-semibold">Register / Tone:</span>
              <div className="inline-flex rounded-lg border border-slate-800 bg-slate-950/80 p-0.5">
                <button
                  type="button"
                  onClick={() => setRegister("standard business English")}
                  className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                    register === "standard business English"
                      ? "bg-blue-600 text-white shadow-md shadow-blue-500/25"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  Standard English
                </button>
                <button
                  type="button"
                  onClick={() => setRegister("Hinglish")}
                  className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                    register === "Hinglish"
                      ? "bg-blue-600 text-white shadow-md shadow-blue-500/25"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  Hinglish
                </button>
              </div>
            </div>

            <Button
              onClick={handleDraft}
              disabled={isLoading}
              className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-4 py-2 rounded-xl shadow-lg shadow-blue-500/25 flex items-center gap-2 cursor-pointer disabled:opacity-50"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  <span>Drafting with Gemini...</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-3.5 w-3.5" />
                  <span>Draft Statutory Notice</span>
                </>
              )}
            </Button>
          </div>

          {errorMsg && (
            <div className="rounded-xl border border-rose-500/30 bg-rose-950/40 p-3.5 flex items-center gap-2.5 text-rose-300 text-xs sm:text-sm font-medium">
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
              <span>{errorMsg}</span>
            </div>
          )}

          {draftResult && (
            <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-2.5 text-xs">
                <div className="flex items-center gap-2">
                  <Badge className="bg-slate-800 border border-slate-700 text-slate-200 text-2xs font-mono font-semibold px-2 py-0.5 rounded-md">
                    Rung {draftResult.current_rung}: {draftResult.rung_tone}
                  </Badge>
                  <span className="text-slate-400 font-medium">
                    Overdue: <strong className="text-white">{draftResult.days_overdue} days</strong>
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <Badge
                    variant="outline"
                    className={`text-2xs font-semibold px-2 py-0.5 rounded-full flex items-center gap-1 ${
                      draftResult.cites_interest_figure
                        ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
                        : "border-slate-700 bg-slate-800/80 text-slate-400"
                    }`}
                  >
                    <ShieldCheck className="h-3 w-3 text-emerald-400" />
                    Rule 9: Compound Interest Verified
                  </Badge>
                  <button
                    type="button"
                    onClick={handleCopy}
                    className="inline-flex items-center gap-1 text-slate-300 hover:text-white text-xs font-semibold bg-slate-800/80 border border-slate-700 rounded-md px-2.5 py-1 shadow-xs cursor-pointer transition-all"
                  >
                    {copied ? (
                      <>
                        <Check className="h-3 w-3 text-emerald-400" />
                        <span className="text-emerald-300">Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy className="h-3 w-3 text-slate-400" />
                        <span>Copy Text</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {draftResult.cooldown_active && (
                <div className="rounded-lg border border-amber-500/30 bg-amber-950/30 p-2.5 flex items-center justify-between text-2xs sm:text-xs text-amber-300 font-medium">
                  <div className="flex items-center gap-1.5">
                    <ShieldAlert className="h-3.5 w-3.5 text-amber-400 shrink-0" />
                    <span>
                      <strong>Rule 8 (contact_frequency_cap):</strong> Contacted {draftResult.days_since_contact ?? 0} days ago. 7-day cooldown active ({draftResult.cooldown_days_remaining}d remaining before dispatch).
                    </span>
                  </div>
                  <Badge variant="outline" className="border-amber-500/40 bg-amber-950/50 text-amber-300 text-[10px] font-semibold px-2 py-0.5 rounded-sm shrink-0">
                    Preview Only • Dispatch Paused
                  </Badge>
                </div>
              )}

              <div className="rounded-lg bg-slate-900/90 border border-slate-800 p-3.5 text-xs sm:text-sm text-slate-200 font-sans whitespace-pre-wrap leading-relaxed shadow-inner">
                {draftResult.message_text}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
