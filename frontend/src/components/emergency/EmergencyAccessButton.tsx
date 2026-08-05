/** Emergency Access Button Component for Phase 5.
 *
 * Doctors can request emergency (break-glass) access to patient records.
 */
import { useState } from "react";
import { AlertTriangle, Clock, Loader2, ShieldAlert } from "lucide-react";
import { emergencyAccessService } from "@/services/emergencyAccessService";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";

interface EmergencyAccessButtonProps {
  patientId: string;
  patientName?: string;
  onSuccess?: () => void;
}

export function EmergencyAccessButton({
  patientId,
  patientName,
  onSuccess,
}: EmergencyAccessButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [reason, setReason] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [granted, setGranted] = useState(false);
  const [expiresAt, setExpiresAt] = useState<string | null>(null);

  const handleOpen = () => {
    setIsOpen(true);
    setError(null);
    setGranted(false);
    setReason("");
  };

  const handleClose = () => {
    if (!isSubmitting) {
      setIsOpen(false);
      setError(null);
      setGranted(false);
      setReason("");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!reason.trim() || reason.trim().length < 20) {
      setError("Please provide a detailed reason (minimum 20 characters)");
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      const result = await emergencyAccessService.requestEmergencyAccess({
        patient_id: patientId,
        reason: reason.trim(),
      });

      setGranted(true);
      setExpiresAt(result.expires_at);
      
      if (onSuccess) {
        onSuccess();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to request emergency access");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <Button
        variant="destructive"
        size="sm"
        onClick={handleOpen}
        className="gap-2"
      >
        <AlertTriangle className="h-4 w-4" />
        Emergency Access
      </Button>

      <Dialog open={isOpen} onOpenChange={handleClose}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-destructive">
              <ShieldAlert className="h-5 w-5" />
              Emergency Access (Break-Glass)
            </DialogTitle>
            <DialogDescription>
              Request emergency access to bypass consent requirements.
              This will be logged as high-priority and requires a mandatory reason.
            </DialogDescription>
          </DialogHeader>

          {!granted ? (
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div className="bg-muted p-3 rounded-md">
                <div className="text-sm font-medium">Patient</div>
                <div className="text-sm text-muted-foreground">
                  {patientName || patientId}
                </div>
              </div>

              <Alert className="bg-amber-50 border-amber-200">
                <Clock className="h-4 w-4 text-amber-600" />
                <AlertDescription className="text-amber-800">
                  Emergency access lasts for <strong>30 minutes</strong> and is audited.
                </AlertDescription>
              </Alert>

              <div className="space-y-2">
                <Label htmlFor="reason">
                  Reason for Emergency Access
                  <span className="text-destructive">*</span>
                </Label>
                <Textarea
                  id="reason"
                  placeholder="Describe the emergency situation requiring immediate access to patient records..."
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  disabled={isSubmitting}
                  rows={4}
                  className="resize-none"
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Minimum 20 characters required</span>
                  <span className={reason.length < 20 ? "text-destructive" : "text-green-600"}>
                    {reason.length} chars
                  </span>
                </div>
              </div>

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleClose}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="destructive"
                  disabled={isSubmitting || reason.trim().length < 20}
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Requesting...
                    </>
                  ) : (
                    "Request Emergency Access"
                  )}
                </Button>
              </DialogFooter>
            </form>
          ) : (
            <div className="space-y-4">
              <Alert className="bg-green-50 border-green-200">
                <ShieldAlert className="h-4 w-4 text-green-600" />
                <AlertDescription className="text-green-800">
                  Emergency access granted successfully!
                </AlertDescription>
              </Alert>

              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-muted rounded-md">
                  <span className="text-sm font-medium">Duration</span>
                  <Badge variant="secondary">30 minutes</Badge>
                </div>
                
                {expiresAt && (
                  <div className="flex items-center justify-between p-3 bg-muted rounded-md">
                    <span className="text-sm font-medium">Expires At</span>
                    <span className="text-sm">
                      {new Date(expiresAt).toLocaleString()}
                    </span>
                  </div>
                )}

                <div className="flex items-center justify-between p-3 bg-amber-50 rounded-md border border-amber-200">
                  <span className="text-sm font-medium text-amber-900">Audit Priority</span>
                  <Badge className="bg-amber-600">HIGH</Badge>
                </div>
              </div>

              <DialogFooter>
                <Button onClick={handleClose}>Close</Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
