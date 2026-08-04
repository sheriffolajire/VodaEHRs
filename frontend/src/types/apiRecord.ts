/** API response types for medical records from the backend. */

import type { RecordType } from "./clinical";

export interface ApiRecord {
  id: string;
  patient_id: string;
  record_type: RecordType;
  title: string;
  summary: string;
  created_by: string;
  created_at: string;
  version: number;
  integrity_ok: boolean;
  signed_by: string | null;
  signature_algorithm: string | null;
  content: string | null;
  hash: string | null;
  signatures: ApiSignature[];
}

export interface ApiSignature {
  signer_id: string;
  algorithm: string;
  created_at: string;
}