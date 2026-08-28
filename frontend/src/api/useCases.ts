import { useQuery } from "@tanstack/react-query";
import { fetchApi } from "./client";
import { AbandonedOrder, Invoice, PaymentCase } from "@/types/api";

export function useCases(module: "A" | "B" | "C", status?: string) {
  return useQuery({
    queryKey: ["cases", module, status],
    queryFn: () => {
      const queryParams = new URLSearchParams({ module });
      if (status) queryParams.append("status", status);
      return fetchApi<PaymentCase[] | Invoice[] | AbandonedOrder[]>(`/api/cases?${queryParams.toString()}`);
    },
  });
}

export function useCaseDetail(module: "A" | "B" | "C", caseId: string) {
  return useQuery({
    queryKey: ["caseDetail", module, caseId],
    queryFn: () => fetchApi<PaymentCase | Invoice | AbandonedOrder>(`/api/cases/${module}/${caseId}`),
    enabled: Boolean(caseId),
  });
}
