import { useState, useMemo } from "react";
import { useCases } from "@/api/useCases";
import CaseQueueRow from "./CaseQueueRow";
import DecisionPacket from "@/components/decision-packet/DecisionPacket";
import { 
  Table, 
  TableHeader, 
  TableHead, 
  TableRow, 
  TableBody, 
  TableCell 
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Search, Filter, RefreshCw } from "lucide-react";

interface CaseQueueProps {
  module: "A" | "B" | "C";
  batchId?: string | null;
}

export default function CaseQueue({ module }: CaseQueueProps) {
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const { data: cases, isLoading, refetch, isFetching } = useCases(module);

  // Status Filter Options per Module
  const filterOptions = useMemo(() => {
    if (module === "A") {
      return ["ALL", "OPEN", "RETRIED", "RECOVERED", "CLOSED_UNRECOVERED"];
    } else if (module === "B") {
      return ["ALL", "PENDING", "OVERDUE", "PARTIALLY_PAID", "DISPUTED", "PENDING_HUMAN_APPROVAL", "PAID"];
    } else {
      return ["ALL", "OPEN", "NUDGED", "RECOVERED", "SKIPPED_LOW_VALUE"];
    }
  }, [module]);

  // Filter and Search Processing
  const filteredCases = useMemo(() => {
    if (!cases) return [];
    return cases.filter((item: any) => {
      // Status check
      if (statusFilter !== "ALL") {
        if (item.status?.toUpperCase() !== statusFilter) return false;
      }
      // Search query check
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        if (module === "A") {
          return (
            item.method?.toLowerCase().includes(query) ||
            item.classified_root_cause?.toLowerCase().includes(query) ||
            item.failure_raw_reason?.toLowerCase().includes(query) ||
            item.fault_attribution?.toLowerCase().includes(query)
          );
        } else if (module === "B") {
          return (
            item.invoice_number?.toLowerCase().includes(query) ||
            item.buyer_name?.toLowerCase().includes(query) ||
            item.buyer_archetype?.toLowerCase().includes(query)
          );
        } else if (module === "C") {
          return (
            item.customer_name?.toLowerCase().includes(query) ||
            item.customer_email?.toLowerCase().includes(query) ||
            item.customer_contact?.toLowerCase().includes(query)
          );
        }
      }
      return true;
    });
  }, [cases, statusFilter, searchQuery, module]);

  return (
    <div className="rounded-lg border border-slate-200/80 bg-white shadow-sm overflow-hidden">
      {/* Header Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200/80 bg-slate-50/50 px-4 py-3">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-bold text-slate-900">
            {module === "A" && "Module A: Payment & Mandate Failures"}
            {module === "B" && "Module B: B2B Invoices & MSMED Receivables"}
            {module === "C" && "Module C: Abandoned Checkout Carts"}
          </h2>
          <Badge variant="outline" className="border-slate-200 bg-white text-slate-600 font-mono text-[11px]">
            {filteredCases.length} {filteredCases.length === 1 ? "case" : "cases"}
          </Badge>
        </div>

        {/* Search & Refresh */}
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search cases..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-8 w-48 rounded-md border border-slate-200 bg-white pl-8 pr-3 text-xs text-slate-800 placeholder-slate-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isFetching}
            className="h-8 px-2.5 text-xs text-slate-600 hover:bg-slate-100"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-1.5 border-b border-slate-100 bg-white px-4 py-2 text-xs">
        <span className="flex items-center gap-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400 mr-1">
          <Filter className="h-3 w-3" /> Filter:
        </span>
        {filterOptions.map((filter) => (
          <button
            key={filter}
            onClick={() => setStatusFilter(filter)}
            className={`rounded-full px-2.5 py-1 text-[11px] font-medium transition-all ${
              statusFilter === filter
                ? "bg-slate-900 text-white shadow-xs"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            {filter.replace("_", " ")}
          </button>
        ))}
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto">
        <Table>
          <TableHeader className="bg-slate-50 text-[11px] font-bold uppercase tracking-wider text-slate-500">
            <TableRow>
              {module === "A" && (
                <>
                  <TableHead className="w-[100px]">Method</TableHead>
                  <TableHead className="w-[130px]">Amount</TableHead>
                  <TableHead>Root Cause Taxonomy</TableHead>
                  <TableHead className="w-[150px]">Fault Attribution</TableHead>
                  <TableHead className="w-[120px]">Payment Link</TableHead>
                  <TableHead className="text-right w-[120px]">Status</TableHead>
                </>
              )}
              {module === "B" && (
                <>
                  <TableHead className="w-[120px]">Invoice No</TableHead>
                  <TableHead>Buyer Counterparty</TableHead>
                  <TableHead className="w-[140px]">Principal</TableHead>
                  <TableHead className="w-[180px]">Escalation Ladder</TableHead>
                  <TableHead className="text-right w-[140px]">Status</TableHead>
                </>
              )}
              {module === "C" && (
                <>
                  <TableHead>Customer</TableHead>
                  <TableHead className="w-[130px]">Cart Value</TableHead>
                  <TableHead className="w-[180px]">Abandonment Time</TableHead>
                  <TableHead className="w-[160px]">Nudge Cap Policy</TableHead>
                  <TableHead className="text-right w-[120px]">Status</TableHead>
                </>
              )}
            </TableRow>
          </TableHeader>

          <TableBody>
            {isLoading ? (
              [1, 2, 3, 4, 5, 6].map((i) => (
                <TableRow key={i}>
                  <TableCell colSpan={6} className="py-4">
                    <Skeleton className="h-5 w-full bg-slate-100" />
                  </TableCell>
                </TableRow>
              ))
            ) : filteredCases.length > 0 ? (
              filteredCases.map((item: any) => (
                <CaseQueueRow
                  key={item.id}
                  module={module}
                  item={item}
                  onClick={() => setSelectedCaseId(item.id)}
                />
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={6} className="py-12 text-center text-xs text-slate-400">
                  No cases found matching filter "{statusFilter}".
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Decision Packet Modal */}
      {selectedCaseId && (
        <DecisionPacket
          module={module}
          caseId={selectedCaseId}
          onClose={() => setSelectedCaseId(null)}
        />
      )}
    </div>
  );
}

