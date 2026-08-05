/** Consent Management Page for Phase 5.
 *
 * Patients can manage consent grants for clinicians.
 */
import { ConsentManager } from "@/components/consent/ConsentManager";
import { ProtectedRoute } from "@/components/ProtectedRoute";

export function ConsentPage() {
  return (
    <ProtectedRoute>
      <div className="container mx-auto py-6">
        <h1 className="text-2xl font-bold mb-6">Consent Management</h1>
        <ConsentManager />
      </div>
    </ProtectedRoute>
  );
}
