/** Audit Log Viewer Page for Phase 5.
 *
 * Admins can view and verify tamper-evident audit logs.
 */
import { AuditLogViewer } from "@/components/audit/AuditLogViewer";
import { ProtectedRoute } from "@/components/ProtectedRoute";

export function AuditPage() {
  return (
    <ProtectedRoute requiredRole="Admin">
      <div className="container mx-auto py-6">
        <h1 className="text-2xl font-bold mb-6">Audit Logs</h1>
        <AuditLogViewer />
      </div>
    </ProtectedRoute>
  );
}
