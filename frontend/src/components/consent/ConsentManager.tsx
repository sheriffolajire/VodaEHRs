/** Consent Manager Component for Phase 5.
 *
 * Patients can view and manage consent grants for clinicians.
 */
import { useState, useEffect } from "react";
import { Shield, ShieldCheck, ShieldAlert, Clock, User, Trash2 } from "lucide-react";
import { consentService, type Consent } from "@/services/consentService";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ConsentGrantDialog } from "./ConsentGrantDialog";

const recordTypeLabels: Record<string, string> = {
  diagnosis: "Diagnosis",
  medication: "Medication",
  nursing_note: "Nursing Notes",
  lab_result: "Lab Results",
  imaging: "Imaging",
  other: "Other",
};

export function ConsentManager() {
  useAuth(); // Ensure user is authenticated
  const [consents, setConsents] = useState<Consent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showGrantDialog, setShowGrantDialog] = useState(false);

  const fetchConsents = async () => {
    try {
      setIsLoading(true);
      const data = await consentService.listConsents();
      setConsents(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load consents");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchConsents();
  }, []);

  const handleRevoke = async (consentId: string) => {
    if (!confirm("Are you sure you want to revoke this consent?")) return;
    
    try {
      await consentService.revokeConsent(consentId);
      await fetchConsents();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to revoke consent");
    }
  };

  const activeConsents = consents.filter((c) => c.is_active);
  const revokedConsents = consents.filter((c) => !c.is_active);

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-primary" />
              Consent Management
            </CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Manage which clinicians can access your medical records
            </p>
          </div>
          <Button onClick={() => setShowGrantDialog(true)}>
            Grant Consent
          </Button>
        </CardHeader>
        <CardContent>
          {error && (
            <Alert variant="destructive" className="mb-4">
              <ShieldAlert className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Active Consents */}
          <div className="space-y-4">
            <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
              Active Consents ({activeConsents.length})
            </h3>
            {activeConsents.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Shield className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>No active consents</p>
                <p className="text-sm">Grant consent to allow clinicians to access your records</p>
              </div>
            ) : (
              <div className="grid gap-3">
                {activeConsents.map((consent) => (
                  <div
                    key={consent.id}
                    className="flex items-center justify-between p-4 border rounded-lg bg-card"
                  >
                    <div className="flex items-center gap-4">
                      <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                        <User className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <div className="font-medium">
                          {consent.clinician_name 
                            ? `Dr. ${consent.clinician_name}` 
                            : `Dr. ${consent.clinician_id.slice(0, 8)}...`}
                        </div>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Badge variant="secondary">
                            {recordTypeLabels[consent.record_type] || consent.record_type}
                          </Badge>
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            Granted {new Date(consent.granted_at).toLocaleDateString()}
                          </span>
                        </div>
                        {consent.expires_at && (
                          <div className="text-xs text-muted-foreground">
                            Expires: {new Date(consent.expires_at).toLocaleDateString()}
                          </div>
                        )}
                      </div>
                    </div>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleRevoke(consent.id)}
                    >
                      <Trash2 className="h-4 w-4 mr-1" />
                      Revoke
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Revoked Consents */}
          {revokedConsents.length > 0 && (
            <div className="mt-8 space-y-4">
              <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
                Revoked/Expired ({revokedConsents.length})
              </h3>
              <div className="grid gap-3 opacity-60">
                {revokedConsents.map((consent) => (
                  <div
                    key={consent.id}
                    className="flex items-center justify-between p-4 border rounded-lg bg-muted"
                  >
                    <div className="flex items-center gap-4">
                      <div className="h-10 w-10 rounded-full bg-muted flex items-center justify-center">
                        <User className="h-5 w-5 text-muted-foreground" />
                      </div>
                      <div>
                        <div className="font-medium line-through">
                          {consent.clinician_name 
                            ? `Dr. ${consent.clinician_name}` 
                            : `Dr. ${consent.clinician_id.slice(0, 8)}...`}
                        </div>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Badge variant="outline">
                            {recordTypeLabels[consent.record_type] || consent.record_type}
                          </Badge>
                          {consent.revoked_at && (
                            <span>Revoked {new Date(consent.revoked_at).toLocaleDateString()}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <ConsentGrantDialog
        open={showGrantDialog}
        onOpenChange={setShowGrantDialog}
        onSuccess={fetchConsents}
      />
    </div>
  );
}
