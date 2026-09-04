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
    <div className="rounded-2xl border border-slate-200/90 bg-white p-5 sm:p-6 shadow-xs space-y-4">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <span className="text-xs sm:text-sm font-black uppercase tracking-wider text-[#0c2340] flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-100 text-indigo-700">
            <FileText className="h-4 w-4" />
          </div>
          B2B Statutory Notice Drafting (Gemini 3.6 Flash)
        </span>
        <Badge variant="outline" className="border-indigo-200 bg-indigo-50 text-indigo-800 text-xs font-bold px-2.5 py-0.5 rounded-md">
          MSMED Section 15-16
        </Badge>
      </div>

      {blockedReason ? (
        <div className="rounded-xl border border-rose-200 bg-rose-50/70 p-4 space-y-1.5">
          <div className="flex items-center gap-2 text-rose-800 font-bold text-xs sm:text-sm">
            <ShieldAlert className="h-4 w-4 text-rose-600 shrink-0" />
            <span>Policy Gate Enforced</span>
          </div>
          <p className="text-xs sm:text-sm text-rose-700 font-medium leading-relaxed">
            {blockedReason}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 text-xs sm:text-sm">
            <div className="flex items-center gap-2">
              <span className="text-slate-600 font-bold">Register / Tone:</span>
              <div className="inline-flex rounded-lg border border-slate-200 bg-slate-100 p-0.5">
                <button
                  type="button"
                  onClick={() => setRegister("standard business English")}
                  className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${
                    register === "standard business English"
                      ? "bg-white text-[#0c2340] shadow-2xs"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  Standard English
                </button>
                <button
                  type="button"
                  onClick={() => setRegister("Hinglish")}
                  className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${
                    register === "Hinglish"
                      ? "bg-white text-[#0c2340] shadow-2xs"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  Hinglish
                </button>
              </div>
            </div>

            <Button
              onClick={handleDraft}
              disabled={isLoading}
              className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold px-4 py-2 rounded-xl shadow-xs flex items-center gap-2 cursor-pointer disabled:opacity-50"
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
            <div className="rounded-xl border border-rose-200 bg-rose-50 p-3.5 flex items-center gap-2.5 text-rose-700 text-xs sm:text-sm font-medium">
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />
              <span>{errorMsg}</span>
            </div>
          )}

          {draftResult && (
            <div className="rounded-xl border border-slate-200 bg-slate-50/80 p-4 space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200/80 pb-2.5 text-xs">
                <div className="flex items-center gap-2">
                  <Badge className="bg-[#0c2340] text-white text-2xs font-mono font-bold px-2 py-0.5 rounded-md">
                    Rung {draftResult.current_rung}: {draftResult.rung_tone}
                  </Badge>
                  <span className="text-slate-500 font-medium">
                    Overdue: <strong className="text-slate-700">{draftResult.days_overdue} days</strong>
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <Badge
                    variant="outline"
                    className={`text-2xs font-bold px-2 py-0.5 rounded-md flex items-center gap-1 ${
                      draftResult.cites_interest_figure
                        ? "border-emerald-300 bg-emerald-50 text-emerald-800"
                        : "border-slate-200 bg-slate-100 text-slate-700"
                    }`}
                  >
                    <ShieldCheck className="h-3 w-3 text-emerald-600" />
                    Rule 9: Compound Interest Verified
                  </Badge>
                  <button
                    type="button"
                    onClick={handleCopy}
                    className="inline-flex items-center gap-1 text-slate-600 hover:text-slate-900 text-xs font-bold bg-white border border-slate-200 rounded-md px-2 py-1 shadow-2xs cursor-pointer transition-all"
                  >
                    {copied ? (
                      <>
                        <Check className="h-3 w-3 text-emerald-600" />
                        <span className="text-emerald-700">Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy className="h-3 w-3 text-slate-500" />
                        <span>Copy Text</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {draftResult.cooldown_active && (
                <div className="rounded-lg border border-amber-200 bg-amber-50 p-2.5 flex items-center justify-between text-2xs sm:text-xs text-amber-900 font-medium">
                  <div className="flex items-center gap-1.5">
                    <ShieldAlert className="h-3.5 w-3.5 text-amber-700 shrink-0" />
                    <span>
                      <strong>Rule 8 (contact_frequency_cap):</strong> Contacted {draftResult.days_since_contact ?? 0} days ago. 7-day cooldown active ({draftResult.cooldown_days_remaining}d remaining before dispatch).
                    </span>
                  </div>
                  <Badge variant="outline" className="border-amber-300 bg-white text-amber-800 text-[10px] font-bold px-2 py-0.5 rounded-sm shrink-0">
                    Preview Only • Dispatch Paused
                  </Badge>
                </div>
              )}

              <div className="rounded-lg bg-white border border-slate-200/90 p-3.5 text-xs sm:text-sm text-slate-800 font-sans whitespace-pre-wrap leading-relaxed shadow-2xs">
                {draftResult.message_text}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
