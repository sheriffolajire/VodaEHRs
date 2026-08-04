import { useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { assignClinician, getPatient, listClinicians } from "@/services/patientService";
import {
  createAppointment,
  createRecord,
  downloadDocument,
  listAppointments,
  listDocuments,
  listRecords,
  uploadDocument,
} from "@/services/clinicalService";
import { useAuth } from "@/contexts/AuthContext";
import { RecordIntegrityDisplay } from "@/components/crypto/RecordIntegrityDisplay";
import { CryptoDashboard } from "@/components/crypto/CryptoDashboard";
import type { EncryptedRecord, RecordType } from "@/types/clinical";
import type { ApiRecord } from "@/types/apiRecord";

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
          
          {isRegistrar && <AssignSection patientId={patientId} />}
        </div>
      )}

      {tab === "records" && (
        <RecordsTab patientId={patientId} canCreate={isClinician} role={user?.role.name} />
      )}
      {tab === "documents" && <DocumentsTab patientId={patientId} canUpload={isClinician} />}
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

  const recordsQuery = useDecryptedRecords(patientId);

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
              <p className="mt-2 text-muted-foreground break-words whitespace-pre-wrap">
                {record.content}
              </p>
              <div className="mt-3">
                <RecordIntegrityDisplay 
                  record={record} 
                  decryptedContent={record.content ?? undefined}
                />
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function DocumentsTab({ patientId, canUpload }: { patientId: string; canUpload: boolean }) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  const documentsQuery = useQuery({
    queryKey: ["documents", patientId],
    queryFn: () => listDocuments(patientId),
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadDocument(patientId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents", patientId] });
      setError(null);
    },
    onError: (err) => setError(err instanceof Error ? err.message : "Upload failed"),
  });

  return (
    <div className="space-y-4">
      {canUpload && (
        <div className="rounded-lg border bg-card p-6">
          <h3 className="mb-3 text-sm font-medium">Upload document</h3>
          <input
            type="file"
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) uploadMutation.mutate(file);
            }}
            className="text-sm"
          />
          {error && <p className="mt-2 text-xs text-red-500">{error}</p>}
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
              className="flex items-center justify-between rounded-md border p-3 text-sm"
            >
              <span className="flex items-center gap-2">
                {doc.filename}
                <span className="text-muted-foreground">
                  {(doc.size_bytes / 1024).toFixed(1)} KB
                </span>
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
                {doc.aes_key_hash && (
                  <span className="text-xs text-muted-foreground" title="Integrity hash">
                    Hash: {doc.aes_key_hash.substring(0, 8)}...
                  </span>
                )}
              </span>
              <button
                type="button"
                onClick={() => downloadDocument(doc.id, doc.filename)}
                className="rounded-md border px-2 py-1 text-xs hover:bg-muted"
              >
                Download
              </button>
            </li>
          ))}
        </ul>
      </div>
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
