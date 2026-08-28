import { Invoice } from "@/types/api";

interface InterestAccrualCounterProps {
  invoice: Invoice;
}

export default function InterestAccrualCounter({ invoice }: InterestAccrualCounterProps) {
  if (!invoice.supplier_is_msme || invoice.status !== "overdue") {
    return null;
  }

  return (
    <div className="rounded-lg border border-rose-200 bg-rose-50/50 p-4">
      <div className="flex items-center justify-between">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-rose-700">
            MSMED Act 2006, Section 16 Interest
          </span>
          <p className="text-xs text-slate-500">Statutory due date: {invoice.statutory_due_date}</p>
        </div>
      </div>
      <div className="mt-2">
        <p className="text-xs text-slate-600">Compounding monthly @ 3x RBI Bank Rate</p>
      </div>
    </div>
  );
}
