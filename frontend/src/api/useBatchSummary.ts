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

export function useRunBatch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => fetchApi<{ batch_id: string }>("/api/batches/run", { method: "POST" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["batches"] });
      queryClient.invalidateQueries({ queryKey: ["batchSummary"] });
      queryClient.invalidateQueries({ queryKey: ["cases"] });
      queryClient.invalidateQueries({ queryKey: ["audit"] });
    },
  });
}
