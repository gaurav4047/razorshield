import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchApi } from "./client";
import { Batch, BatchSummary } from "@/types/api";

export function useBatches() {
  return useQuery({
    queryKey: ["batches"],
    queryFn: () => fetchApi<Batch[]>("/api/batches"),
  });
}

export function useBatchSummary(batchId: string | null) {
  return useQuery({
    queryKey: ["batchSummary", batchId],
    queryFn: () => fetchApi<BatchSummary>(`/api/batches/${batchId}/summary`),
    enabled: Boolean(batchId),
    refetchInterval: 3000,
  });
}

export function useBatchPattern(batchId: string | null, module: string = "A") {
  return useQuery({
    queryKey: ["batchPattern", batchId, module],
    queryFn: () =>
      fetchApi<{
        batch_id: string;
        module: string;
        findings: Array<{
          module?: string;
          title?: string;
          badge_label?: string;
          stat_badge_primary?: string;
          stat_badge_secondary?: string;
          rule_enforcement_title?: string;
          rule_enforcement_detail?: string;
          rule_enforcement_outcome?: string;
          grouping_description: string;
          bucket_count: number;
          total_cases_in_scope?: number;
          total_count?: number;
          observed_share: number;
          expected_share: number;
          excess_ratio: number;
          narration: string;
        }>;
      }>(`/api/batches/${batchId}/pattern?module=${module}`),
    enabled: Boolean(batchId),
    staleTime: 60000,
  });
}

export function useRunBatch(onSuccessCallback?: (batchId: string) => void) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      fetchApi<{ batch_id: string }>("/api/batches/run", {
        method: "POST",
        body: JSON.stringify({}),
      }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["batches"] });
      queryClient.invalidateQueries({ queryKey: ["batchSummary"] });
      queryClient.invalidateQueries({ queryKey: ["batchPattern"] });
      queryClient.invalidateQueries({ queryKey: ["cases"] });
      queryClient.invalidateQueries({ queryKey: ["audit"] });
      if (onSuccessCallback && data?.batch_id) {
        onSuccessCallback(data.batch_id);
      }
    },
  });
}

