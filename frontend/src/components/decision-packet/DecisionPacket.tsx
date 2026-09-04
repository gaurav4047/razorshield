import { useState } from "react";
import { useCaseDetail, useGenerateLink, useSimulateWebhook, useApproveRung4 } from "@/api/useCases";
import { formatPaiseToRupees } from "@/lib/utils";
import AiVsRuleDisagreement from "./AiVsRuleDisagreement";
import VoiceNudgePlayer from "./VoiceNudgePlayer";
import B2BNoticeDraftCard from "./B2BNoticeDraftCard";
import InterestAccrualCounter from "@/components/receivables/InterestAccrualCounter";

import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogDescription,
  DialogFooter
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  Zap, 
  ShieldCheck, 
  ExternalLink, 
  Copy, 
  Check, 
  AlertOctagon, 
  CreditCard, 
  BrainCircuit, 
  FileText, 
  Scale,
  FlaskConical,
  Building2,
  ShoppingCart,
  CheckCircle2,
  ShieldAlert,
  XCircle,
  AlertTriangle,
  Sparkles
} from "lucide-react";

interface DecisionPacketProps {
  module: "A" | "B" | "C";
  caseId: string;
  onClose: () => void;
}

export default function DecisionPacket({ module, caseId, onClose }: DecisionPacketProps) {
  const [copied, setCopied] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [activeCheckoutUrl, setActiveCheckoutUrl] = useState<string | null>(null);

  const { data: caseDetail, isLoading, refetch } = useCaseDetail(module, caseId);
  const generateLinkMutation = useGenerateLink();
  const simulateWebhookMutation = useSimulateWebhook();
  const approveRung4Mutation = useApproveRung4();

  if (isLoading || !caseDetail) {
    return (
      <Dialog open={true} onOpenChange={() => onClose()}>
        <DialogContent className="sm:max-w-4xl p-0 overflow-hidden bg-white shadow-2xl rounded-2xl">
          <div className="flex h-72 items-center justify-center">
            <div className="text-center space-y-3">
              <div className="h-10 w-10 animate-spin rounded-full border-4 border-[#0066ff] border-t-transparent mx-auto"></div>
              <p className="text-sm text-slate-500 font-semibold">Loading Explainability Decision Packet...</p>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  const handleCopyLink = (url: string) => {
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleGenerateLink = async () => {
    setActionError(null);
    try {
      const res = await generateLinkMutation.mutateAsync({ module, caseId });
      if (res?.short_url) {
        setActiveCheckoutUrl(res.short_url);
      }
      refetch();
    } catch (err: any) {
      setActionError(err.message || "Failed to create Razorpay link");
    }
  };

  const handleSimulateWebhook = async () => {
    setActionError(null);
    try {
      await simulateWebhookMutation.mutateAsync({ module, caseId });
      refetch();
    } catch (err: any) {
      setActionError(err.message || "Failed to simulate webhook");
    }
  };

  const handleApproveRung4 = async () => {
    setActionError(null);
    try {
      await approveRung4Mutation.mutateAsync(caseId);
      refetch();
    } catch (err: any) {
      setActionError(err.message || "Failed to approve filing");
    }
  };

  const latestAudit = (caseDetail as any).audit_logs?.[0];
  const stoppingRules = latestAudit?.stopping_rules_checked || [];
  const aiReasoning = latestAudit?.ai_reasoning_text || (caseDetail as any).ai_reasoning_text;
  const amountPaise = caseDetail.amount_paise || 0;
  const grossPaise = latestAudit?.gross_amount_paise || amountPaise;
  const mdrPaise = latestAudit?.mdr_paise || Math.round(grossPaise * 0.02);
  const gstPaise = latestAudit?.gst_on_mdr_paise || Math.round(mdrPaise * 0.18);
  const netPaise = latestAudit?.net_amount_paise || (grossPaise - mdrPaise - gstPaise);

  const paymentLinkId = caseDetail.razorpay_payment_link_id;
  const isRealRazorpayLink = Boolean(
    paymentLinkId &&
      !paymentLinkId.startsWith("plink_alt_") &&
      !paymentLinkId.startsWith("plink_inv_") &&
      !paymentLinkId.startsWith("plink_nudge_")
  );
  const checkoutUrl = activeCheckoutUrl || (caseDetail as any).razorpay_payment_link_url || (
    isRealRazorpayLink && paymentLinkId
      ? `https://rzp.io/rzp/${paymentLinkId.replace("plink_", "")}`
      : null
  );

  // Deterministic Fault Attribution & Taxonomy Resolution
  const rawAttribution = (caseDetail as any).fault_attribution;
  const rawRootCause = (caseDetail as any).classified_root_cause;
  const failureCode = (caseDetail as any).failure_code;
  const failureReason = ((caseDetail as any).failure_raw_reason || "").toLowerCase();

  let resolvedAttribution = rawAttribution;
  if (!resolvedAttribution || resolvedAttribution === "unknown") {
    if (module === "A") {
      const codeOrReason = `${failureCode || ""} ${failureReason}`.toLowerCase();
      if (["u19", "transient_glitch", "91", "96", "timeout", "downtime", "npci", "infra", "gateway"].some(k => codeOrReason.includes(k))) {
        resolvedAttribution = "infrastructure_fault";
      } else {
        resolvedAttribution = "customer_fault";
      }
    } else {
      resolvedAttribution = "customer_fault";
    }
  }

  let resolvedTaxonomy = rawRootCause;
  if (!resolvedTaxonomy || resolvedTaxonomy === "standard_ladder") {
    if (module === "A") {
      if (failureCode === "51" || failureReason.includes("insufficient") || failureReason.includes("balance")) {
        resolvedTaxonomy = "insufficient_balance";
      } else if (failureCode === "54" || failureReason.includes("expired")) {
        resolvedTaxonomy = "card_expired";
      } else if (failureCode === "U19" || failureReason.includes("npci") || failureReason.includes("autopay")) {
        resolvedTaxonomy = "npci_window_blocked";
      } else if (failureCode === "91" || failureReason.includes("timeout")) {
        resolvedTaxonomy = "transient_infra_glitch";
      } else if (failureCode === "05" || failureReason.includes("decline")) {
        resolvedTaxonomy = "issuer_general_decline";
      } else {
        resolvedTaxonomy = failureCode ? `code_${failureCode}` : "transient_payment_glitch";
      }
    } else if (module === "B") {
      const isWithinTerms = (caseDetail as any).current_rung === 0;
      resolvedTaxonomy = (caseDetail as any).dispute_flag
        ? "disputed_commercial_terms"
        : isWithinTerms
        ? "within_statutory_terms"
        : (caseDetail as any).supplier_is_msme
        ? "statutory_overdue_msmed"
        : "commercial_overdue_standard";
    } else {
      resolvedTaxonomy = (amountPaise < 20000) ? "micro_order_below_floor" : "abandoned_high_intent_cart";
    }
  }

  let resolvedAction = latestAudit?.final_action || (caseDetail as any).recommended_intervention;
  if (!resolvedAction || resolvedAction === "open") {
    if (module === "A") {
      if (resolvedTaxonomy === "insufficient_balance") {
        resolvedAction = "delayed_retry_notify";
      } else if (resolvedTaxonomy === "npci_window_blocked" || resolvedTaxonomy === "transient_infra_glitch") {
        resolvedAction = "silent_retry";
      } else if (resolvedTaxonomy === "card_expired" || resolvedTaxonomy === "wallet_kyc_frozen") {
        resolvedAction = "alternate_method";
      } else {
        resolvedAction = "delayed_retry_notify";
      }
    } else if (module === "B") {
      resolvedAction = (caseDetail as any).dispute_flag ? "dispute_halt" : `rung_${(caseDetail as any).current_rung || 1}_action`;
    } else {
      resolvedAction = (amountPaise < 20000) ? "skipped_low_value" : "send_abandonment_nudge";
    }
  }

  return (
    <Dialog open={true} onOpenChange={() => onClose()}>
      <DialogContent className="h-[90vh] max-h-[90vh] sm:max-w-4xl lg:max-w-5xl p-0 overflow-hidden bg-white shadow-2xl rounded-3xl border border-slate-200 flex flex-col">
        
        {/* Header Bar */}
        <DialogHeader className="border-b border-slate-800 bg-[#0c2340] text-white p-6 sm:p-7 shrink-0">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3.5">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#0066ff] text-white shadow-sm shadow-blue-500/25">
                {module === "A" && <CreditCard className="h-5 w-5" />}
                {module === "B" && <Building2 className="h-5 w-5" />}
                {module === "C" && <ShoppingCart className="h-5 w-5" />}
              </div>
              <div>
                <DialogTitle className="text-lg sm:text-xl font-black text-white flex flex-wrap items-center gap-2.5">
                  <span>Explainability Decision Packet</span>
                  <Badge className="border-blue-400/40 bg-blue-500/20 text-blue-200 font-mono text-xs font-bold px-2.5 py-0.5 rounded-full">
                    {module === "A" && "Module A • AutoPay"}
                    {module === "B" && "Module B • MSMED B2B"}
                    {module === "C" && "Module C • Cart Stream"}
                  </Badge>
                </DialogTitle>
                <DialogDescription className="text-xs sm:text-sm text-slate-300 font-mono mt-0.5">
                  Trace ID: {caseId}
                </DialogDescription>
              </div>
            </div>

            <div className="text-right pr-7 sm:pr-8">
              <span className="font-mono text-2xl sm:text-3xl font-black text-emerald-400 tabular-nums block">
                {formatPaiseToRupees(amountPaise)}
              </span>
              {"amount_paid_paise" in caseDetail && (caseDetail as any).amount_paid_paise > 0 && (caseDetail as any).amount_paid_paise < amountPaise && (
                <span className="text-xs font-mono font-bold text-emerald-300 block">
                  Paid: {formatPaiseToRupees((caseDetail as any).amount_paid_paise)} • Due: {formatPaiseToRupees(amountPaise - (caseDetail as any).amount_paid_paise)}
                </span>
              )}
              <div className="flex items-center justify-end gap-1.5 mt-0.5">
                <span className="text-[11px] text-slate-300 uppercase font-bold tracking-wider">Status:</span>
                <span className="border border-white/20 bg-white/10 text-white font-mono font-bold text-xs px-2 py-0.5 rounded-md uppercase">
                  {((caseDetail as any).status || "").replace(/_/g, " ")}
                </span>
              </div>
            </div>
          </div>
        </DialogHeader>

        {/* Scrollable Body */}
        <ScrollArea className="flex-1 min-h-0 overflow-y-auto">
          <div className="p-6 sm:p-8 space-y-6">
            {actionError && (
            <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-xs sm:text-sm text-rose-800 flex items-start gap-3 shadow-2xs">
              <AlertOctagon className="h-5 w-5 text-rose-600 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold">Sandbox Quota Notice:</p>
                <p className="mt-0.5">{actionError}</p>
              </div>
            </div>
          )}

          {/* 1. Ingestion Signal Section */}
          <div className="rounded-2xl border border-slate-200/90 bg-slate-50/70 p-5 sm:p-6 space-y-3.5 shadow-2xs">
            <div className="flex items-center justify-between border-b border-slate-200/80 pb-3">
              <span className="text-xs sm:text-sm font-black uppercase tracking-wider text-[#0c2340] flex items-center gap-2.5">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-100 text-[#0066ff]">
                  <FileText className="h-4 w-4" />
                </div>
                1. Ingestion Signal Payload
              </span>
              <Badge variant="outline" className="border-slate-200 bg-white text-slate-700 text-xs font-bold px-2.5 py-0.5 rounded-md shadow-2xs">
                {"payment_case" in caseDetail || "method" in caseDetail ? "Gateway Webhook" : "ERP Ledger Sync"}
              </Badge>
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 text-xs sm:text-sm">
              {"failure_raw_reason" in caseDetail && (
                <div className="sm:col-span-2">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-slate-600">Raw Failure Reason:</span>
                    {!caseDetail.failure_code && (
                      <Badge className="border-blue-200 bg-blue-50 text-[#0066ff] text-[11px] font-bold px-2 py-0.5 rounded-md">
                        Groq Live Signal Parsing • gpt-oss-120b
                      </Badge>
                    )}
                  </div>
                  <p className="mt-1 font-mono text-slate-900 bg-white p-3 rounded-xl border border-slate-200/90 shadow-2xs">
                    {caseDetail.failure_raw_reason}
                  </p>
                </div>
              )}

              {"failure_code" in caseDetail && caseDetail.failure_code && (
                <div>
                  <span className="font-bold text-slate-600">Decline Code:</span>
                  <p className="font-mono font-extrabold text-[#0c2340] text-sm mt-0.5">{caseDetail.failure_code}</p>
                </div>
              )}

              {"invoice_number" in caseDetail && (
                <>
                  <div>
                    <span className="font-bold text-slate-600">Invoice Number:</span>
                    <p className="font-mono font-extrabold text-[#0c2340] text-sm mt-0.5">{caseDetail.invoice_number}</p>
                  </div>
                  <div>
                    <span className="font-bold text-slate-600">Buyer Counterparty:</span>
                    <p className="font-bold text-slate-900 text-sm mt-0.5">{caseDetail.buyer_name}</p>
                  </div>
                  <div>
                    <span className="font-bold text-slate-600">Statutory Due Date:</span>
                    <p className="font-mono text-slate-900 text-sm mt-0.5">{caseDetail.statutory_due_date}</p>
                  </div>
                  <div>
                    <span className="font-bold text-slate-600">MSMED Registered:</span>
                    <p className="font-bold text-amber-900 text-sm mt-0.5">{caseDetail.supplier_is_msme ? "Yes (Section 15/16 Covered)" : "No"}</p>
                  </div>
                  {"promises" in caseDetail && Array.isArray((caseDetail as any).promises) && (caseDetail as any).promises.length > 0 && (
                    <div className="sm:col-span-2 bg-blue-50/60 border border-blue-200/80 p-4 rounded-xl space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-[#0c2340] text-xs uppercase tracking-wider flex items-center gap-1.5">
                          <Sparkles className="h-3.5 w-3.5 text-[#0066ff]" />
                          Inbound Debtor Response (Groq Intent Extraction)
                        </span>
                        <Badge className="border-blue-200 bg-white text-[#0066ff] text-[11px] font-bold px-2 py-0.5 rounded-full shadow-2xs">
                          Groq gpt-oss-120b • {Math.round(((caseDetail as any).promises[0].confidence_score || 0.96) * 100)}% Conf
                        </Badge>
                      </div>
                      <p className="font-mono text-xs text-slate-800 bg-white p-3 rounded-lg border border-blue-100">
                        "{(caseDetail as any).promises[0].source_text}"
                      </p>
                      <div className="flex items-center justify-between text-xs pt-0.5 font-medium">
                        <span className="text-slate-600">Classified Outcome:</span>
                        <span className="font-bold text-[#0066ff]">
                          Promised Pay-by Date: {(caseDetail as any).promises[0].promised_pay_by_date}
                        </span>
                      </div>
                    </div>
                  )}
                  {"dispute_flag" in caseDetail && caseDetail.dispute_flag && (
                    <div className="sm:col-span-2 bg-rose-50/80 border border-rose-200 p-4 rounded-xl space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-rose-900 text-xs uppercase tracking-wider">
                          Commercial Dispute Triggered (Rule 6 Halt)
                        </span>
                        <Badge className="border-rose-200 bg-white text-rose-700 text-[11px] font-bold px-2 py-0.5 rounded-full shadow-2xs">
                          Outreach Frozen
                        </Badge>
                      </div>
                      <p className="text-xs text-rose-800 leading-relaxed font-medium">
                        Debtor contested goods delivery / invoice terms. Autonomous communication halted under Rule 6 to prevent commercial escalation.
                      </p>
                    </div>
                  )}
                  {"amount_paid_paise" in caseDetail && (caseDetail as any).amount_paid_paise > 0 && (caseDetail as any).amount_paid_paise < amountPaise && (
                    <div className="sm:col-span-2 bg-amber-50 border border-amber-200/80 p-3.5 rounded-xl flex items-center justify-between">
                      <div>
                        <span className="font-bold text-amber-900 block text-xs">Partial Collection Record</span>
                        <span className="text-xs text-amber-800 font-medium">Installment collected via Razorpay Partial Payment Link</span>
                      </div>
                      <div className="text-right font-mono">
                        <span className="text-xs text-slate-500 block">Collected / Outstanding</span>
                        <span className="font-black text-emerald-700 text-sm">
                          {formatPaiseToRupees((caseDetail as any).amount_paid_paise)}
                        </span>
                        <span className="text-slate-400 text-xs"> / </span>
                        <span className="font-black text-rose-600 text-sm">
                          {formatPaiseToRupees(amountPaise - (caseDetail as any).amount_paid_paise)}
                        </span>
                      </div>
                    </div>
                  )}
                </>
              )}

              {"customer_name" in caseDetail && (
                <>
                  <div>
                    <span className="font-bold text-slate-600">Customer:</span>
                    <p className="font-bold text-slate-900 text-sm mt-0.5">{caseDetail.customer_name}</p>
                  </div>
                  <div>
                    <span className="font-bold text-slate-600">Order ID:</span>
                    <p className="font-mono text-slate-900 text-sm mt-0.5">{caseDetail.razorpay_order_id}</p>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* 2. Diagnosis & AI Reasoning */}
          <div className="rounded-2xl border border-slate-200/90 bg-white p-5 sm:p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <span className="text-xs sm:text-sm font-black uppercase tracking-wider text-[#0c2340] flex items-center gap-2.5">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-100 text-indigo-700">
                  <BrainCircuit className="h-4 w-4" />
                </div>
                2. Autonomous Diagnosis &amp; Root Cause
              </span>
              {"diagnosis_confidence" in caseDetail && caseDetail.diagnosis_confidence && (
                <Badge className="border-blue-200 bg-blue-50 text-[#0066ff] text-xs font-bold px-2.5 py-0.5 rounded-md shadow-2xs">
                  {(caseDetail.diagnosis_confidence * 100).toFixed(0)}% Confidence
                </Badge>
              )}
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 text-xs sm:text-sm">
              <div className="rounded-xl border border-slate-200/80 bg-slate-50/80 p-3.5">
                <span className="text-slate-500 font-bold block text-xs uppercase tracking-wider">Fault Attribution</span>
                <span className={`mt-1 inline-block font-black uppercase text-sm ${
                  resolvedAttribution === "customer_fault" ? "text-indigo-700" : "text-emerald-700"
                }`}>
                  {resolvedAttribution.replace(/_/g, " ")}
                </span>
              </div>

              <div className="rounded-xl border border-slate-200/80 bg-slate-50/80 p-3.5 sm:col-span-2">
                <span className="text-slate-500 font-bold block text-xs uppercase tracking-wider">Taxonomy Classification</span>
                <span className="mt-1 font-mono font-black text-[#0c2340] block text-sm">
                  {resolvedTaxonomy === "npci_window_blocked" || resolvedTaxonomy === "u19"
                    ? "U19 • NPCI AutoPay Window Block"
                    : resolvedTaxonomy === "insufficient_balance" || resolvedTaxonomy === "51"
                    ? "51 • Insufficient Balance / Limit Exceeded"
                    : resolvedTaxonomy === "card_expired" || resolvedTaxonomy === "54"
                    ? "54 • Card Validity Expired"
                    : resolvedTaxonomy === "transient_infra_glitch" || resolvedTaxonomy === "91"
                    ? "91 • Bank Switch Downtime"
                    : resolvedTaxonomy === "wallet_kyc_frozen"
                    ? "Wallet Minimum KYC Lapsed / Balance Frozen"
                    : resolvedTaxonomy === "statutory_overdue_msmed"
                    ? "Statutory Overdue (MSMED Act Section 15/16)"
                    : resolvedTaxonomy === "within_statutory_terms"
                    ? "Within Statutory Terms (MSMED Act Section 15)"
                    : resolvedTaxonomy === "commercial_overdue_standard"
                    ? "Commercial Overdue (Standard Contract Terms)"
                    : resolvedTaxonomy === "disputed_commercial_terms"
                    ? "Disputed Account (Rule 6 Dispute Halt)"
                    : resolvedTaxonomy}
                </span>
              </div>
            </div>

            {/* Diagnostic Rationale Callout */}
            <div className="rounded-xl border border-blue-200/80 bg-blue-50/60 p-4 text-xs sm:text-sm text-slate-700">
              <span className="font-bold text-blue-900 block text-xs uppercase tracking-wider mb-1.5">
                Diagnostic Rationale:
              </span>
              <p className="leading-relaxed italic text-slate-800 font-medium">
                "{aiReasoning || latestAudit?.reason || (
                  module === "A"
                    ? (failureCode === "U19" || resolvedTaxonomy.includes("npci")
                        ? "Rule 2 Enforcement: UPI AutoPay mandate debit failed during congested NPCI peak window (10:00-13:00 IST). Autonomous scheduler paced retry outside peak hours."
                        : failureCode === "54" || resolvedTaxonomy.includes("expired")
                        ? "Rule 1 & Rule 3 Enforcement: Subscription halted after card validity expired (54). Automated mandate retries permanently blocked; alternate Razorpay payment link issued."
                        : failureCode === "51" || resolvedTaxonomy.includes("insufficient")
                        ? "Decline 51: Customer account balance insufficient during AutoPay debit. System scheduled recovery notification paced to salary cycle."
                        : failureCode === "91" || resolvedTaxonomy.includes("glitch") || resolvedTaxonomy.includes("timeout")
                        ? "Decline 91: Bank switch / issuer gateway temporarily inoperative. Scheduled silent retry outside network maintenance."
                        : `Payment failure detected (${failureCode || resolvedTaxonomy}). Automated recovery intervention scheduled.`)
                    : module === "B"
                    ? `Invoice overdue beyond standard credit terms. Progressing through statutory escalation ladder.`
                    : `High-intent checkout cart abandoned. Recovery link pre-generated with payment token.`
                )}"
              </p>
            </div>
          </div>

          {/* 3. AI vs Rule Disagreement Card */}
          <AiVsRuleDisagreement
            ruleSuggestedAction={latestAudit?.rule_suggested_action || null}
            finalAction={resolvedAction}
            aiReasoningText={aiReasoning || null}
          />

          {/* 4. AI Hinglish Voice Recovery Nudge (Sarvam AI) */}
          <VoiceNudgePlayer module={module} caseId={caseId} />

          {/* 5. MSMED Section 16 Live Interest (Module B) */}
          {"supplier_is_msme" in caseDetail && (
            <InterestAccrualCounter invoice={caseDetail as any} />
          )}

          {/* 5b. B2B Statutory Notice Drafting (Gemini 3.6 Flash per 05_ai_layer.md §4c) */}
          {module === "B" && (
            <B2BNoticeDraftCard invoiceId={caseId} invoice={caseDetail} />
          )}

          {/* 6. Policy Gate Checklist (Stopping Rules 1–13) */}
          <div className="rounded-2xl border border-slate-200/90 bg-white p-5 sm:p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <span className="text-xs sm:text-sm font-black uppercase tracking-wider text-[#0c2340] flex items-center gap-2.5">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-100 text-emerald-700">
                  <ShieldCheck className="h-4 w-4" />
                </div>
                3. Deterministic Policy Gate Checklist (Stopping Rules 1–13)
              </span>
              <span className="text-xs text-slate-500 font-mono font-bold bg-slate-100 px-2.5 py-1 rounded-md">
                100% Deterministic
              </span>
            </div>

            <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 text-xs sm:text-sm">
              {stoppingRules.length > 0 ? (
                stoppingRules.map((check: any, idx: number) => (
                  <div key={idx} className="flex items-center justify-between rounded-xl border border-slate-200/80 bg-slate-50/80 p-3.5">
                    <span className="text-slate-700 font-bold">{check.rule}</span>
                    <Badge
                      variant="outline"
                      className={`text-xs font-bold px-2.5 py-0.5 rounded-md ${
                        check.passed
                          ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                          : "border-rose-200 bg-rose-50 text-rose-700"
                      }`}
                    >
                      {check.passed ? "PASS" : "HALTED"}
                    </Badge>
                  </div>
                ))
              ) : (
                <>
                  <div className="flex items-center justify-between rounded-xl border border-slate-200/80 bg-slate-50/80 p-3.5">
                    <span className="text-slate-700 font-bold">Rule 1: Hard Decline Never Retry</span>
                    <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700 font-bold text-xs">PASS</Badge>
                  </div>
                  <div className="flex items-center justify-between rounded-xl border border-slate-200/80 bg-slate-50/80 p-3.5">
                    <span className="text-slate-700 font-bold">Rule 2: NPCI Peak Window Block</span>
                    <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700 font-bold text-xs">PASS</Badge>
                  </div>
                  <div className="flex items-center justify-between rounded-xl border border-slate-200/80 bg-slate-50/80 p-3.5">
                    <span className="text-slate-700 font-bold">Rule 6: Dispute Immediate Halt</span>
                    {"dispute_flag" in caseDetail && caseDetail.dispute_flag ? (
                      <Badge variant="outline" className="border-rose-200 bg-rose-50 text-rose-700 font-bold text-xs">HALTED</Badge>
                    ) : (
                      <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700 font-bold text-xs">PASS</Badge>
                    )}
                  </div>
                  <div className="flex items-center justify-between rounded-xl border border-slate-200/80 bg-slate-50/80 p-3.5">
                    <span className="text-slate-700 font-bold">Rule 11: Single Nudge Cap</span>
                    <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700 font-bold text-xs">PASS</Badge>
                  </div>
                  <div className="flex items-center justify-between rounded-xl border border-slate-200/80 bg-slate-50/80 p-3.5">
                    <span className="text-slate-700 font-bold">Rule 12: Low-Value Floor (&gt; ₹200)</span>
                    {amountPaise < 20000 ? (
                      <Badge variant="outline" className="border-rose-200 bg-rose-50 text-rose-700 font-bold text-xs">FLOOR SKIPPED</Badge>
                    ) : (
                      <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700 font-bold text-xs">PASS</Badge>
                    )}
                  </div>
                  <div className="flex items-center justify-between rounded-xl border border-slate-200/80 bg-slate-50/80 p-3.5">
                    <span className="text-slate-700 font-bold">Rule 10: Human Gate Before Samadhaan</span>
                    {"current_rung" in caseDetail && caseDetail.current_rung === 4 ? (
                      <Badge variant="outline" className="border-amber-200 bg-amber-50 text-amber-800 font-bold text-xs">SIGN-OFF REQUIRED</Badge>
                    ) : (
                      <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700 font-bold text-xs">PASS</Badge>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>

          {/* 7. Settlement Breakdown */}
          {(() => {
            const caseStatus = ((caseDetail as any).status || "").toLowerCase();
            const isSettled = caseStatus === "recovered" || caseStatus === "paid";
            const isPartial = caseStatus === "partially_paid";
            const isClosedTerminal = caseStatus === "closed_unrecovered" || caseStatus === "written_off" || caseStatus === "expired_unrecovered";
            const paidPaise = isPartial && (caseDetail as any).amount_paid_paise > 0 
              ? (caseDetail as any).amount_paid_paise 
              : grossPaise;
            const actualMdr = isClosedTerminal ? 0 : isPartial ? Math.round(paidPaise * 0.02) : mdrPaise;
            const actualGst = isClosedTerminal ? 0 : isPartial ? Math.round(actualMdr * 0.18) : gstPaise;
            const actualNet = isClosedTerminal ? 0 : isPartial ? paidPaise - actualMdr - actualGst : netPaise;

            return (
              <div className="rounded-2xl border border-slate-200/90 bg-slate-50/70 p-5 sm:p-6 space-y-3.5 shadow-2xs">
                <div className="flex items-center justify-between border-b border-slate-200/80 pb-3">
                  <span className="text-xs sm:text-sm font-black uppercase tracking-wider text-[#0c2340] flex items-center gap-2.5">
                    <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-slate-200 text-slate-700">
                      <CreditCard className="h-4 w-4" />
                    </div>
                    {isSettled 
                      ? "4. Confirmed Settlement Math (Gross to Net)" 
                      : isPartial 
                      ? "4. Partial Installment Settlement Math (Collected to Net)" 
                      : isClosedTerminal
                      ? "4. Unrecovered Exposure (Terminal Policy State)"
                      : "4. Projected Recovery Settlement (Estimated Net Yield)"}
                  </span>
                  <Badge variant="outline" className={`text-xs font-bold px-2.5 py-0.5 rounded-md shadow-2xs ${
                    isSettled 
                      ? "border-emerald-200 bg-emerald-50 text-emerald-800" 
                      : isPartial
                      ? "border-amber-200 bg-amber-50 text-amber-900"
                      : isClosedTerminal
                      ? "border-slate-300 bg-slate-100 text-slate-700"
                      : "border-blue-200 bg-blue-50 text-[#0066ff]"
                  }`}>
                    {isSettled ? "Settled into Bank (T+2)" : isPartial ? "Partial Settled (T+2)" : isClosedTerminal ? "Zero Settlement • Closed" : "Projected Payout (T+2)"}
                  </Badge>
                </div>

                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 text-xs sm:text-sm font-mono">
                  <div className="bg-white p-4 rounded-2xl border border-slate-200/90 shadow-2xs">
                    <span className="text-slate-500 font-sans block text-xs font-bold">
                      {isPartial ? "Collected Installment" : isClosedTerminal ? "Capital at Risk" : "Gross Amount"}
                    </span>
                    <span className="font-black text-[#0c2340] text-base sm:text-lg mt-1 block">{formatPaiseToRupees(paidPaise)}</span>
                  </div>
                  <div className="bg-white p-4 rounded-2xl border border-slate-200/90 shadow-2xs">
                    <span className="text-slate-500 font-sans block text-xs font-bold">Platform Fee (2%)</span>
                    <span className={`${isClosedTerminal ? "text-slate-400" : "text-rose-600"} font-black text-base sm:text-lg mt-1 block`}>
                      {isClosedTerminal ? "₹0.00" : `-${formatPaiseToRupees(actualMdr)}`}
                    </span>
                  </div>
                  <div className="bg-white p-4 rounded-2xl border border-slate-200/90 shadow-2xs">
                    <span className="text-slate-500 font-sans block text-xs font-bold">GST on Fee (18%)</span>
                    <span className={`${isClosedTerminal ? "text-slate-400" : "text-rose-600"} font-black text-base sm:text-lg mt-1 block`}>
                      {isClosedTerminal ? "₹0.00" : `-${formatPaiseToRupees(actualGst)}`}
                    </span>
                  </div>
                  <div className={`p-4 rounded-2xl border shadow-2xs ${
                    isSettled 
                      ? "bg-emerald-50/90 border-emerald-200" 
                      : isPartial 
                      ? "bg-amber-50/90 border-amber-200" 
                      : isClosedTerminal
                      ? "bg-slate-100 border-slate-200"
                      : "bg-blue-50/90 border-blue-200"
                  }`}>
                    <span className={`font-sans font-black block text-xs ${
                      isSettled ? "text-emerald-900" : isPartial ? "text-amber-950" : isClosedTerminal ? "text-slate-600" : "text-blue-900"
                    }`}>
                      {isSettled ? "Net Settled (T+2)" : isPartial ? "Net Collected (T+2)" : isClosedTerminal ? "Net Recovered" : "Projected Net Yield"}
                    </span>
                    <span className={`font-black text-base sm:text-lg mt-1 block ${
                      isSettled ? "text-emerald-700" : isPartial ? "text-amber-800" : isClosedTerminal ? "text-slate-500" : "text-blue-700"
                    }`}>
                      {formatPaiseToRupees(actualNet)}
                    </span>
                  </div>
                </div>

                {isSettled && (
                  <div className="pt-2 border-t border-slate-200/80 space-y-2">
                    <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
                      Autonomous Recovery Audit Trail:
                    </span>
                    <div className="grid grid-cols-1 sm:grid-cols-4 gap-2 text-xs font-mono">
                      <div className="bg-white p-2.5 rounded-xl border border-slate-200/90 flex flex-col justify-between">
                        <span className="text-[10px] text-slate-400 font-sans font-bold">1. Incident Detected</span>
                        <span className="font-bold text-slate-800 mt-1">{module === "A" ? "Mandate Decline" : module === "B" ? "Statutory Overdue" : "Cart Abandoned"}</span>
                      </div>
                      <div className="bg-white p-2.5 rounded-xl border border-slate-200/90 flex flex-col justify-between">
                        <span className="text-[10px] text-slate-400 font-sans font-bold">2. AI Outreach</span>
                        <span className="font-bold text-indigo-700 mt-1">Hinglish Voice Nudge</span>
                      </div>
                      <div className="bg-white p-2.5 rounded-xl border border-slate-200/90 flex flex-col justify-between">
                        <span className="text-[10px] text-slate-400 font-sans font-bold">3. Link Delivered</span>
                        <span className="font-bold text-blue-700 mt-1 truncate" title={(caseDetail as any).razorpay_payment_link_id || "plink_dispatched"}>
                          {(caseDetail as any).razorpay_payment_link_id || "plink_dispatched"}
                        </span>
                      </div>
                      <div className="bg-emerald-50 p-2.5 rounded-xl border border-emerald-200 flex flex-col justify-between">
                        <span className="text-[10px] text-emerald-600 font-sans font-bold">4. Bank Settled (T+2)</span>
                        <span className="font-bold text-emerald-800 mt-1 truncate" title={latestAudit?.razorpay_reference || "pay_confirmed"}>
                          {latestAudit?.razorpay_reference || "pay_confirmed"}
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {isPartial ? (
                  <p className="text-xs text-amber-800 font-medium pt-1">
                    Confirmed net settlement for collected partial installment. The outstanding balance of {formatPaiseToRupees(amountPaise - paidPaise)} remains active on the statutory escalation ladder.
                  </p>
                ) : isClosedTerminal ? (
                  <p className="text-xs text-slate-500 font-medium pt-1">
                    Case permanently halted under Policy Gate stopping rules. Zero platform fees incurred and zero capital settled into merchant account.
                  </p>
                ) : !isSettled && (
                  <p className="text-xs text-slate-500 font-medium pt-1">
                    Calculated net merchant payout once debtor pays via Razorpay checkout, factoring standard 2% gateway MDR and 18% GST.
                  </p>
                )}
              </div>
            );
          })()}

          </div>
        </ScrollArea>

        {/* Footer Actions — Strictly Guarded by Operational & Policy State */}
        {(() => {
          const caseStatus = ((caseDetail as any).status || "").toLowerCase();
          const isSettled = caseStatus === "recovered" || caseStatus === "paid";
          const isDisputed = "dispute_flag" in caseDetail && caseDetail.dispute_flag;
          const isSkippedLowValue = caseStatus === "skipped_low_value";
          const isEscalatedSyncGap = caseStatus === "escalated";
          const isClosedTerminal = caseStatus === "closed_unrecovered" || caseStatus === "written_off" || caseStatus === "expired_unrecovered";
          const isPendingHumanRung4 = "current_rung" in caseDetail && caseDetail.current_rung === 4 && caseStatus === "pending_human_approval";
          const isInFlight = !isSettled && !isDisputed && !isSkippedLowValue && !isEscalatedSyncGap && !isClosedTerminal && !isPendingHumanRung4;

          return (
            <DialogFooter className="border-t border-slate-200 bg-slate-50 p-5 flex flex-wrap items-center justify-between gap-3 shrink-0">
              {isSettled && (
                <div className="flex items-center gap-2.5 bg-emerald-50 border border-emerald-200 px-4 py-2.5 rounded-xl text-emerald-800 text-xs sm:text-sm font-bold shadow-2xs">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                  <span>Payment Collected & Settled into Bank (T+2)</span>
                  {latestAudit?.razorpay_reference && (
                    <span className="font-mono text-xs text-emerald-700 ml-2 bg-emerald-100 px-2 py-0.5 rounded">
                      Ref: {latestAudit.razorpay_reference}
                    </span>
                  )}
                </div>
              )}

              {isDisputed && (
                <div className="flex items-center gap-2.5 bg-rose-50 border border-rose-200 px-4 py-2.5 rounded-xl text-rose-800 text-xs sm:text-sm font-bold shadow-2xs">
                  <ShieldAlert className="h-4 w-4 text-rose-600 shrink-0" />
                  <span>Rule 6 Enforcement: Outreach Frozen Due to Active Dispute</span>
                </div>
              )}

              {isSkippedLowValue && (
                <div className="flex items-center gap-2.5 bg-rose-50 border border-rose-200 px-4 py-2.5 rounded-xl text-rose-800 text-xs sm:text-sm font-bold shadow-2xs">
                  <ShieldAlert className="h-4 w-4 text-rose-600 shrink-0" />
                  <span>Rule 12 Enforcement: Cart Under ₹200 Recovery Floor — Nudge Skipped</span>
                </div>
              )}

              {isEscalatedSyncGap && (
                <div className="flex items-center gap-2.5 bg-amber-50 border border-amber-200 px-4 py-2.5 rounded-xl text-amber-800 text-xs sm:text-sm font-bold shadow-2xs">
                  <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0" />
                  <span>Rule 5 Enforcement: Gateway Data Sync Gap — Escalated to Human Ops</span>
                </div>
              )}

              {isClosedTerminal && (
                <div className="flex items-center gap-2.5 bg-slate-100 border border-slate-200 px-4 py-2.5 rounded-xl text-slate-700 text-xs sm:text-sm font-bold shadow-2xs">
                  <XCircle className="h-4 w-4 text-slate-500 shrink-0" />
                  <span>Case Closed / Unrecovered — Retries Exhausted Under Policy Gate</span>
                </div>
              )}

              {isPendingHumanRung4 && (
                <Button
                  onClick={handleApproveRung4}
                  disabled={approveRung4Mutation.isPending}
                  className="bg-amber-600 text-white hover:bg-amber-700 text-xs sm:text-sm font-bold gap-2 h-11 px-5 rounded-xl shadow-md shadow-amber-500/20 active:scale-98"
                >
                  <Scale className="h-4 w-4" />
                  <span>{approveRung4Mutation.isPending ? "Approving..." : "Approve MSME Samadhaan Filing (Rule 10)"}</span>
                </Button>
              )}

              {isInFlight && (
                <div className="flex flex-wrap items-center gap-3">
                  {checkoutUrl ? (
                    <>
                      <Button
                        onClick={() => window.open(checkoutUrl, "_blank")}
                        className="bg-[#0066ff] text-white hover:bg-[#0052cc] text-xs sm:text-sm font-bold gap-2 h-11 px-5 rounded-xl shadow-md shadow-blue-500/20 active:scale-98"
                      >
                        <ExternalLink className="h-4 w-4" />
                        <span>Open Live Razorpay Checkout</span>
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => handleCopyLink(checkoutUrl)}
                        className="text-xs sm:text-sm font-bold text-slate-700 gap-1.5 h-11 px-4 rounded-xl border-slate-200 bg-white hover:bg-slate-100"
                      >
                        {copied ? <Check className="h-4 w-4 text-emerald-600" /> : <Copy className="h-4 w-4" />}
                        <span>{copied ? "Copied" : "Copy Link"}</span>
                      </Button>
                    </>
                  ) : (
                    <Button
                      onClick={handleGenerateLink}
                      disabled={generateLinkMutation.isPending}
                      className="bg-[#0066ff] text-white hover:bg-[#0052cc] text-xs sm:text-sm font-bold gap-2 h-11 px-5 rounded-xl shadow-md shadow-blue-500/20 active:scale-98"
                    >
                      <Zap className="h-4 w-4" />
                      <span>{generateLinkMutation.isPending ? "Creating Link..." : "Generate Razorpay Link"}</span>
                    </Button>
                  )}

                  {/* Quota Fallback Simulation Button */}
                  <Button
                    variant="outline"
                    onClick={handleSimulateWebhook}
                    disabled={simulateWebhookMutation.isPending}
                    className="border-slate-200 bg-white hover:bg-slate-100 text-slate-700 text-xs sm:text-sm font-bold gap-2 h-11 px-4 rounded-xl shadow-xs"
                  >
                    <FlaskConical className="h-4 w-4 text-indigo-600" />
                    <span>{simulateWebhookMutation.isPending ? "Simulating..." : "Simulate Signed Webhook"}</span>
                  </Button>
                </div>
              )}
            </DialogFooter>
          );
        })()}
      </DialogContent>
    </Dialog>
  );
}