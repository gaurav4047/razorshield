import { useState, useMemo, useEffect } from "react";
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
import { Search, Filter, RefreshCw, SlidersHorizontal, ChevronLeft, ChevronRight, CreditCard, Building2, ShoppingCart } from "lucide-react";

interface CaseQueueProps {
  module: "A" | "B" | "C";
  batchId?: string | null;
}

export default function CaseQueue({ module, batchId }: CaseQueueProps) {
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [currentPage, setCurrentPage] = useState<number>(1);
  const ITEMS_PER_PAGE = 8;

  const { data: cases, isLoading, refetch, isFetching } = useCases(module, batchId);

  // Status Filter Options per Module
  const filterOptions = useMemo(() => {
    if (module === "A") {
      return ["ALL", "OPEN", "RETRIED", "RECOVERED", "CLOSED_UNRECOVERED", "ESCALATED"];
    } else if (module === "B") {
      return ["ALL", "PENDING", "OVERDUE", "PARTIALLY_PAID", "DISPUTED", "PENDING_HUMAN_APPROVAL", "PAID", "WRITTEN_OFF"];
    } else {
      return ["ALL", "OPEN", "NUDGED", "RECOVERED", "EXPIRED_UNRECOVERED", "SKIPPED_LOW_VALUE"];
    }
  }, [module]);

  // Reset page when filter or search changes
  useEffect(() => {
    setCurrentPage(1);
  }, [statusFilter, searchQuery, module, batchId]);

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

  const totalPages = Math.ceil(filteredCases.length / ITEMS_PER_PAGE) || 1;
  const paginatedCases = useMemo(() => {
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    return filteredCases.slice(start, start + ITEMS_PER_PAGE);
  }, [filteredCases, currentPage]);

  return (
    <div className="rounded-3xl border border-slate-200/90 bg-white shadow-xs overflow-hidden">
      {/* Header Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-5 border-b border-slate-200/80 bg-slate-50/70 px-7 sm:px-8 py-6">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-white border border-slate-200/90 text-[#0066ff] shadow-sm">
            {module === "A" && <CreditCard className="h-6 w-6 text-[#0066ff]" />}
            {module === "B" && <Building2 className="h-6 w-6 text-amber-700" />}
            {module === "C" && <ShoppingCart className="h-6 w-6 text-[#0066ff]" />}
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <h2 className="text-lg sm:text-xl font-black tracking-tight text-[#0c2340]">
                {module === "A" && "Module A: Payment & Mandate Failures"}
                {module === "B" && "Module B: B2B Invoices & MSMED Receivables"}
                {module === "C" && "Module C: Abandoned Checkout Carts"}
              </h2>
              <Badge className="border-blue-200 bg-blue-50 text-[#0066ff] font-extrabold text-xs px-3 py-1 rounded-full shadow-2xs">
                {filteredCases.length} {filteredCases.length === 1 ? "case" : "cases"}
              </Badge>
            </div>
            <p className="text-xs sm:text-sm text-slate-600 font-medium mt-1">
              {module === "A" && "Infrastructure-aware retry pacing and mandate re-engagement"}
              {module === "B" && "MSMED Act 2006 compliance ladder with Section 16 penal compound interest"}
              {module === "C" && "Rule 12 low-value floor filtering (< ₹200) and strict 1-nudge anti-spam caps"}
            </p>
          </div>
        </div>

        {/* Search & Refresh */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search cases, codes, buyers..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-10 w-60 sm:w-72 rounded-xl border border-slate-200 bg-white pl-10 pr-3.5 text-xs sm:text-sm text-slate-800 placeholder-slate-400 focus:border-[#0066ff] focus:outline-none focus:ring-2 focus:ring-blue-500/20 shadow-2xs transition-all"
            />
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isFetching}
            className="h-10 px-3.5 text-xs sm:text-sm font-semibold text-slate-700 hover:bg-slate-100 rounded-xl border-slate-200 shadow-2xs"
          >
            <RefreshCw className={`h-4 w-4 ${isFetching ? "animate-spin text-[#0066ff]" : ""}`} />
          </Button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-100 bg-slate-50/40 px-7 sm:px-8 py-4 text-xs sm:text-sm">
        <span className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-slate-400 mr-2">
          <SlidersHorizontal className="h-3.5 w-3.5" /> Filter:
        </span>
        {filterOptions.map((filter) => (
          <button
            key={filter}
            onClick={() => setStatusFilter(filter)}
            className={`rounded-xl px-3.5 py-1.5 text-xs font-bold transition-all ${
              statusFilter === filter
                ? "bg-[#0066ff] text-white shadow-sm shadow-blue-500/25"
                : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 hover:text-slate-900 shadow-2xs"
            }`}
          >
            {filter.replace(/_/g, " ")}
          </button>
        ))}
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto">
        <Table>
          <TableHeader className="bg-slate-50/90 border-b border-slate-200/80 text-xs font-extrabold uppercase tracking-wider text-slate-500">
            <TableRow>
              {module === "A" && (
                <>
                  <TableHead className="w-[130px] py-4 pl-6">Method</TableHead>
                  <TableHead className="w-[150px] py-4">Amount</TableHead>
                  <TableHead className="py-4">Root Cause Taxonomy</TableHead>
                  <TableHead className="w-[160px] py-4">Attribution</TableHead>
                  <TableHead className="w-[150px] py-4">Recovery Link</TableHead>
                  <TableHead className="w-[140px] py-4">Status</TableHead>
                  <TableHead className="text-right w-[110px] py-4 pr-6">Action</TableHead>
                </>
              )}
              {module === "B" && (
                <>
                  <TableHead className="w-[150px] py-4 pl-6">Invoice No</TableHead>
                  <TableHead className="py-4">Buyer Counterparty</TableHead>
                  <TableHead className="w-[170px] py-4">Principal &amp; Interest</TableHead>
                  <TableHead className="w-[180px] py-4">Escalation Ladder</TableHead>
                  <TableHead className="w-[150px] py-4">Status</TableHead>
                  <TableHead className="text-right w-[110px] py-4 pr-6">Action</TableHead>
                </>
              )}
              {module === "C" && (
                <>
                  <TableHead className="py-4 pl-6">Customer</TableHead>
                  <TableHead className="w-[150px] py-4">Cart Value</TableHead>
                  <TableHead className="w-[190px] py-4">Abandonment Time</TableHead>
                  <TableHead className="w-[180px] py-4">Nudge Cap Policy</TableHead>
                  <TableHead className="w-[150px] py-4">Status</TableHead>
                  <TableHead className="text-right w-[110px] py-4 pr-6">Action</TableHead>
                </>
              )}
            </TableRow>
          </TableHeader>

          <TableBody>
            {isLoading ? (
              [1, 2, 3, 4, 5, 6].map((i) => (
                <TableRow key={i}>
                  <TableCell colSpan={7} className="py-5">
                    <Skeleton className="h-6 w-full bg-slate-100 rounded-lg" />
                  </TableCell>
                </TableRow>
              ))
            ) : paginatedCases.length > 0 ? (
              paginatedCases.map((item: any) => (
                <CaseQueueRow
                  key={item.id}
                  module={module}
                  item={item}
                  onClick={() => setSelectedCaseId(item.id)}
                />
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={7} className="py-16 text-center text-sm text-slate-500">
                  {cases && cases.length > 0
                    ? `No cases found matching filter "${statusFilter}".`
                    : "No cases in queue. Click \"Run Synthetic Scenario\" in the header to generate a batch."}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination Footer (8 per page) */}
      {filteredCases.length > 0 && (
        <div className="flex flex-wrap items-center justify-between gap-4 border-t border-slate-200/80 bg-slate-50/60 px-6 py-3.5">
          <div className="text-xs sm:text-sm text-slate-600 font-medium">
            Showing <strong className="text-[#0c2340] font-bold">{(currentPage - 1) * ITEMS_PER_PAGE + 1}</strong> to{" "}
            <strong className="text-[#0c2340] font-bold">
              {Math.min(currentPage * ITEMS_PER_PAGE, filteredCases.length)}
            </strong>{" "}
            of <strong className="text-[#0c2340] font-bold">{filteredCases.length}</strong> cases
          </div>

          <div className="flex items-center gap-1.5">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              className="h-9 px-3 rounded-xl border-slate-200 text-xs sm:text-sm font-semibold text-slate-700 hover:bg-white hover:border-slate-300 disabled:opacity-40 shadow-2xs gap-1"
            >
              <ChevronLeft className="h-4 w-4" />
              <span className="hidden sm:inline">Previous</span>
            </Button>

            {/* Page Numbers */}
            <div className="flex items-center gap-1">
              {Array.from({ length: totalPages }, (_, idx) => idx + 1)
                .filter((p) => {
                  if (totalPages <= 7) return true;
                  if (p === 1 || p === totalPages) return true;
                  return Math.abs(p - currentPage) <= 1;
                })
                .map((pageNum, idx, arr) => {
                  const showEllipsisBefore = idx > 0 && pageNum - arr[idx - 1] > 1;
                  return (
                    <div key={pageNum} className="flex items-center">
                      {showEllipsisBefore && (
                        <span className="px-1 text-xs text-slate-400 font-bold select-none">...</span>
                      )}
                      <button
                        onClick={() => setCurrentPage(pageNum)}
                        className={`h-9 min-w-[36px] px-2.5 rounded-xl text-xs sm:text-sm font-bold transition-all ${
                          currentPage === pageNum
                            ? "bg-[#0066ff] text-white shadow-sm shadow-blue-500/25"
                            : "bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 hover:border-slate-300 shadow-2xs"
                        }`}
                      >
                        {pageNum}
                      </button>
                    </div>
                  );
                })}
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages}
              className="h-9 px-3 rounded-xl border-slate-200 text-xs sm:text-sm font-semibold text-slate-700 hover:bg-white hover:border-slate-300 disabled:opacity-40 shadow-2xs gap-1"
            >
              <span className="hidden sm:inline">Next</span>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

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