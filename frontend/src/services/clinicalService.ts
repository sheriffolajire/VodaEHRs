import { apiClient } from "@/services/apiClient";
import { getAccessToken } from "@/services/tokenStorage";
import type { SuccessResponse } from "@/types/api";
import type {
  Appointment,
  EncryptedRecord,
  MedicalDocument,
  RecordType,
} from "@/types/clinical";
import type { ApiRecord } from "@/types/apiRecord";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

/**
 * Decode base64 string to Uint8Array.
 */
function base64ToUint8Array(base64: string): Uint8Array {
  const binaryString = atob(base64);
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes;
}

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
 * Download a document as a blob. Uses fetch so the Authorization header is sent
 * and the binary body is handled without axios JSON parsing.
 */
export async function downloadDocument(documentId: string, filename: string): Promise<void> {
  try {
    const response = await fetch(`${baseURL}/documents/${documentId}`, {
      headers: { Authorization: `Bearer ${getAccessToken() ?? ""}` },
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Download failed with status ${response.status}:`, errorText);
      throw new Error(`Download failed: ${response.status} ${response.statusText}`);
    }
    
    const blob = await response.blob();
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