/** Emergency Access Admin Page.
 *
 * Admins can view and manage emergency access (break-glass) requests.
 */
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Clock, User, X, RefreshCw, Check, XCircle } from "lucide-react";
import { emergencyAccessService, type EmergencyAccess } from "@/services/emergencyAccessService";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export function EmergencyAccessAdminPage() {
  const queryClient = useQueryClient();
  const [selectedEmergency, setSelectedEmergency] = useState<EmergencyAccess | null>(null);
  const [isRevokeDialogOpen, setIsRevokeDialogOpen] = useState(false);
  const [isApproveDialogOpen, setIsApproveDialogOpen] = useState(false);
  const [isRejectDialogOpen, setIsRejectDialogOpen] = useState(false);
  const [reviewNotes, setReviewNotes] = useState("");

  // Fetch all emergency access
  const emergenciesQuery = useQuery({
    queryKey: ["emergency-access-admin"],
    queryFn: emergencyAccessService.listEmergencyAccess,
  });

  // Approve mutation
  const approveMutation = useMutation({
    mutationFn: ({ id, notes }: { id: string; notes?: string }) =>
      emergencyAccessService.approveEmergencyAccess(id, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["emergency-access-admin"] });
      setIsApproveDialogOpen(false);
      setSelectedEmergency(null);
      setReviewNotes("");
    },
  });

  // Reject mutation
  const rejectMutation = useMutation({
    mutationFn: ({ id, notes }: { id: string; notes?: string }) =>
      emergencyAccessService.rejectEmergencyAccess(id, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["emergency-access-admin"] });
      setIsRejectDialogOpen(false);
      setSelectedEmergency(null);
      setReviewNotes("");
    },
  });

  // Revoke mutation
  const revokeMutation = useMutation({
    mutationFn: (emergencyId: string) =>
      emergencyAccessService.revokeEmergencyAccess(emergencyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["emergency-access-admin"] });
      setIsRevokeDialogOpen(false);
      setSelectedEmergency(null);
    },
  });

  const handleApprove = (emergency: EmergencyAccess) => {
    setSelectedEmergency(emergency);
    setIsApproveDialogOpen(true);
  };

  const handleReject = (emergency: EmergencyAccess) => {
    setSelectedEmergency(emergency);
    setIsRejectDialogOpen(true);
  };

  const handleRevoke = (emergency: EmergencyAccess) => {
    setSelectedEmergency(emergency);
    setIsRevokeDialogOpen(true);
  };

  const confirmApprove = () => {
    if (selectedEmergency) {
      approveMutation.mutate({ id: selectedEmergency.id, notes: reviewNotes });
    }
  };

  const confirmReject = () => {
    if (selectedEmergency) {
      rejectMutation.mutate({ id: selectedEmergency.id, notes: reviewNotes });
    }
  };

  const confirmRevoke = () => {
    if (selectedEmergency) {
      revokeMutation.mutate(selectedEmergency.id);
    }
  };

  // Format remaining time
  const formatRemainingTime = (minutes: number) => {
    if (minutes <= 0) return "Expired";
    if (minutes < 1) return "< 1 min";
    if (minutes < 60) return `${Math.floor(minutes)} min`;
    const hours = Math.floor(minutes / 60);
    const mins = Math.floor(minutes % 60);
    return `${hours}h ${mins}m`;
  };

  // Format date
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold">Emergency Access Management</h2>
        <p className="text-sm text-muted-foreground">
          View and manage emergency (break-glass) access requests
        </p>
      </div>

      {/* Error Alert */}
      {emergenciesQuery.isError && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            {emergenciesQuery.error instanceof Error
              ? emergenciesQuery.error.message
              : "Failed to load emergency access requests"}
          </AlertDescription>
        </Alert>
      )}

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Pending Approval
            </CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {emergenciesQuery.data?.filter((e) => e.status === "pending").length ?? 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Awaiting admin review
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Active
            </CardTitle>
            <AlertTriangle className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {emergenciesQuery.data?.filter((e) => e.is_active).length ?? 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Currently active emergency access
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Expiring Soon
            </CardTitle>
            <Clock className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {emergenciesQuery.data?.filter(
                (e) => e.is_active && e.remaining_minutes < 10
              ).length ?? 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Expires within 10 minutes
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Requests</CardTitle>
            <User className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {emergenciesQuery.data?.length ?? 0}
            </div>
            <p className="text-xs text-muted-foreground">
              All emergency access requests
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Emergency Access List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Emergency Access Requests</CardTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={() => emergenciesQuery.refetch()}
              disabled={emergenciesQuery.isFetching}
            >
              <RefreshCw
                className={`h-4 w-4 mr-2 ${
                  emergenciesQuery.isFetching ? "animate-spin" : ""
                }`}
              />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {emergenciesQuery.isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            </div>
          ) : emergenciesQuery.data?.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <AlertTriangle className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No emergency access requests found.</p>
              <p className="text-sm">
                Emergency access requests will appear here when doctors request them.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {emergenciesQuery.data?.map((emergency) => (
                <div
                  key={emergency.id}
                  className={`rounded-lg border p-4 ${
                    emergency.is_active
                      ? "border-orange-200 bg-orange-50 dark:border-orange-900 dark:bg-orange-950"
                      : "border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-900"
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium">
                          Emergency Access Request
                        </h3>
                        {emergency.status === "pending" ? (
                          <Badge className="bg-yellow-100 text-yellow-800 hover:bg-yellow-100">
                            Pending Approval
                          </Badge>
                        ) : emergency.status === "approved" ? (
                          emergency.is_active ? (
                            <Badge className="bg-orange-100 text-orange-800 hover:bg-orange-100">
                              Active
                            </Badge>
                          ) : (
                            <Badge variant="secondary">Expired</Badge>
                          )
                        ) : emergency.status === "rejected" ? (
                          <Badge className="bg-red-100 text-red-800 hover:bg-red-100">
                            Rejected
                          </Badge>
                        ) : (
                          <Badge variant="secondary">Inactive</Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        Clinician: {emergency.clinician_name || emergency.clinician_id}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        Patient: {emergency.patient_name || emergency.patient_id}
                      </p>
                    </div>
                    <div className="text-right">
                      {emergency.is_active && (
                        <div className="text-sm font-medium text-orange-600">
                          {formatRemainingTime(emergency.remaining_minutes)} remaining
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="mt-4 space-y-2">
                    <div>
                      <span className="text-xs font-medium text-muted-foreground">
                        Reason:
                      </span>
                      <p className="text-sm mt-1">{emergency.reason}</p>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <span>Requested: {formatDate(emergency.granted_at)}</span>
                      {emergency.status === "approved" && (
                        <span>Expires: {formatDate(emergency.expires_at)}</span>
                      )}
                      {emergency.status === "rejected" && emergency.reviewed_at && (
                        <span>Rejected: {formatDate(emergency.reviewed_at)}</span>
                      )}
                    </div>
                  </div>

                  {/* Action buttons based on status */}
                  {emergency.status === "pending" && (
                    <div className="mt-4 flex justify-end gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleReject(emergency)}
                        disabled={rejectMutation.isPending}
                      >
                        <XCircle className="h-4 w-4 mr-2" />
                        Reject
                      </Button>
                      <Button
                        variant="default"
                        size="sm"
                        onClick={() => handleApprove(emergency)}
                        disabled={approveMutation.isPending}
                      >
                        <Check className="h-4 w-4 mr-2" />
                        Approve
                      </Button>
                    </div>
                  )}
                  {emergency.status === "approved" && emergency.is_active && (
                    <div className="mt-4 flex justify-end">
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleRevoke(emergency)}
                        disabled={revokeMutation.isPending}
                      >
                        <X className="h-4 w-4 mr-2" />
                        Revoke Access
                      </Button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Approve Confirmation Dialog */}
      <Dialog open={isApproveDialogOpen} onOpenChange={setIsApproveDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Approve Emergency Access</DialogTitle>
            <DialogDescription>
              Are you sure you want to approve this emergency access request?
              The clinician will be granted access to the patient&apos;s records for 30 minutes.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4 space-y-4">
            {selectedEmergency && (
              <div className="rounded-lg border bg-muted p-4">
                <p className="text-sm">
                  <strong>Clinician:</strong> {selectedEmergency.clinician_name || selectedEmergency.clinician_id}
                </p>
                <p className="text-sm">
                  <strong>Patient:</strong> {selectedEmergency.patient_name || selectedEmergency.patient_id}
                </p>
                <p className="text-sm mt-2">
                  <strong>Reason:</strong> {selectedEmergency.reason}
                </p>
              </div>
            )}
            <div>
              <label className="text-sm font-medium">Review Notes (optional)</label>
              <textarea
                className="w-full mt-1 p-2 border rounded-md text-sm"
                rows={3}
                placeholder="Add optional notes about this approval..."
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsApproveDialogOpen(false)}
              disabled={approveMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              variant="default"
              onClick={confirmApprove}
              disabled={approveMutation.isPending}
            >
              {approveMutation.isPending ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Approving...
                </>
              ) : (
                <>
                  <Check className="h-4 w-4 mr-2" />
                  Approve Access
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reject Confirmation Dialog */}
      <Dialog open={isRejectDialogOpen} onOpenChange={setIsRejectDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reject Emergency Access</DialogTitle>
            <DialogDescription>
              Are you sure you want to reject this emergency access request?
              The clinician will not be granted access to the patient&apos;s records.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4 space-y-4">
            {selectedEmergency && (
              <div className="rounded-lg border bg-muted p-4">
                <p className="text-sm">
                  <strong>Clinician:</strong> {selectedEmergency.clinician_name || selectedEmergency.clinician_id}
                </p>
                <p className="text-sm">
                  <strong>Patient:</strong> {selectedEmergency.patient_name || selectedEmergency.patient_id}
                </p>
                <p className="text-sm mt-2">
                  <strong>Reason:</strong> {selectedEmergency.reason}
                </p>
              </div>
            )}
            <div>
              <label className="text-sm font-medium">Review Notes (optional)</label>
              <textarea
                className="w-full mt-1 p-2 border rounded-md text-sm"
                rows={3}
                placeholder="Add optional notes about this rejection..."
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsRejectDialogOpen(false)}
              disabled={rejectMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={confirmReject}
              disabled={rejectMutation.isPending}
            >
              {rejectMutation.isPending ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Rejecting...
                </>
              ) : (
                <>
                  <XCircle className="h-4 w-4 mr-2" />
                  Reject Request
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Revoke Confirmation Dialog */}
      <Dialog open={isRevokeDialogOpen} onOpenChange={setIsRevokeDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Revoke Emergency Access</DialogTitle>
            <DialogDescription>
              Are you sure you want to revoke this emergency access? The clinician
              will immediately lose access to the patient&apos;s records.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            {selectedEmergency && (
              <div className="rounded-lg border bg-muted p-4">
                <p className="text-sm">
                  <strong>Clinician:</strong> {selectedEmergency.clinician_name || selectedEmergency.clinician_id}
                </p>
                <p className="text-sm">
                  <strong>Patient:</strong> {selectedEmergency.patient_name || selectedEmergency.patient_id}
                </p>
                <p className="text-sm mt-2">
                  <strong>Reason:</strong> {selectedEmergency.reason}
                </p>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsRevokeDialogOpen(false)}
              disabled={revokeMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={confirmRevoke}
              disabled={revokeMutation.isPending}
            >
              {revokeMutation.isPending ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Revoking...
                </>
              ) : (
                <>
                  <X className="h-4 w-4 mr-2" />
                  Revoke Access
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
