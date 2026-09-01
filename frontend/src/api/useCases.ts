import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchApi } from "./client";
import { AbandonedOrder, Invoice, PaymentCase } from "@/types/api";

export function useCases(module: "A" | "B" | "C", batchId?: string | null, status?: string) {
  return useQuery({
    queryKey: ["cases", module, batchId, status],
    queryFn: async () => {
      const queryParams = new URLSearchParams({ module });
      if (batchId) queryParams.append("batch_id", batchId);
      if (status && status !== "ALL") queryParams.append("status", status.toLowerCase());
      const res = await fetchApi<{ count: number; cases: any[] } | any[]>(
        `/api/cases?${queryParams.toString()}`
      );
      const items = Array.isArray(res) ? res : res?.cases || [];
      return items as PaymentCase[] | Invoice[] | AbandonedOrder[];
    },
    refetchInterval: 5000,
  });
}


export function useCaseDetail(module: "A" | "B" | "C", caseId: string) {
  return useQuery({
    queryKey: ["caseDetail", module, caseId],
    queryFn: () => fetchApi<PaymentCase | Invoice | AbandonedOrder>(`/api/cases/${module}/${caseId}`),
    enabled: Boolean(caseId),
  });
}

export function useGenerateLink() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ module, caseId }: { module: "A" | "B" | "C"; caseId: string }) =>
      fetchApi<{
        status: string;
        module: string;
        case_id: string;
        payment_link_id: string;
        short_url: string;
        amount_paise: number;
        amount_inr: number;
      }>(`/api/cases/${module}/${caseId}/create-link`, {
        method: "POST",
      }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["cases", variables.module] });
      queryClient.invalidateQueries({ queryKey: ["caseDetail", variables.module, variables.caseId] });
      queryClient.invalidateQueries({ queryKey: ["batchSummary"] });
    },
  });
}

export function useSimulateWebhook() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ module, caseId }: { module: "A" | "B" | "C"; caseId: string }) =>
      fetchApi<{
        status: string;
        module: string;
        case_id: string;
        simulated_payment_id: string;
        amount_inr: number;
        recovery: any;
      }>(`/api/cases/${module}/${caseId}/simulate-webhook`, {
        method: "POST",
      }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["cases", variables.module] });
      queryClient.invalidateQueries({ queryKey: ["caseDetail", variables.module, variables.caseId] });
      queryClient.invalidateQueries({ queryKey: ["batchSummary"] });
    },
  });
}

export function useApproveRung4() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (invoiceId: string) =>
      fetchApi<{ status: string; invoice_id: string; current_rung: number }>(
        `/api/cases/invoices/${invoiceId}/approve`,
        { method: "POST" }
      ),
    onSuccess: (_, invoiceId) => {
      queryClient.invalidateQueries({ queryKey: ["cases", "B"] });
      queryClient.invalidateQueries({ queryKey: ["caseDetail", "B", invoiceId] });
      queryClient.invalidateQueries({ queryKey: ["batchSummary"] });
    },
  });
}

