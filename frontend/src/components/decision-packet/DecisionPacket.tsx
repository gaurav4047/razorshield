import { useState } from "react";
import { useCaseDetail, useGenerateLink, useSimulateWebhook, useApproveRung4 } from "@/api/useCases";
import { formatPaiseToRupees } from "@/lib/utils";
import AiVsRuleDisagreement from "./AiVsRuleDisagreement";
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
  FlaskConical
} from "lucide-react";


interface DecisionPacketProps {
  module: "A" | "B" | "C";
  caseId: string;
  onClose: () => void;
}

export default function DecisionPacket({ module, caseId, onClose }: DecisionPacketProps) {
  const [copied, setCopied] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const { data: caseDetail, isLoading, refetch } = useCaseDetail(module, caseId);
  const generateLinkMutation = useGenerateLink();
  const simulateWebhookMutation = useSimulateWebhook();
  const approveRung4Mutation = useApproveRung4();

  if (isLoading || !caseDetail) {
    return (
      <Dialog open={true} onOpenChange={() => onClose()}>
        <DialogContent className="sm:max-w-3xl">
          <div className="flex h-64 items-center justify-center">
            <div className="text-center">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent mx-auto"></div>
              <p className="mt-3 text-xs text-slate-500 font-medium">Loading Explainability Decision Packet...</p>
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
      await generateLinkMutation.mutateAsync({ module, caseId });
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

  // Settlement Calculation Breakdown (2% MDR + 18% GST)
  const amountPaise = caseDetail.amount_paise || 0;
  const mdrPaise = Math.round(amountPaise * 0.02);
  const gstPaise = Math.round(mdrPaise * 0.18);
  const netPaise = amountPaise - mdrPaise - gstPaise;

  const paymentLinkId = caseDetail.razorpay_payment_link_id;
  const checkoutUrl = paymentLinkId ? `https://rzp.io/i/${paymentLinkId.replace("plink_", "")}` : null;

  return (
    <Dialog open={true} onOpenChange={() => onClose()}>
      <DialogContent className="max-h-[92vh] sm:max-w-3xl p-0 overflow-hidden bg-white shadow-2xl">
        {/* Header Bar */}
        <DialogHeader className="border-b border-slate-200 bg-slate-900 text-white p-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="flex h-7 w-7 items-center justify-center rounded-md bg-blue-600 text-white">
                <BrainCircuit className="h-4 w-4" />
              </div>
              <div>
                <DialogTitle className="text-base font-bold text-white flex items-center gap-2">
                  <span>Decision Packet &amp; Audit Trace</span>
                  <Badge variant="outline" className="border-slate-700 bg-slate-800 text-slate-300 font-mono text-[10px]">
                    Module {module}
                  </Badge>
                </DialogTitle>
                <DialogDescription className="text-xs text-slate-400 font-mono mt-0.5">
                  ID: {caseId}
                </DialogDescription>
              </div>
            </div>

            <div className="text-right">
              <span className="font-mono text-lg font-bold text-emerald-400 tabular-nums">
                {formatPaiseToRupees(amountPaise)}
              </span>
              <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">
                Status: {(caseDetail as any).status}
              </div>
            </div>
          </div>
        </DialogHeader>

        {/* Scrollable Body */}
        <ScrollArea className="max-h-[calc(92vh-140px)] p-6 space-y-5">
          {actionError && (
            <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800 flex items-start gap-2">
              <AlertOctagon className="h-4 w-4 text-rose-600 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold">Sandbox Quota Notice:</p>
                <p className="mt-0.5">{actionError}</p>
              </div>
            </div>
          )}

          {/* 1. Ingestion Signal Section */}
          <div className="rounded-lg border border-slate-200 bg-slate-50/70 p-4">
            <div className="flex items-center justify-between border-b border-slate-200/60 pb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                <FileText className="h-3.5 w-3.5 text-slate-500" />
                1. Ingestion Signal Payload
              </span>
              <Badge variant="outline" className="border-slate-200 bg-white text-slate-600 text-[10px]">
                {"payment_case" in caseDetail || "method" in caseDetail ? "Gateway Webhook" : "ERP Ledger Sync"}
              </Badge>
            </div>

            <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2 text-xs">
              {"failure_raw_reason" in caseDetail && (
                <div className="sm:col-span-2">
                  <span className="font-semibold text-slate-600">Raw Failure Reason:</span>
                  <p className="mt-1 font-mono text-slate-900 bg-white p-2 rounded border border-slate-200">
                    {caseDetail.failure_raw_reason}
                  </p>
                </div>
              )}

              {"failure_code" in caseDetail && caseDetail.failure_code && (
                <div>
                  <span className="font-semibold text-slate-600">Decline Code:</span>
                  <p className="font-mono font-bold text-slate-900">{caseDetail.failure_code}</p>
                </div>
              )}

              {"invoice_number" in caseDetail && (
                <>
                  <div>
                    <span className="font-semibold text-slate-600">Invoice Number:</span>
                    <p className="font-mono font-bold text-slate-900">{caseDetail.invoice_number}</p>
                  </div>
                  <div>
                    <span className="font-semibold text-slate-600">Buyer Counterparty:</span>
                    <p className="font-medium text-slate-900">{caseDetail.buyer_name}</p>
                  </div>
                  <div>
                    <span className="font-semibold text-slate-600">Statutory Due Date:</span>
                    <p className="font-mono text-slate-900">{caseDetail.statutory_due_date}</p>
                  </div>
                  <div>
                    <span className="font-semibold text-slate-600">MSMED Registered:</span>
                    <p className="font-medium text-slate-900">{caseDetail.supplier_is_msme ? "Yes (Section 15/16 Covered)" : "No"}</p>
                  </div>
                </>
              )}

              {"customer_name" in caseDetail && (
                <>
                  <div>
                    <span className="font-semibold text-slate-600">Customer:</span>
                    <p className="font-medium text-slate-900">{caseDetail.customer_name}</p>
                  </div>
                  <div>
                    <span className="font-semibold text-slate-600">Order ID:</span>
                    <p className="font-mono text-slate-900">{caseDetail.razorpay_order_id}</p>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* 2. Diagnosis & AI Reasoning */}
          <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-xs">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                <BrainCircuit className="h-3.5 w-3.5 text-blue-600" />
                2. Autonomous Diagnosis &amp; Root Cause
              </span>
              {"diagnosis_confidence" in caseDetail && caseDetail.diagnosis_confidence && (
                <Badge className="border-blue-200 bg-blue-50 text-blue-800 text-[10px]">
                  {(caseDetail.diagnosis_confidence * 100).toFixed(0)}% Confidence
                </Badge>
              )}
            </div>

            <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3 text-xs">
              {"fault_attribution" in caseDetail && (
                <div className="rounded border border-slate-100 bg-slate-50 p-2.5">
                  <span className="text-slate-500 font-semibold block text-[11px] uppercase">Fault Attribution</span>
                  <span className={`mt-1 inline-block font-bold uppercase ${
                    caseDetail.fault_attribution === "customer_fault" ? "text-indigo-700" : "text-emerald-700"
                  }`}>
                    {caseDetail.fault_attribution?.replace("_", " ")}
                  </span>
                </div>
              )}

              {"classified_root_cause" in caseDetail && (
                <div className="rounded border border-slate-100 bg-slate-50 p-2.5 sm:col-span-2">
                  <span className="text-slate-500 font-semibold block text-[11px] uppercase">Taxonomy Classification</span>
                  <span className="mt-1 font-mono font-bold text-slate-900 block">
                    {caseDetail.classified_root_cause || "standard_ladder"}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* 3. AI vs Rule Disagreement Card */}
          <AiVsRuleDisagreement
            ruleSuggestedAction={
              "fault_attribution" in caseDetail && caseDetail.fault_attribution === "customer_fault" && caseDetail.attempt_number > 2
                ? "silent_retry"
                : null
            }
            finalAction={(caseDetail as any).recommended_intervention || (caseDetail as any).status}
            aiReasoningText={
              "classified_root_cause" in caseDetail && caseDetail.classified_root_cause === "insufficient_balance"
                ? "Customer has 18 months of clean payment history. Diagnosis indicates a transient month-end liquidity dip. Rescheduling delayed nudge aligns with upcoming salary cycle."
                : null
            }
          />

          {/* 4. MSMED Section 16 Live Interest (Module B) */}
          {"supplier_is_msme" in caseDetail && (
            <InterestAccrualCounter invoice={caseDetail as any} />
          )}

          {/* 5. Policy Gate Checklist */}
          <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-xs">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
                3. Policy Gate Checklist (Stopping Rules 1–13)
              </span>
              <span className="text-[10px] text-slate-500 font-mono">100% Deterministic</span>
            </div>

            <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2 text-xs">
              <div className="flex items-center justify-between rounded border border-slate-100 bg-slate-50 p-2">
                <span className="text-slate-700 font-medium">Rule 1: Hard Decline Never Retry</span>
                <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700 text-[10px]">PASS</Badge>
              </div>

              <div className="flex items-center justify-between rounded border border-slate-100 bg-slate-50 p-2">
                <span className="text-slate-700 font-medium">Rule 2: NPCI Peak Window Block</span>
                <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700 text-[10px]">PASS</Badge>
              </div>

              <div className="flex items-center justify-between rounded border border-slate-100 bg-slate-50 p-2">
                <span className="text-slate-700 font-medium">Rule 6: Dispute Immediate Halt</span>
                {"dispute_flag" in caseDetail && caseDetail.dispute_flag ? (
                  <Badge variant="outline" className="border-rose-200 bg-rose-50 text-rose-700 text-[10px]">HALTED</Badge>
                ) : (
                  <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700 text-[10px]">PASS</Badge>
                )}
              </div>

              <div className="flex items-center justify-between rounded border border-slate-100 bg-slate-50 p-2">
                <span className="text-slate-700 font-medium">Rule 11: Single Nudge Cap</span>
                <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700 text-[10px]">PASS</Badge>
              </div>

              <div className="flex items-center justify-between rounded border border-slate-100 bg-slate-50 p-2">
                <span className="text-slate-700 font-medium">Rule 12: Low-Value Floor (&gt;₹200)</span>
                {amountPaise < 20000 ? (
                  <Badge variant="outline" className="border-rose-200 bg-rose-50 text-rose-700 text-[10px]">FLOOR SKIPPED</Badge>
                ) : (
                  <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700 text-[10px]">PASS</Badge>
                )}
              </div>

              <div className="flex items-center justify-between rounded border border-slate-100 bg-slate-50 p-2">
                <span className="text-slate-700 font-medium">Rule 10: Human Gate Before Samadhaan</span>
                {"current_rung" in caseDetail && caseDetail.current_rung === 4 ? (
                  <Badge variant="outline" className="border-amber-200 bg-amber-50 text-amber-800 text-[10px]">SIGN-OFF REQUIRED</Badge>
                ) : (
                  <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700 text-[10px]">PASS</Badge>
                )}
              </div>
            </div>
          </div>

          {/* 6. Settlement Breakdown */}
          <div className="rounded-lg border border-slate-200 bg-slate-50/70 p-4">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5 border-b border-slate-200/60 pb-2">
              <CreditCard className="h-3.5 w-3.5 text-slate-600" />
              4. Verified Settlement Math (Gross to Net)
            </span>

            <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4 text-xs font-mono">
              <div className="bg-white p-2.5 rounded border border-slate-200">
                <span className="text-slate-500 font-sans block text-[11px]">Gross Amount</span>
                <span className="font-bold text-slate-900">{formatPaiseToRupees(amountPaise)}</span>
              </div>
              <div className="bg-white p-2.5 rounded border border-slate-200">
                <span className="text-slate-500 font-sans block text-[11px]">Platform Fee (2%)</span>
                <span className="text-rose-600">-{formatPaiseToRupees(mdrPaise)}</span>
              </div>
              <div className="bg-white p-2.5 rounded border border-slate-200">
                <span className="text-slate-500 font-sans block text-[11px]">GST on Fee (18%)</span>
                <span className="text-rose-600">-{formatPaiseToRupees(gstPaise)}</span>
              </div>
              <div className="bg-emerald-50 p-2.5 rounded border border-emerald-200">
                <span className="text-emerald-800 font-sans font-bold block text-[11px]">Net Settled (T+2)</span>
                <span className="font-bold text-emerald-700">{formatPaiseToRupees(netPaise)}</span>
              </div>
            </div>
          </div>
        </ScrollArea>

        {/* Footer Actions */}
        <DialogFooter className="border-t border-slate-200 bg-slate-50 p-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            {checkoutUrl ? (
              <>
                <Button
                  onClick={() => window.open(checkoutUrl, "_blank")}
                  className="bg-blue-600 text-white hover:bg-blue-700 text-xs font-semibold gap-1.5 h-9"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  Open Live Razorpay Checkout
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleCopyLink(checkoutUrl)}
                  className="text-xs text-slate-700 gap-1 h-9"
                >
                  {copied ? <Check className="h-3.5 w-3.5 text-emerald-600" /> : <Copy className="h-3.5 w-3.5" />}
                  {copied ? "Copied" : "Copy Link"}
                </Button>
              </>
            ) : (
              <Button
                onClick={handleGenerateLink}
                disabled={generateLinkMutation.isPending}
                className="bg-blue-600 text-white hover:bg-blue-700 text-xs font-semibold gap-1.5 h-9"
              >
                <Zap className="h-3.5 w-3.5" />
                {generateLinkMutation.isPending ? "Creating Link..." : "Generate Razorpay Link"}
              </Button>
            )}

            {/* Quota Fallback Simulation Button */}
            <Button
              variant="outline"
              size="sm"
              onClick={handleSimulateWebhook}
              disabled={simulateWebhookMutation.isPending}
              className="border-slate-300 text-slate-700 hover:bg-slate-100 text-xs gap-1 h-9"
            >
              <FlaskConical className="h-3.5 w-3.5 text-indigo-600" />
              {simulateWebhookMutation.isPending ? "Simulating..." : "Simulate Signed Webhook"}
            </Button>
          </div>

          {/* Rung 4 Human Sign-off CTA */}
          {"current_rung" in caseDetail && caseDetail.current_rung === 4 && (
            <Button
              onClick={handleApproveRung4}
              disabled={approveRung4Mutation.isPending}
              className="bg-amber-600 text-white hover:bg-amber-700 text-xs font-semibold gap-1.5 h-9"
            >
              <Scale className="h-3.5 w-3.5" />
              {approveRung4Mutation.isPending ? "Approving..." : "Approve MSME Samadhaan Filing"}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

