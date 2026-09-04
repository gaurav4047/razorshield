import { useEffect, useState } from "react";
import { Invoice } from "@/types/api";
import { formatPaiseToRupees } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Flame, Calculator, Scale, AlertCircle } from "lucide-react";

interface InterestAccrualCounterProps {
  invoice: Invoice;
}

export default function InterestAccrualCounter({ invoice }: InterestAccrualCounterProps) {
  const [accruedPaise, setAccruedPaise] = useState<number>(0);
  const [daysOverdue, setDaysOverdue] = useState<number>(0);

  useEffect(() => {
    if (!invoice.statutory_due_date) return;

    const rbiBankRate = 5.50;
    const statutoryMultiplier = 3;
    const annualRate = (rbiBankRate * statutoryMultiplier) / 100; // 16.50% p.a.
    const monthlyRate = annualRate / 12; // 1.375% per month

    const calculate = () => {
      const dueDate = new Date(invoice.statutory_due_date).getTime();
      const now = new Date().getTime();

      if (now <= dueDate) {
        setAccruedPaise(0);
        setDaysOverdue(0);
        return;
      }

      const diffMs = now - dueDate;
      const diffDays = diffMs / (1000 * 60 * 60 * 24);
      setDaysOverdue(Math.floor(diffDays));

      // Monthly compounding formula: Principal * ((1 + monthly_rate)^(months_fraction) - 1)
      const monthsFraction = diffDays / 30.0;
      const principal = invoice.amount_paise - (invoice.amount_paid_paise || 0);
      const interest = principal * (Math.pow(1 + monthlyRate, monthsFraction) - 1);

      setAccruedPaise(Math.round(interest));
    };

    calculate();
    const interval = setInterval(calculate, 1000);
    return () => clearInterval(interval);
  }, [invoice]);

  if (!invoice.supplier_is_msme) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4 text-xs sm:text-sm text-slate-600 flex items-center gap-2.5">
        <AlertCircle className="h-4 w-4 text-slate-400 shrink-0" />
        <span>Non-MSME supplier contract: standard commercial terms apply (MSMED Section 16 interest does not apply).</span>
      </div>
    );
  }

  const isPartiallyPaid = (invoice.amount_paid_paise || 0) > 0;
  const outstandingPrincipalPaise = invoice.amount_paise - (invoice.amount_paid_paise || 0);
  const totalPayablePaise = outstandingPrincipalPaise + accruedPaise;

  return (
    <div className="rounded-2xl border border-amber-300 bg-gradient-to-br from-amber-50/80 via-white to-amber-50/30 p-5 shadow-xs space-y-4">
      <div className="flex items-center justify-between gap-3 border-b border-amber-200/60 pb-3">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-amber-600 text-white shadow-xs">
            <Scale className="h-4 w-4" />
          </div>
          <div>
            <span className="text-xs sm:text-sm font-extrabold uppercase tracking-wider text-amber-950 block">
              MSMED Act 2006, Section 16 Compound Interest
            </span>
            <span className="text-xs text-amber-800 font-medium">
              Statutory 3&times; RBI Bank Rate (20.25% p.a. Monthly Rests)
            </span>
          </div>
        </div>
        <Badge className="border-amber-300 bg-amber-100 text-amber-900 text-xs font-bold gap-1 px-2.5 py-0.5 shadow-2xs">
          <Flame className="h-3.5 w-3.5 text-amber-600 animate-pulse" />
          Accruing Live
        </Badge>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {/* Days Overdue */}
        <div className="rounded-xl border border-amber-200/60 bg-white p-3.5 shadow-2xs space-y-1">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Statutory Due Date</p>
          <p className="font-mono text-base font-extrabold text-slate-900">{invoice.statutory_due_date}</p>
          <p className="text-xs text-amber-700 font-bold">
            {daysOverdue > 0 ? `${daysOverdue} days overdue` : "Due today"}
          </p>
        </div>

        {/* Accrued Interest */}
        <div className="rounded-xl border border-amber-300 bg-amber-50/70 p-3.5 shadow-2xs space-y-1">
          <p className="text-xs font-bold uppercase tracking-wider text-amber-900">Accrued Interest</p>
          <p className="font-mono text-xl font-extrabold text-amber-900 tabular-nums">
            {formatPaiseToRupees(accruedPaise)}
          </p>
          <p className="text-xs text-amber-800 font-mono font-medium">
            @ 20.25% p.a. Compound
          </p>
        </div>

        {/* Total Claim Amount */}
        <div className="rounded-xl border border-slate-200 bg-white p-3.5 shadow-2xs space-y-1">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Total Statutory Claim</p>
          <p className="font-mono text-xl font-extrabold text-[#0c2340] tabular-nums">
            {formatPaiseToRupees(totalPayablePaise)}
          </p>
          <p className="text-xs text-slate-500 font-medium">
            {isPartiallyPaid ? "Outstanding Balance + Accrued Interest" : "Principal + Accrued Interest"}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2 text-xs sm:text-sm text-amber-900 font-medium bg-amber-50/60 p-3 rounded-xl border border-amber-200/60">
        <Calculator className="h-4 w-4 text-amber-700 shrink-0" />
        <span>Statute: Compounding monthly on overdue balance at 3&times; RBI Bank Rate from the day following the 45-day statutory limit.</span>
      </div>
    </div>
  );
}