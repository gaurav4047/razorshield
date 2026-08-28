import { useEffect, useState } from "react";
import { AuditLogEntry } from "@/types/api";

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || "ws://localhost:8000";

export function useAuditStream(batchId: string | null) {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (!batchId) return;

    const ws = new WebSocket(`${WS_BASE_URL}/ws/audit?batch_id=${batchId}`);

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);
    ws.onerror = () => setIsConnected(false);

    ws.onmessage = (event) => {
      try {
        const newEntry: AuditLogEntry = JSON.parse(event.data);
        setLogs((prev) => [newEntry, ...prev]);
      } catch (err) {
        console.error("Failed to parse audit log WebSocket message", err);
      }
    };

    return () => {
      ws.close();
    };
  }, [batchId]);

  return { logs, isConnected };
}
