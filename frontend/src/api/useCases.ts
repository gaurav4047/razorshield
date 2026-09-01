import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchApi } from "./client";
import { AbandonedOrder, Invoice, PaymentCase } from "@/types/api";

export function useCases(module: "A" | "B" | "C", status?: string) {
  return useQuery({
    queryKey: ["cases", module, status],
    queryFn: () => {
      const queryParams = new URLSearchParams({ module });
      if (status && status !== "ALL") queryParams.append("status", status);
      return fetchApi<PaymentCase[] | Invoice[] | AbandonedOrder[]>(`/api/cases?${queryParams.toString()}`);
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

