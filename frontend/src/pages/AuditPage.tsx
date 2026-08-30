/** Audit Log Viewer Page for Phase 5.
 *
 * Admins and Auditors can view and verify tamper-evident audit logs.
 */
import { AuditLogViewer } from "@/components/audit/AuditLogViewer";

export function AuditPage() {
  return (
    <div className="container mx-auto py-6">
      <h1 className="text-2xl font-bold mb-6">Audit Logs</h1>
      <AuditLogViewer />
    </div>
  );
}
