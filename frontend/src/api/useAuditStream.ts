import { useEffect, useState } from "react";
import { AuditLogEntry } from "@/types/api";
import { fetchApi } from "./client";

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || "ws://localhost:8000";

export function useAuditStream(batchId: string | null, caseType?: CaseType) {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (!batchId) return;

    let isMounted = true;

    // Fetch initial history filtered by caseType
    const typeParam = caseType ? `&case_type=${caseType}` : "";
    fetchApi<{ count: number; audit_logs: AuditLogEntry[] } | AuditLogEntry[]>(
      `/api/audit?batch_id=${batchId}${typeParam}&limit=100`
    )
      .then((res) => {
        if (isMounted && res) {
          const items = Array.isArray(res) ? res : res.audit_logs || [];
          setLogs(items);
        }
      })
      .catch((err) => console.error("Failed to fetch initial audit logs", err));


    const wsUrl = `${WS_BASE_URL}/ws/audit?batch_id=${batchId}`;
    let ws: WebSocket | null = null;

    try {
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        if (isMounted) setIsConnected(true);
      };

      ws.onclose = () => {
        if (isMounted) setIsConnected(false);
      };

      ws.onerror = () => {
        if (isMounted) setIsConnected(false);
      };

      ws.onmessage = (event) => {
        try {
          const newEntry: AuditLogEntry = JSON.parse(event.data);
          if (isMounted) {
            if (caseType && newEntry.case_type !== caseType) return;
            setLogs((prev) => {
              if (prev.some((p) => p.id === newEntry.id)) return prev;
              return [newEntry, ...prev];
            });
          }
        } catch (err) {
          console.error("Failed to parse audit log WebSocket message", err);
        }
      };
    } catch (e) {
      console.error("WebSocket connection error:", e);
    }

    return () => {
      isMounted = false;
      if (ws) ws.close();
    };
  }, [batchId, caseType]);

  return { logs, isConnected };
}

