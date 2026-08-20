import { apiClient } from "@/services/apiClient";
import type { SuccessResponse } from "@/types/api";
import type {
  Appointment,
  EncryptedRecord,
  MedicalDocument,
  RecordType,
} from "@/types/clinical";
import type { ApiRecord } from "@/types/apiRecord";

// NOTE: Decryption of records is performed server‑side. The frontend now receives
// plaintext `content` directly from the API. The previous client‑side envelope
// decryption implementation has been removed to eliminate exposure of the
// institutional private key.

// --- Records ---

export async function listRecords(patientId: string): Promise<ApiRecord[]> {
  const { data } = await apiClient.get<SuccessResponse<ApiRecord[]>>("/records", {
    params: { patient_id: patientId },
  });
  return data.data;
}

/**
 * Admin override to view a record without normal consent.
 * Requires a reason (min 20 characters) which is logged for audit.
 */
export async function adminOverrideViewRecord(recordId: string, reason: string): Promise<ApiRecord> {
  const { data } = await apiClient.post<SuccessResponse<ApiRecord>>(`/records/${recordId}/admin-override`, null, {
    params: { reason },
  });
  return data.data;
}

export async function createRecord(
  patientId: string,
  recordType: RecordType,
  content: string,
): Promise<EncryptedRecord> {
  const { data } = await apiClient.post<SuccessResponse<EncryptedRecord>>("/records", {
    patient_id: patientId,
    record_type: recordType,
    content,
  });
  return data.data;
}

// --- Documents ---

export async function listDocuments(patientId: string): Promise<MedicalDocument[]> {
  const { data } = await apiClient.get<SuccessResponse<MedicalDocument[]>>("/documents", {
    params: { patient_id: patientId },
  });
  return data.data;
}

export async function uploadDocument(
  patientId: string,
  file: File,
): Promise<MedicalDocument> {
  const form = new FormData();
  form.append("patient_id", patientId);
  form.append("file", file);
  const { data } = await apiClient.post<SuccessResponse<MedicalDocument>>("/documents", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data.data;
}

/**
 * Download a document as a blob. apiClient sends the HttpOnly session cookie
 * and retains the standard refresh/session-expiry handling.
 */
export async function downloadDocument(documentId: string, filename: string): Promise<void> {
  try {
    const response = await apiClient.get(`/documents/${documentId}`, {
      responseType: "blob",
    });

    const blob = response.data as Blob;
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error("Error downloading document:", error);
    throw new Error(`Failed to download document: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Admin override download - allows admins to download documents they didn't create.
 * Requires a reason (min 20 characters) which is logged for audit.
 */
export async function adminOverrideDownload(documentId: string, filename: string, reason: string): Promise<void> {
  try {
    const formData = new FormData();
    formData.append("reason", reason);
    const response = await apiClient.post(`/documents/${documentId}/admin-override`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
      responseType: "blob",
    });

    const blob = response.data as Blob;
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error("Error downloading document with admin override:", error);
    throw new Error(`Failed to download document: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

// --- Appointments ---

export async function listAppointments(patientId: string): Promise<Appointment[]> {
  const { data } = await apiClient.get<SuccessResponse<Appointment[]>>("/appointments", {
    params: { patient_id: patientId },
  });
  return data.data;
}

export async function createAppointment(
  patientId: string,
  clinicianId: string,
  scheduledAt: string,
  reason: string,
): Promise<Appointment> {
  const { data } = await apiClient.post<SuccessResponse<Appointment>>("/appointments", {
    patient_id: patientId,
    clinician_id: clinicianId,
    scheduled_at: scheduledAt,
    reason,
  });
  return data.data;
}
