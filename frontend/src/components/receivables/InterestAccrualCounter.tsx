import { useEffect, useState } from "react";
import { Invoice } from "@/types/api";
import { formatPaiseToRupees } from "@/lib/utils";
import { Card, CardContent } from "@/components/ui/card";
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

    const rbiBankRate = 6.75; // 6.75% published rate
    const statutoryMultiplier = 3;
    const annualRate = (rbiBankRate * statutoryMultiplier) / 100; // 20.25% p.a.
    const monthlyRate = annualRate / 12; // 1.6875% per month

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
      <Card className="border-slate-200 bg-slate-50/70 shadow-xs">
        <CardContent className="p-3 text-xs text-slate-600 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-slate-400 shrink-0" />
          <span>Non-MSME supplier contract: standard commercial terms apply (MSMED Section 16 interest does not apply).</span>
        </CardContent>
      </Card>
    );
  }

  const totalPayablePaise = invoice.amount_paise + accruedPaise;

  return (
    <Card className="border-amber-300 bg-gradient-to-br from-amber-50/80 via-white to-amber-50/30 shadow-sm overflow-hidden">
      <CardContent className="p-4">
        <div className="flex items-center justify-between gap-2 border-b border-amber-200/60 pb-2.5">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-amber-500/20 text-amber-800">
              <Scale className="h-3.5 w-3.5 text-amber-700" />
            </div>
            <span className="text-xs font-bold uppercase tracking-wider text-amber-900">
              MSMED Act 2006, Section 16 Compound Interest
            </span>
          </div>
          <Badge className="border-amber-300 bg-amber-100 text-amber-900 text-[10px] font-semibold gap-1">
            <Flame className="h-3 w-3 text-amber-600 animate-pulse" />
            Accruing Live
          </Badge>
        </div>

        <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
          {/* Days Overdue */}
          <div className="rounded border border-amber-200/60 bg-white p-2.5">
            <p className="text-[11px] font-semibold uppercase text-slate-500">Statutory Due Date</p>
            <p className="mt-0.5 font-mono text-sm font-bold text-slate-900">{invoice.statutory_due_date}</p>
            <p className="text-[10px] text-amber-700 font-medium mt-0.5">
              {daysOverdue > 0 ? `${daysOverdue} days overdue` : "Due today"}
            </p>
          </div>

          {/* Accrued Interest */}
          <div className="rounded border border-amber-300 bg-amber-50/60 p-2.5">
            <p className="text-[11px] font-semibold uppercase text-amber-900">Accrued Interest (Paise)</p>
            <p className="mt-0.5 font-mono text-lg font-bold text-amber-800 tabular-nums">
              {formatPaiseToRupees(accruedPaise)}
            </p>
            <p className="text-[10px] text-slate-500 font-mono mt-0.5">
              @ 20.25% p.a. (3x RBI Bank Rate)
            </p>
          </div>

          {/* Total Claim Amount */}
          <div className="rounded border border-slate-200 bg-white p-2.5">
            <p className="text-[11px] font-semibold uppercase text-slate-500">Total Statutory Claim</p>
            <p className="mt-0.5 font-mono text-lg font-bold text-slate-900 tabular-nums">
              {formatPaiseToRupees(totalPayablePaise)}
            </p>
            <p className="text-[10px] text-slate-500 mt-0.5">
              Principal + Compounded Interest
            </p>
          </div>
        </div>

        <div className="mt-3 flex items-center gap-1.5 text-[11px] text-slate-500 font-mono bg-amber-50/40 p-2 rounded border border-amber-200/40">
          <Calculator className="h-3.5 w-3.5 text-amber-600 shrink-0" />
          <span>Statute: Compounding monthly on overdue balance at 3x RBI Bank Rate from day after due date.</span>
        </div>
      </CardContent>
    </Card>
  );
}

