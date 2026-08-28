import CaseQueue from "@/components/queue/CaseQueue";
import AuditLogStream from "@/components/audit/AuditLogStream";

interface ModuleProps {
  batchId: string | null;
}

export default function ModuleB({ batchId }: ModuleProps) {
  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <div className="lg:col-span-2">
        <CaseQueue module="B" batchId={batchId} />
      </div>
      <div>
        <AuditLogStream batchId={batchId} caseType="invoice" />
      </div>
    </div>
  );
}
