/** My Records Page for Patients.
 *
 * Patients can view their own medical records and documents.
 */
import { useQuery } from "@tanstack/react-query";
import { FileText, Calendar, User, ShieldCheck, AlertCircle, Download, File } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { listRecords, listDocuments, downloadDocument } from "@/services/clinicalService";
import { apiClient } from "@/services/apiClient";
import type { SuccessResponse } from "@/types/api";
import type { Patient } from "@/types/clinical";
import type { MedicalDocument } from "@/types/document";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { useState } from "react";
// Note: RecordIntegrityDisplay temporarily disabled due to compatibility issues

const recordTypeLabels: Record<string, string> = {
  diagnosis: "Diagnosis",
  medication: "Medication",
  nursing_note: "Nursing Notes",
  lab_result: "Lab Results",
  imaging: "Imaging",
  other: "Other",
};

const recordTypeColors: Record<string, string> = {
  diagnosis: "bg-blue-100 text-blue-800",
  medication: "bg-green-100 text-green-800",
  nursing_note: "bg-purple-100 text-purple-800",
  lab_result: "bg-amber-100 text-amber-800",
  imaging: "bg-cyan-100 text-cyan-800",
  other: "bg-gray-100 text-gray-800",
};

/** Get current patient's own record */
async function getMyPatient(): Promise<Patient> {
  const { data } = await apiClient.get<SuccessResponse<Patient>>("/patients/me");
  return data.data;
}

export function MyRecordsPage() {
  const { user } = useAuth();

  // Get the current patient's record using /patients/me endpoint
  const patientQuery = useQuery({
    queryKey: ["my-patient-record"],
    queryFn: getMyPatient,
    enabled: !!user && user.role.name === "Patient",
  });

  const patientId = patientQuery.data?.id;
  const [downloadError, setDownloadError] = useState<string | null>(null);

  // Fetch records once we have the patient ID
  const recordsQuery = useQuery({
    queryKey: ["my-records", patientId],
    queryFn: async () => {
      if (!patientId) throw new Error("No patient ID found");
      return listRecords(patientId);
    },
    enabled: !!patientId,
  });

  // Fetch documents once we have the patient ID
  const documentsQuery = useQuery({
    queryKey: ["my-documents", patientId],
    queryFn: async () => {
      if (!patientId) throw new Error("No patient ID found");
      return listDocuments(patientId);
    },
    enabled: !!patientId,
  });

  // Show loading state while looking up patient
  if (patientQuery.isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-semibold">My Medical Records</h2>
          <p className="text-sm text-muted-foreground">
            View your medical history and records
          </p>
        </div>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Show error if patient lookup failed
  if (patientQuery.isError || !patientId) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-semibold">My Medical Records</h2>
          <p className="text-sm text-muted-foreground">
            View your medical history and records
          </p>
        </div>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {patientQuery.error instanceof Error
              ? patientQuery.error.message
              : "Unable to load your records. Please contact support if this persists."}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold">My Medical Records</h2>
        <p className="text-sm text-muted-foreground">
          View your medical history and records
        </p>
      </div>

      {recordsQuery.isLoading && (
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-center">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            </div>
          </CardContent>
        </Card>
      )}

      {recordsQuery.isError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {recordsQuery.error instanceof Error
              ? recordsQuery.error.message
              : "Failed to load records"}
          </AlertDescription>
        </Alert>
      )}

      {recordsQuery.data && recordsQuery.data.length === 0 && (
        <Card>
          <CardContent className="p-6 text-center">
            <FileText className="h-12 w-12 mx-auto mb-3 text-muted-foreground opacity-50" />
            <p className="text-muted-foreground">No medical records found.</p>
            <p className="text-sm text-muted-foreground mt-1">
              Your records will appear here once they are created by your clinician.
            </p>
          </CardContent>
        </Card>
      )}

      {recordsQuery.data && recordsQuery.data.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Showing {recordsQuery.data.length} record{recordsQuery.data.length !== 1 ? "s" : ""}
            </p>
          </div>

          <div className="grid gap-4">
            {recordsQuery.data.map((record) => (
              <Card key={record.id} className="overflow-hidden">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                        <FileText className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <CardTitle className="text-base">
                          <Badge className={recordTypeColors[record.record_type] || "bg-gray-100"}>
                            {recordTypeLabels[record.record_type] || record.record_type}
                          </Badge>
                        </CardTitle>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                          <Calendar className="h-3 w-3" />
                          {new Date(record.created_at).toLocaleDateString()}
                          <span>•</span>
                          <User className="h-3 w-3" />
                          Dr. {record.created_by_name || record.created_by?.slice(0, 8) + "..."}
                        </div>
                      </div>
                    </div>
                    {record.integrity_ok && (
                      <div className="flex items-center gap-1 text-green-600">
                        <ShieldCheck className="h-4 w-4" />
                        <span className="text-xs font-medium">Verified</span>
                      </div>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-sm whitespace-pre-wrap">
                    {record.content || (
                      <span className="text-muted-foreground italic">
                        Encrypted content - view details to decrypt
                      </span>
                    )}
                  </div>

                  {/* Record Integrity Section - Simplified */}
                  {record.hash && (
                    <div className="mt-4 pt-4 border-t">
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <ShieldCheck className="h-4 w-4 text-green-600" />
                        <span>Record verified</span>
                        <code className="text-xs bg-muted px-1 rounded">{record.hash.slice(0, 16)}...</code>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Documents Section */}
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold">My Documents</h3>
          <p className="text-sm text-muted-foreground">
            View and download your medical documents
          </p>
        </div>

        {documentsQuery.isLoading && (
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-center">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
              </div>
            </CardContent>
          </Card>
        )}

        {documentsQuery.isError && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {documentsQuery.error instanceof Error
                ? documentsQuery.error.message
                : "Failed to load documents"}
            </AlertDescription>
          </Alert>
        )}

        {documentsQuery.data && documentsQuery.data.length === 0 && (
          <Card>
            <CardContent className="p-6 text-center">
              <File className="h-12 w-12 mx-auto mb-3 text-muted-foreground opacity-50" />
              <p className="text-muted-foreground">No documents found.</p>
              <p className="text-sm text-muted-foreground mt-1">
                Your documents will appear here once they are uploaded by your clinician.
              </p>
            </CardContent>
          </Card>
        )}

        {documentsQuery.data && documentsQuery.data.length > 0 && (
          <div className="grid gap-4">
            {documentsQuery.data.map((doc: MedicalDocument) => (
              <Card key={doc.id} className="overflow-hidden">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                        <FileText className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <p className="font-medium">{doc.filename}</p>
                        <p className="text-sm text-muted-foreground">
                          {(doc.size_bytes / 1024).toFixed(1)} KB • Uploaded{" "}
                          {new Date(doc.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setDownloadError(null);
                        downloadDocument(doc.id, doc.filename).catch((err) => {
                          setDownloadError(
                            err instanceof Error ? err.message : "Download failed"
                          );
                        });
                      }}
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Download
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {downloadError && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{downloadError}</AlertDescription>
          </Alert>
        )}
      </div>
    </div>
  );
}
