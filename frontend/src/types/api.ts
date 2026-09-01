export type InvoiceStatus =
  | "pending"
  | "overdue"
  | "disputed"
  | "partially_paid"
  | "pending_human_approval"
  | "paid"
  | "written_off";

export type PromiseStatus = "pending" | "kept" | "broken";

export type PaymentMethod = "upi" | "card" | "netbanking" | "wallet" | "emi";
export type PaymentContext = "subscription" | "one_time";
export type SubscriptionState = "active" | "pending" | "halted" | "completed" | "cancelled";
export type FaultAttribution = "customer_fault" | "infrastructure_fault" | "unknown";
export type InterventionType = "silent_retry" | "delayed_retry_notify" | "escalate_human" | "alternate_method";
export type PaymentCaseStatus = "open" | "retried" | "recovered" | "escalated" | "closed_unrecovered";

export type AbandonedOrderStatus = "open" | "nudged" | "recovered" | "expired_unrecovered" | "skipped_low_value";

export type CaseType = "invoice" | "payment_case" | "abandoned_order";
export type PipelineStage = "diagnose" | "policy_gate" | "execute" | "audit";

export interface Batch {
  id: string;
  label: string;
  description: string | null;
  created_at: string;
}

export interface InvoicePromise {
  id: string;
  invoice_id: string;
  source_text: string;
  promised_pay_by_date: string;
  promised_amount_paise: number | null;
  classified_by: string;
  confidence_score: number | null;
  status: PromiseStatus;
  resolved_at: string | null;
  created_at: string;
}

export interface Invoice {
  id: string;
  batch_id: string;
  invoice_number: string;
  buyer_name: string;
  buyer_contact: string;
  buyer_email: string;
  supplier_is_msme: boolean;
  has_written_agreement: boolean;
  amount_paise: number;
  amount_paid_paise: number;
  currency: string;
  invoice_date: string;
  goods_accepted_date: string;
  statutory_due_date: string;
  status: InvoiceStatus;
  current_rung: number;
  dispute_flag: boolean;
  broken_promise_count: number;
  buyer_archetype: string;
  razorpay_payment_link_id: string | null;
  last_contact_at: string | null;
  created_at: string;
  updated_at: string;
  promises?: InvoicePromise[];
}

export interface PaymentCase {
  id: string;
  batch_id: string;
  razorpay_payment_id: string | null;
  razorpay_subscription_id: string | null;
  razorpay_order_id: string | null;
  method: PaymentMethod;
  context: PaymentContext;
  subscription_state: SubscriptionState | null;
  amount_paise: number;
  currency: string;
  failure_code: string | null;
  failure_raw_reason: string;
  attempt_number: number;
  fault_attribution: FaultAttribution;
  classified_root_cause: string | null;
  diagnosis_confidence: number | null;
  recommended_intervention: InterventionType | null;
  npci_execution_window_conflict: boolean;
  status: PaymentCaseStatus;
  retry_count: number;
  last_action_at: string | null;
  razorpay_payment_link_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface AbandonedOrder {
  id: string;
  batch_id: string;
  razorpay_order_id: string;
  customer_name: string;
  customer_contact: string;
  customer_email: string;
  amount_paise: number;
  currency: string;
  order_created_at: string;
  abandonment_detected_at: string | null;
  nudge_sent: boolean;
  nudge_sent_at: string | null;
  razorpay_payment_link_id: string | null;
  status: AbandonedOrderStatus;
  created_at: string;
  updated_at: string;
}

export interface StoppingRuleCheck {
  rule: string;
  passed: boolean;
  detail: string;
}

export interface AuditLogEntry {
  id: number;
  batch_id: string;
  case_type: CaseType;
  case_id: string;
  timestamp: string;
  stage: PipelineStage;
  rule_suggested_action: string | null;
  ai_reasoning_text: string | null;
  stopping_rules_checked: StoppingRuleCheck[];
  final_action: string;
  reason: string;
  gross_amount_paise: number | null;
  mdr_paise: number | null;
  gst_on_mdr_paise: number | null;
  net_amount_paise: number | null;
  computed_interest_accrued_paise: number | null;
  razorpay_reference: string | null;
  created_at: string;
}

export interface UnrecoveredExceptionItem {
  reference: string;
  case_type: string;
  status: string;
  amount_paise: number;
}

export interface ExceptionsBreakdown {
  low_value_floor_skipped: number;
  dispute_halted: number;
  hard_declines_closed: number;
  pending_human_approval: number;
}


export interface BatchSummary {
  batch_id: string;
  total_at_risk_paise: number;
  gross_recovered_paise: number;
  net_recovered_paise: number;
  recovery_rate_pct: number;
  total_cases: number;
  recovered_cases: number;
  partially_paid_cases: number;
  partially_paid_recovered_paise: number;
  exception_count: number;
  exceptions: UnrecoveredExceptionItem[];
  exceptions_breakdown: ExceptionsBreakdown;
}

export interface SystemicPatternFinding {
  grouping_description: string;
  bucket_count: number;
  total_count: number;
  observed_share: number;
  expected_share: number;
  anomaly_ratio: number;
  narration: string;
}

