/** Consent Grant Dialog Component for Phase 5.
 *
 * Dialog for patients to grant consent to clinicians.
 */
import { useState, useEffect } from "react";
import { ShieldCheck, Loader2, User, Stethoscope } from "lucide-react";
import { consentService } from "@/services/consentService";
import { listClinicians } from "@/services/userService";
import type { AuthUser } from "@/types/auth";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";

interface ConsentGrantDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

const recordTypes = [
  { value: "diagnosis", label: "Diagnosis" },
  { value: "medication", label: "Medication" },
  { value: "nursing_note", label: "Nursing Notes" },
  { value: "lab_result", label: "Lab Results" },
  { value: "imaging", label: "Imaging" },
  { value: "other", label: "Other" },
];

export function ConsentGrantDialog({
  open,
  onOpenChange,
  onSuccess,
}: ConsentGrantDialogProps) {
  const [clinicianId, setClinicianId] = useState("");
  const [recordType, setRecordType] = useState("");
  const [clinicians, setClinicians] = useState<AuthUser[]>([]);
  const [isLoadingClinicians, setIsLoadingClinicians] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load clinicians when dialog opens
  useEffect(() => {
    if (open) {
      loadClinicians();
    }
  }, [open]);

  const loadClinicians = async () => {
    try {
      setIsLoadingClinicians(true);
      const data = await listClinicians();
      setClinicians(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load clinicians");
    } finally {
      setIsLoadingClinicians(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!clinicianId.trim() || !recordType) {
      setError("Please select a clinician and record type");
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      
      await consentService.grantConsent({
        clinician_id: clinicianId.trim(),
        record_type: recordType,
      });
      
      setClinicianId("");
      setRecordType("");
      onOpenChange(false);
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to grant consent");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      setClinicianId("");
      setRecordType("");
      setError(null);
      onOpenChange(false);
    }
  };

  // Get selected clinician details
  const selectedClinician = clinicians.find(c => c.id === clinicianId);

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-primary" />
            Grant Consent
          </DialogTitle>
          <DialogDescription>
            Grant a clinician permission to access your medical records of a specific type.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="space-y-2">
            <Label htmlFor="clinician">Select Clinician</Label>
            <Select
              value={clinicianId}
              onValueChange={setClinicianId}
              disabled={isSubmitting || isLoadingClinicians}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder={isLoadingClinicians ? "Loading clinicians..." : "Select a clinician"} />
              </SelectTrigger>
              <SelectContent className="z-[100] w-full min-w-[var(--radix-select-trigger-width)]">
                {clinicians.length === 0 && !isLoadingClinicians && (
                  <SelectItem value="" disabled>
                    No clinicians available
                  </SelectItem>
                )}
                {clinicians.map((clinician) => (
                  <SelectItem key={clinician.id} value={clinician.id}>
                    <div className="flex items-center gap-2">
                      {clinician.role?.name === "Doctor" ? (
                        <Stethoscope className="h-4 w-4 text-blue-500" />
                      ) : (
                        <User className="h-4 w-4 text-green-500" />
                      )}
                      <span>
                        Dr. {clinician.first_name} {clinician.last_name}
                      </span>
                      <Badge variant="secondary" className="text-xs">
                        {clinician.role?.name === "Doctor" ? "Doctor" : "Nurse"}
                      </Badge>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            {/* Selected clinician info */}
            {selectedClinician && (
              <div className="p-3 bg-muted rounded-lg mt-2">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                    {selectedClinician.role?.name === "Doctor" ? (
                      <Stethoscope className="h-5 w-5 text-blue-500" />
                    ) : (
                      <User className="h-5 w-5 text-green-500" />
                    )}
                  </div>
                  <div>
                    <div className="font-medium">
                      Dr. {selectedClinician.first_name} {selectedClinician.last_name}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {selectedClinician.email}
                    </div>
                    <Badge variant="secondary" className="mt-1">
                      {selectedClinician.role?.name === "Doctor" ? "Doctor" : "Nurse"}
                    </Badge>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="recordType">Record Type</Label>
            <Select
              value={recordType}
              onValueChange={setRecordType}
              disabled={isSubmitting}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select record type" />
              </SelectTrigger>
              <SelectContent className="z-[100] w-full min-w-[var(--radix-select-trigger-width)]">
                {recordTypes.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
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
            <Button type="submit" disabled={isSubmitting || !clinicianId || !recordType}>
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Granting...
                </>
              ) : (
                "Grant Consent"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
