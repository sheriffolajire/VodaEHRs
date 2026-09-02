import { useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { assignClinician, getPatient, listClinicians } from "@/services/patientService";
import {
  adminOverrideDownload,
  adminOverrideViewRecord,
  createAppointment,
  createRecord,
  downloadDocument,
  listAppointments,
  listDocuments,
  listRecords,
  uploadDocument,
} from "@/services/clinicalService";
import { useAuth } from "@/contexts/AuthContext";
import { CryptoDashboard } from "@/components/crypto/CryptoDashboard";
import { EmergencyAccessButton } from "@/components/emergency/EmergencyAccessButton";
import type { RecordType } from "@/types/clinical";

type Tab = "overview" | "records" | "documents" | "appointments";

// Roles allowed to author records / upload documents.
const CLINICAL_ROLES = ["Doctor", "Nurse"];
// Roles allowed to assign clinicians and manage patient contact details.
const REGISTRAR_ROLES = ["Admin", "Receptionist"];
// Roles allowed to schedule appointments.
const SCHEDULER_ROLES = ["Admin", "Receptionist", "Doctor"];

export function PatientProfilePage() {
  const { patientId = "" } = useParams();
  const { user } = useAuth();
  const [tab, setTab] = useState<Tab>("overview");

  const isClinician = user != null && CLINICAL_ROLES.includes(user.role.name);
  const isRegistrar = user != null && REGISTRAR_ROLES.includes(user.role.name);
  const isScheduler = user != null && SCHEDULER_ROLES.includes(user.role.name);
  const isDoctor = user != null && user.role.name === "Doctor";

  const patientQuery = useQuery({
    queryKey: ["patient", patientId],
    queryFn: () => getPatient(patientId),
  });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold">
          {patientQuery.data
            ? `${patientQuery.data.first_name} ${patientQuery.data.last_name}`
            : "Patient"}
        </h2>
        {patientQuery.data && (
          <p className="text-sm text-muted-foreground">
            {patientQuery.data.hospital_number} · DOB {patientQuery.data.dob}
          </p>
        )}
      </div>

      <div className="flex gap-2 border-b">
        {(["overview", "records", "documents", "appointments"] as Tab[]).map((name) => (
          <button
            key={name}
            type="button"
            onClick={() => setTab(name)}
            className={`px-3 py-2 text-sm capitalize ${
              tab === name
                ? "border-b-2 border-primary text-foreground"
                : "text-muted-foreground"
            }`}
          >
            {name}
          </button>
        ))}
      </div>

      {patientQuery.isError && <p className="text-sm text-red-500">Unable to load patient.</p>}

      {tab === "overview" && patientQuery.data && (
        <div className="space-y-6">
          <div className="rounded-lg border bg-card p-6 text-sm">
            <dl className="grid grid-cols-2 gap-3">
              <dt className="text-muted-foreground">Email</dt>
              <dd>{patientQuery.data.email ?? "—"}</dd>
              <dt className="text-muted-foreground">Phone</dt>
              <dd>{patientQuery.data.phone ?? "—"}</dd>
              <dt className="text-muted-foreground">Emergency contact</dt>
              <dd>{patientQuery.data.emergency_contact_name ?? "—"}</dd>
            </dl>
          </div>
          
          <CryptoDashboard patientId={patientId} />
          
          {/* Emergency Access Button for Doctors */}
          {isDoctor && patientQuery.data && (
            <div className="rounded-lg border border-orange-200 bg-orange-50 p-4 dark:border-orange-900 dark:bg-orange-950">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-orange-900 dark:text-orange-100">
                    Emergency Access (Break-Glass)
                  </h3>
                  <p className="text-xs text-orange-700 dark:text-orange-300">
                    Request emergency access to bypass consent requirements for this patient.
                  </p>
                </div>
                <EmergencyAccessButton
                  patientId={patientId}
                  patientName={`${patientQuery.data.first_name} ${patientQuery.data.last_name}`}
                  onSuccess={() => {
                    // Refresh the page to show records after emergency access is granted
                    window.location.reload();
                  }}
                />
              </div>
            </div>
          )}
          
          {isRegistrar && <AssignSection patientId={patientId} />}
        </div>
      )}

      {tab === "records" && (
        <RecordsTab patientId={patientId} canCreate={isClinician} role={user?.role.name} />
      )}
      {tab === "documents" && <DocumentsTab patientId={patientId} canUpload={isClinician} currentUserId={user?.id} currentUserRole={user?.role.name} />}
      {tab === "appointments" && (
        <AppointmentsTab patientId={patientId} canSchedule={isScheduler} />
      )}
    </div>
  );
}

function AssignSection({ patientId }: { patientId: string }) {
  const queryClient = useQueryClient();
  const [clinicianId, setClinicianId] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  const cliniciansQuery = useQuery({ queryKey: ["clinicians"], queryFn: listClinicians });

  const assignMutation = useMutation({
    mutationFn: () => assignClinician(patientId, clinicianId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["patient", patientId] });
      setMessage("Clinician assigned.");
    },
    onError: (error) =>
      setMessage(error instanceof Error ? error.message : "Assignment failed."),
  });

  return (
    <div className="rounded-lg border bg-card p-6">
      <h3 className="mb-3 text-sm font-medium">Assign clinician</h3>
      <div className="flex gap-2">
        <select
          value={clinicianId}
          onChange={(event) => setClinicianId(event.target.value)}
          className="flex-1 rounded-md border bg-background px-3 py-2 text-sm"
        >
          <option value="">Select a clinician…</option>
          {cliniciansQuery.data?.map((clinician) => (
            <option key={clinician.id} value={clinician.id}>
              {clinician.first_name} {clinician.last_name} · {clinician.role.name}
            </option>
          ))}
        </select>
        <button
          type="button"
          disabled={!clinicianId || assignMutation.isPending}
          onClick={() => assignMutation.mutate()}
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-60"
        >
          {assignMutation.isPending ? "Assigning…" : "Assign"}
        </button>
      </div>
      {message && <p className="mt-2 text-xs text-muted-foreground">{message}</p>}
    </div>
  );
}

function useDecryptedRecords(patientId: string) {
  const recordsQuery = useQuery({
    queryKey: ["records", patientId],
    queryFn: async () => {
      const records = await listRecords(patientId);
      return records;
    },
    enabled: !!patientId,
  });

  return recordsQuery;
}

function RecordsTab({
  patientId,
  canCreate,
  role,
}: {
  patientId: string;
  canCreate: boolean;
  role?: string;
}) {
  const queryClient = useQueryClient();
  const [content, setContent] = useState("");
  const [recordType, setRecordType] = useState<RecordType>(
    role === "Nurse" ? "nursing_note" : "diagnosis",
  );
  const [error, setError] = useState<string | null>(null);
  const [overrideRecord, setOverrideRecord] = useState<{id: string, record_type: string} | null>(null);
  const [overrideReason, setOverrideReason] = useState("");
  const [overrideError, setOverrideError] = useState<string | null>(null);
  const [overriddenRecords, setOverriddenRecords] = useState<Set<string>>(new Set());

  const recordsQuery = useDecryptedRecords(patientId);
  const isAdmin = role === "Admin";

  const createMutation = useMutation({
    mutationFn: () => createRecord(patientId, recordType, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["records", patientId] });
      setContent("");
      setError(null);
    },
    onError: (err) => setError(err instanceof Error ? err.message : "Failed"),
  });

  return (
    <div className="space-y-4">
      {canCreate && (
        <div className="rounded-lg border bg-card p-6">
          <h3 className="mb-3 text-sm font-medium">Add record</h3>
          <div className="space-y-3">
            <select
              value={recordType}
              onChange={(event) => setRecordType(event.target.value as RecordType)}
              disabled={role === "Nurse"}
              className="w-full rounded-md border bg-background px-3 py-2 text-sm"
            >
              <option value="diagnosis">Diagnosis</option>
              <option value="medication">Medication</option>
              <option value="nursing_note">Nursing note</option>
              <option value="lab_result">Lab result</option>
              <option value="imaging">Imaging</option>
              <option value="other">Other</option>
            </select>
            <textarea
              value={content}
              onChange={(event) => setContent(event.target.value)}
              placeholder="Clinical note"
              className="w-full rounded-md border bg-background px-3 py-2 text-sm"
              rows={3}
            />
            <button
              type="button"
              disabled={!content || createMutation.isPending}
              onClick={() => createMutation.mutate()}
              className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-60"
            >
              {createMutation.isPending ? "Saving…" : "Save record"}
            </button>
            {error && <p className="text-xs text-red-500">{error}</p>}
          </div>
        </div>
      )}

      <div className="rounded-lg border bg-card p-6">
        <h3 className="mb-3 text-sm font-medium">Records</h3>
        {recordsQuery.isLoading && <p className="text-sm text-muted-foreground">Loading…</p>}
        {recordsQuery.data && recordsQuery.data.length === 0 && (
          <p className="text-sm text-muted-foreground">No records yet.</p>
        )}
        <ul className="space-y-2">
          {recordsQuery.data?.map((record) => (
            <li key={record.id} className="rounded-md border p-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="font-medium capitalize">{record.record_type.replace("_", " ")}</span>
                <span className="text-muted-foreground text-xs">
                  {new Date(record.created_at).toLocaleString()}
                </span>
              </div>
              <div className="mt-1 text-xs text-muted-foreground">
                By: {record.created_by_name || `Dr. ${record.created_by.slice(0, 8)}...`}
              </div>
              
              {/* Show content if available, otherwise show access denied message */}
              {record.access_denied && !overriddenRecords.has(record.id) ? (
                <div className="mt-2 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                  <div className="flex items-center gap-2 text-yellow-800">
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                    <span className="font-medium text-sm">Access Restricted</span>
                  </div>
                  <p className="text-xs text-yellow-700 mt-1">
                    {record.access_denied_reason || "Patient consent required to view this record"}
                  </p>
                  {isAdmin && (
                    <button
                      type="button"
                      onClick={() => {
                        setOverrideRecord({id: record.id, record_type: record.record_type});
                        setOverrideReason("");
                        setOverrideError(null);
                      }}
                      className="mt-2 rounded-md border border-amber-500 bg-amber-50 px-2 py-1 text-xs text-amber-700 hover:bg-amber-100 dark:bg-amber-900 dark:text-amber-100"
                    >
                      Admin Override
                    </button>
                  )}
                </div>
              ) : (
                <p className="mt-2 text-muted-foreground break-words whitespace-pre-wrap">
                  {record.content}
                </p>
              )}
              
              {record.hash && !record.access_denied && (
                <div className="mt-2 text-xs text-muted-foreground">
                  Hash: <code className="bg-muted px-1 rounded">{record.hash.slice(0, 16)}...</code>
                </div>
              )}
              
              {/* Signature information */}
              {!record.access_denied && record.signatures && record.signatures.length > 0 && (
                <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded-md">
                  <div className="flex items-center gap-2 text-green-800">
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span className="font-medium text-xs">
                      {record.signatures.length} Signature{record.signatures.length > 1 ? 's' : ''} Verified
                    </span>
                  </div>
                  <div className="text-xs text-green-700 mt-1">
                    Signed by: {record.signatures.map(s => s.signer_id.slice(0, 8)).join(', ')}...
                  </div>
                  
                </div>
              )}
              
              {!record.access_denied && (!record.signatures || record.signatures.length === 0) && (
                <div className="mt-2 text-xs text-muted-foreground">
                  <span className="text-yellow-600">⚠ Not signed</span>
                </div>
              )}
              
              {/* Show signature count even when access is denied */}
              {record.access_denied && (record.signature_count || 0) > 0 && (
                <div className="mt-2 text-xs text-muted-foreground">
                  <span className="text-green-600">
                    ✓ {record.signature_count} Signature{record.signature_count !== 1 ? 's' : ''} (verified)
                  </span>
                </div>
              )}
            </li>
          ))}
        </ul>
      </div>
      
      {/* Admin Override Dialog for Records */}
      {overrideRecord && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-md rounded-lg border bg-card p-6 shadow-lg">
            <h3 className="mb-4 text-lg font-semibold text-amber-600">Admin Override - View Record</h3>
            <p className="mb-4 text-sm text-muted-foreground">
              You are about to view a <strong>{overrideRecord.record_type.replace("_", " ")}</strong> record using admin override.
              This action will be logged for audit purposes.
            </p>
            <div className="mb-4">
              <label className="mb-2 block text-sm font-medium">
                Reason for override (required, min 20 characters):
              </label>
              <textarea
                value={overrideReason}
                onChange={(e) => setOverrideReason(e.target.value)}
                className="w-full rounded-md border p-2 text-sm"
                rows={3}
                placeholder="e.g., Legal compliance audit - required by court order"
              />
            </div>
            {overrideError && (
              <p className="mb-4 text-xs text-red-500">{overrideError}</p>
            )}
            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setOverrideRecord(null)}
                className="rounded-md border px-4 py-2 text-sm hover:bg-muted"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={overrideReason.length < 20}
                onClick={() => {
                  setOverrideError(null);
                  adminOverrideViewRecord(overrideRecord.id, overrideReason)
                    .then((recordData) => {
                      // Add to overridden records set to show content
                      setOverriddenRecords(prev => new Set(prev).add(overrideRecord.id));
                      // Update the record in the cache
                      queryClient.setQueryData(["records", patientId], (oldData: any) => {
                        if (!oldData) return oldData;
                        return oldData.map((r: any) => 
                          r.id === overrideRecord.id 
                            ? { ...r, ...recordData, access_denied: false }
                            : r
                        );
                      });
                      setOverrideRecord(null);
                    })
                    .catch((err) => {
                      setOverrideError(err instanceof Error ? err.message : "Failed to view record");
                    });
                }}
                className="rounded-md bg-amber-600 px-4 py-2 text-sm text-white hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                View with Override
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

import type { UploadPurpose, UploadedForType } from "@/services/clinicalService";

const PURPOSE_OPTIONS: { value: UploadPurpose; label: string }[] = [
  { value: "general", label: "General" },
  { value: "lab_results", label: "Lab Results" },
  { value: "prescriptions", label: "Prescriptions" },
  { value: "imaging", label: "Imaging" },
  { value: "consent_forms", label: "Consent Forms" },
];

const UPLOADED_FOR_TYPE_OPTIONS: { value: UploadedForType; label: string }[] = [
  { value: "patient", label: "Patient" },
  { value: "department", label: "Department" },
  { value: "external_provider", label: "External Provider" },
  { value: "internal_reference", label: "Internal Reference" },
];

function DocumentsTab({ 
  patientId, 
  canUpload, 
  currentUserId,
  currentUserRole 
}: { 
  patientId: string; 
  canUpload: boolean;
  currentUserId?: string;
  currentUserRole?: string;
}) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [overrideDoc, setOverrideDoc] = useState<{id: string, filename: string} | null>(null);
  const [overrideReason, setOverrideReason] = useState("");
  const [overrideError, setOverrideError] = useState<string | null>(null);
  
  // Upload form state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadPurpose, setUploadPurpose] = useState<UploadPurpose>("general");
  const [uploadedFor, setUploadedFor] = useState("");
  const [uploadedForType, setUploadedForType] = useState<UploadedForType | undefined>(undefined);

  const documentsQuery = useQuery({
    queryKey: ["documents", patientId],
    queryFn: () => listDocuments(patientId),
  });
  
  // Check if user can download a specific document
  const canDownload = (docUploadedBy: string, requiresConsent?: boolean): boolean => {
    const isUploader = currentUserId === docUploadedBy;
    const isPatient = currentUserRole === "Patient";
    // Admin can always download
    const isAdmin = currentUserRole === "Admin";
    if (isAdmin) return true;
    // Patient can always download their own documents
    if (isPatient) return true;
    // Uploader can always download their own documents
    if (isUploader) return true;
    // If consent is NOT required (they have consent), they can download
    if (!requiresConsent) return true;
    // Otherwise, they need consent
    return false;
  };
  
  const isAdmin = currentUserRole === "Admin";

  const uploadMutation = useMutation({
    mutationFn: () => {
      if (!selectedFile) throw new Error("No file selected");
      return uploadDocument(
        patientId, 
        selectedFile, 
        uploadPurpose, 
        uploadedFor || undefined, 
        uploadedForType
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents", patientId] });
      setError(null);
      setSelectedFile(null);
      setUploadPurpose("general");
      setUploadedFor("");
      setUploadedForType(undefined);
    },
    onError: (err) => setError(err instanceof Error ? err.message : "Upload failed"),
  });

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) setSelectedFile(file);
  };

  const handleUpload = () => {
    if (!selectedFile) {
      setError("Please select a file");
      return;
    }
    uploadMutation.mutate();
  };

  // Format purpose for display
  const formatPurpose = (purpose?: string): string => {
    if (!purpose) return "General";
    return purpose.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
  };

  return (
    <div className="space-y-4">
      {canUpload && (
        <div className="rounded-lg border bg-card p-6">
          <h3 className="mb-4 text-sm font-medium">Upload Document</h3>
          <div className="space-y-4">
            {/* File Selection */}
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">
                File
              </label>
              <input
                type="file"
                onChange={handleFileChange}
                className="text-sm w-full"
              />
              {selectedFile && (
                <p className="mt-1 text-xs text-muted-foreground">
                  Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
                </p>
              )}
            </div>

            {/* Purpose Selection */}
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">
                Purpose
              </label>
              <select
                value={uploadPurpose}
                onChange={(e) => setUploadPurpose(e.target.value as UploadPurpose)}
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
              >
                {PURPOSE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Uploaded For */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">
                  Uploaded For (Optional)
                </label>
                <input
                  type="text"
                  value={uploadedFor}
                  onChange={(e) => setUploadedFor(e.target.value)}
                  placeholder="e.g., Dr. Smith, Cardiology Dept"
                  className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                  maxLength={255}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">
                  Type (Optional)
                </label>
                <select
                  value={uploadedForType || ""}
                  onChange={(e) => setUploadedForType(e.target.value as UploadedForType || undefined)}
                  className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                >
                  <option value="">-- Select --</option>
                  {UPLOADED_FOR_TYPE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Upload Button */}
            <button
              type="button"
              onClick={handleUpload}
              disabled={uploadMutation.isPending || !selectedFile}
              className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {uploadMutation.isPending ? "Uploading..." : "Upload Document"}
            </button>
            
            {error && <p className="text-xs text-red-500">{error}</p>}
          </div>
        </div>
      )}

      <div className="rounded-lg border bg-card p-6">
        <h3 className="mb-3 text-sm font-medium">Documents</h3>
        {documentsQuery.data && documentsQuery.data.length === 0 && (
          <p className="text-sm text-muted-foreground">No documents.</p>
        )}
        <ul className="space-y-2">
          {documentsQuery.data?.map((doc) => (
            <li
              key={doc.id}
              className="flex flex-col rounded-md border p-3 text-sm"
            >
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 flex-wrap">
                  <span className="font-medium">{doc.filename}</span>
                  <span className="text-muted-foreground">
                    {(doc.size_bytes / 1024).toFixed(1)} KB
                  </span>
                  {/* Purpose Badge */}
                  {doc.upload_purpose && doc.upload_purpose !== "general" && (
                    <span className="inline-flex items-center rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800 dark:bg-blue-900 dark:text-blue-100">
                      {formatPurpose(doc.upload_purpose)}
                    </span>
                  )}
                  {doc.encrypted ? (
                    <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800 dark:bg-green-900 dark:text-green-100">
                      <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                      </svg>
                      Encrypted
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 rounded-full bg-yellow-100 px-2 py-0.5 text-xs font-medium text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100">
                      <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                      Unencrypted
                    </span>
                  )}
                  {/* Consent Required Badge */}
                  {doc.requires_consent && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800 dark:bg-amber-900 dark:text-amber-100">
                      <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                      </svg>
                      Consent Required
                    </span>
                  )}
                </span>
                <div className="flex items-center gap-2">
                  {canDownload(doc.uploaded_by, doc.requires_consent) ? (
                    <button
                      type="button"
                      onClick={() => {
                        setDownloadError(null);
                        downloadDocument(doc.id, doc.filename).catch((err) => {
                          setDownloadError(err instanceof Error ? err.message : "Download failed");
                        });
                      }}
                      className="rounded-md border px-2 py-1 text-xs hover:bg-muted"
                    >
                      Download
                    </button>
                  ) : isAdmin ? (
                    <button
                      type="button"
                      onClick={() => {
                        setOverrideDoc({id: doc.id, filename: doc.filename});
                        setOverrideReason("");
                        setOverrideError(null);
                      }}
                      className="rounded-md border border-amber-500 bg-amber-50 px-2 py-1 text-xs text-amber-700 hover:bg-amber-100 dark:bg-amber-900 dark:text-amber-100"
                      title="Admin override - requires reason"
                    >
                      Override
                    </button>
                  ) : doc.requires_consent ? (
                    <span className="text-xs text-amber-600 italic" title="Patient consent required to download this document">
                      Consent required
                    </span>
                  ) : (
                    <span className="text-xs text-muted-foreground italic" title="Only the document creator can download">
                      View only
                    </span>
                  )}
                </div>
              </div>
              
              {/* Document Metadata Row */}
              {(doc.uploaded_for || doc.upload_purpose) && (
                <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
                  {doc.upload_purpose && doc.upload_purpose !== "general" && (
                    <span className="inline-flex items-center rounded bg-slate-100 px-1.5 py-0.5 dark:bg-slate-800">
                      Purpose: {formatPurpose(doc.upload_purpose)}
                    </span>
                  )}
                  {doc.uploaded_for && (
                    <span className="inline-flex items-center rounded bg-slate-100 px-1.5 py-0.5 dark:bg-slate-800">
                      For: {doc.uploaded_for}
                      {doc.uploaded_for_type && (
                        <span className="ml-1 text-slate-500">({doc.uploaded_for_type.replace(/_/g, " ")})</span>
                      )}
                    </span>
                  )}
                </div>
              )}
            </li>
          ))}
        </ul>
        {downloadError && (
          <p className="mt-3 text-xs text-red-500">{downloadError}</p>
        )}
      </div>
      
      {/* Admin Override Dialog */}
      {overrideDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-md rounded-lg border bg-card p-6 shadow-lg">
            <h3 className="mb-4 text-lg font-semibold text-amber-600">Admin Override Download</h3>
            <p className="mb-4 text-sm text-muted-foreground">
              You are about to download <strong>{overrideDoc.filename}</strong> using admin override.
              This action will be logged for audit purposes.
            </p>
            <div className="mb-4">
              <label className="mb-2 block text-sm font-medium">
                Reason for override (required, min 20 characters):
              </label>
              <textarea
                value={overrideReason}
                onChange={(e) => setOverrideReason(e.target.value)}
                className="w-full rounded-md border p-2 text-sm"
                rows={3}
                placeholder="e.g., Legal compliance audit - required by court order"
              />
            </div>
            {overrideError && (
              <p className="mb-4 text-xs text-red-500">{overrideError}</p>
            )}
            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setOverrideDoc(null)}
                className="rounded-md border px-4 py-2 text-sm hover:bg-muted"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={overrideReason.length < 20}
                onClick={() => {
                  setOverrideError(null);
                  adminOverrideDownload(overrideDoc.id, overrideDoc.filename, overrideReason)
                    .then(() => {
                      setOverrideDoc(null);
                    })
                    .catch((err) => {
                      setOverrideError(err instanceof Error ? err.message : "Download failed");
                    });
                }}
                className="rounded-md bg-amber-600 px-4 py-2 text-sm text-white hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Download with Override
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function AppointmentsTab({
  patientId,
  canSchedule,
}: {
  patientId: string;
  canSchedule: boolean;
}) {
  const queryClient = useQueryClient();
  const [clinicianId, setClinicianId] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);

  const appointmentsQuery = useQuery({
    queryKey: ["appointments", patientId],
    queryFn: () => listAppointments(patientId),
  });

  const cliniciansQuery = useQuery({
    queryKey: ["clinicians"],
    queryFn: listClinicians,
    enabled: canSchedule,
  });

  const scheduleMutation = useMutation({
    // The datetime-local value is local time; convert to ISO for the API.
    mutationFn: () =>
      createAppointment(patientId, clinicianId, new Date(scheduledAt).toISOString(), reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["appointments", patientId] });
      setScheduledAt("");
      setReason("");
      setError(null);
    },
    onError: (err) => setError(err instanceof Error ? err.message : "Scheduling failed."),
  });

  return (
    <div className="space-y-4">
      {canSchedule && (
        <div className="rounded-lg border bg-card p-6">
          <h3 className="mb-3 text-sm font-medium">Schedule appointment</h3>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <select
              value={clinicianId}
              onChange={(event) => setClinicianId(event.target.value)}
              className="rounded-md border bg-background px-3 py-2 text-sm"
            >
              <option value="">Select a clinician…</option>
              {cliniciansQuery.data?.map((clinician) => (
                <option key={clinician.id} value={clinician.id}>
                  {clinician.first_name} {clinician.last_name} · {clinician.role.name}
                </option>
              ))}
            </select>
            <input
              type="datetime-local"
              value={scheduledAt}
              onChange={(event) => setScheduledAt(event.target.value)}
              className="rounded-md border bg-background px-3 py-2 text-sm"
            />
            <input
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              placeholder="Reason"
              className="rounded-md border bg-background px-3 py-2 text-sm sm:col-span-2"
            />
            <button
              type="button"
              disabled={!clinicianId || !scheduledAt || scheduleMutation.isPending}
              onClick={() => scheduleMutation.mutate()}
              className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-60 sm:col-span-2"
            >
              {scheduleMutation.isPending ? "Scheduling…" : "Schedule"}
            </button>
          </div>
          {error && <p className="mt-2 text-xs text-red-500">{error}</p>}
        </div>
      )}

      <div className="rounded-lg border bg-card p-6">
        <h3 className="mb-3 text-sm font-medium">Appointments</h3>
        {appointmentsQuery.data && appointmentsQuery.data.length === 0 && (
          <p className="text-sm text-muted-foreground">No appointments.</p>
        )}
        <ul className="space-y-2">
          {appointmentsQuery.data?.map((appointment) => (
            <li key={appointment.id} className="rounded-md border p-3 text-sm">
              <span className="font-medium">
                {new Date(appointment.scheduled_at).toLocaleString()}
              </span>
              <span className="ml-2 capitalize text-muted-foreground">{appointment.status}</span>
              {appointment.reason && <p className="mt-1">{appointment.reason}</p>}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
