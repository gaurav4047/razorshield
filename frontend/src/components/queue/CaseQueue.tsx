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
import { Search, RefreshCw, SlidersHorizontal, ChevronLeft, ChevronRight, CreditCard, Building2, ShoppingCart } from "lucide-react";

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
    <div className="rounded-2xl border border-slate-800 bg-slate-900/90 shadow-2xl backdrop-blur-xl overflow-hidden">
      {/* Header Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 bg-slate-950/60 px-6 py-5">
        <div className="flex items-center gap-3.5">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-slate-800/80 border border-slate-700/60 shadow-inner">
            {module === "A" && <CreditCard className="h-5 w-5 text-blue-400" />}
            {module === "B" && <Building2 className="h-5 w-5 text-amber-400" />}
            {module === "C" && <ShoppingCart className="h-5 w-5 text-indigo-400" />}
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2.5">
              <h2 className="text-base sm:text-lg font-bold tracking-tight text-white">
                {module === "A" && "Stream A: Payment & Mandate Recovery"}
                {module === "B" && "Stream B: B2B Invoices & MSMED Act Recovery"}
                {module === "C" && "Stream C: Abandoned Checkout Protection"}
              </h2>
              <Badge className="border-blue-500/30 bg-blue-500/15 text-blue-300 font-bold text-xs px-2.5 py-0.5 rounded-full shadow-xs">
                {filteredCases.length} {filteredCases.length === 1 ? "case" : "cases"}
              </Badge>
            </div>
            <p className="text-xs text-slate-400 font-medium mt-0.5">
              {module === "A" && "Infrastructure-aware retry pacing, bank switch monitoring & mandate re-engagement"}
              {module === "B" && "MSMED Act 2006 statutory ladder with Section 16 monthly compounding interest"}
              {module === "C" && "Rule 12 floor filtering (< ₹200) & strict 1-nudge anti-spam caps"}
            </p>
          </div>
        </div>

        {/* Search & Refresh */}
        <div className="flex items-center gap-2.5">
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            <input
              type="text"
              placeholder="Search cases, codes, buyers..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-9 w-52 sm:w-64 rounded-xl border border-slate-700/80 bg-slate-800/80 pl-9.5 pr-3 text-xs sm:text-sm text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 shadow-inner transition-all"
            />
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isFetching}
            className="h-9 px-3 text-xs font-semibold text-slate-300 hover:bg-slate-800 hover:text-white rounded-xl border-slate-700 shadow-sm"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? "animate-spin text-blue-400" : ""}`} />
          </Button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-800 bg-slate-950/30 px-6 py-3 text-xs">
        <span className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-500 mr-2">
          <SlidersHorizontal className="h-3 w-3" /> Filter:
        </span>
        {filterOptions.map((filter) => (
          <button
            key={filter}
            onClick={() => setStatusFilter(filter)}
            className={`rounded-lg px-3 py-1 text-xs font-semibold transition-all ${
              statusFilter === filter
                ? "bg-blue-600 text-white shadow-md shadow-blue-500/25 border border-blue-400/40"
                : "bg-slate-800/80 border border-slate-700/60 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
            }`}
          >
            {filter.replace(/_/g, " ")}
          </button>
        ))}
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto">
        <Table>
          <TableHeader className="bg-slate-950/80 border-b border-slate-800 text-[11px] font-bold uppercase tracking-wider text-slate-400">
            <TableRow className="border-b border-slate-800 hover:bg-transparent">
              {module === "A" && (
                <>
                  <TableHead className="w-[140px] py-3.5 pl-6 text-slate-400">Method</TableHead>
                  <TableHead className="w-[150px] py-3.5 text-slate-400">Amount</TableHead>
                  <TableHead className="py-3.5 text-slate-400">Root Cause Taxonomy</TableHead>
                  <TableHead className="w-[160px] py-3.5 text-slate-400">Attribution</TableHead>
                  <TableHead className="w-[150px] py-3.5 text-slate-400">Recovery Link</TableHead>
                  <TableHead className="w-[140px] py-3.5 text-slate-400">Status</TableHead>
                  <TableHead className="text-right w-[110px] py-3.5 pr-6 text-slate-400">Action</TableHead>
                </>
              )}
              {module === "B" && (
                <>
                  <TableHead className="w-[150px] py-3.5 pl-6 text-slate-400">Invoice No</TableHead>
                  <TableHead className="py-3.5 text-slate-400">Buyer Counterparty</TableHead>
                  <TableHead className="w-[180px] py-3.5 text-slate-400">Principal &amp; Interest</TableHead>
                  <TableHead className="w-[180px] py-3.5 text-slate-400">Escalation Ladder</TableHead>
                  <TableHead className="w-[150px] py-3.5 text-slate-400">Status</TableHead>
                  <TableHead className="text-right w-[110px] py-3.5 pr-6 text-slate-400">Action</TableHead>
                </>
              )}
              {module === "C" && (
                <>
                  <TableHead className="py-3.5 pl-6 text-slate-400">Customer</TableHead>
                  <TableHead className="w-[150px] py-3.5 text-slate-400">Cart Value</TableHead>
                  <TableHead className="w-[190px] py-3.5 text-slate-400">Abandonment Time</TableHead>
                  <TableHead className="w-[180px] py-3.5 text-slate-400">Nudge Cap Policy</TableHead>
                  <TableHead className="w-[150px] py-3.5 text-slate-400">Status</TableHead>
                  <TableHead className="text-right w-[110px] py-3.5 pr-6 text-slate-400">Action</TableHead>
                </>
              )}
            </TableRow>
          </TableHeader>

          <TableBody>
            {isLoading ? (
              [1, 2, 3, 4, 5, 6].map((i) => (
                <TableRow key={i} className="border-b border-slate-800/80">
                  <TableCell colSpan={7} className="py-4">
                    <Skeleton className="h-6 w-full bg-slate-800/80 rounded-lg" />
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
              <TableRow className="border-b border-slate-800">
                <TableCell colSpan={7} className="py-16 text-center text-sm text-slate-400">
                  {cases && cases.length > 0
                    ? `No cases found matching filter "${statusFilter}".`
                    : 'No cases in queue. Click "Run Autonomous Scenario" in the header to generate a batch.'}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination Footer (8 per page) */}
      {filteredCases.length > 0 && (
        <div className="flex flex-wrap items-center justify-between gap-4 border-t border-slate-800 bg-slate-950/60 px-6 py-3.5">
          <div className="text-xs sm:text-sm text-slate-400 font-medium">
            Showing <strong className="text-white font-bold">{(currentPage - 1) * ITEMS_PER_PAGE + 1}</strong> to{" "}
            <strong className="text-white font-bold">
              {Math.min(currentPage * ITEMS_PER_PAGE, filteredCases.length)}
            </strong>{" "}
            of <strong className="text-white font-bold">{filteredCases.length}</strong> cases
          </div>

          <div className="flex items-center gap-1.5">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              className="h-8 px-2.5 rounded-lg border-slate-700 bg-slate-800/80 text-xs text-slate-300 hover:bg-slate-700 hover:text-white disabled:opacity-30 shadow-sm gap-1"
            >
              <ChevronLeft className="h-3.5 w-3.5" />
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
                        <span className="px-1 text-xs text-slate-600 font-bold select-none">...</span>
                      )}
                      <button
                        onClick={() => setCurrentPage(pageNum)}
                        className={`h-8 min-w-[32px] px-2 rounded-lg text-xs font-bold transition-all ${
                          currentPage === pageNum
                            ? "bg-blue-600 text-white shadow-sm shadow-blue-500/25 border border-blue-400/40"
                            : "bg-slate-800/80 border border-slate-700/60 text-slate-400 hover:bg-slate-700 hover:text-white shadow-xs"
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
              className="h-8 px-2.5 rounded-lg border-slate-700 bg-slate-800/80 text-xs text-slate-300 hover:bg-slate-700 hover:text-white disabled:opacity-30 shadow-sm gap-1"
            >
              <span className="hidden sm:inline">Next</span>
              <ChevronRight className="h-3.5 w-3.5" />
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