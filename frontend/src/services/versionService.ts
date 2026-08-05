/** Record version history service for Phase 5.
 *
 * View immutable version history of records.
 */
import { apiClient } from "./apiClient";
import type { SuccessResponse } from "@/types/api";

export interface RecordVersion {
  id: string;
  record_id: string;
  version: number;
  hash: string;
  created_by: string;
  created_at: string;
}

export interface RecordVersionDetail extends RecordVersion {
  encrypted_data_size: number;
  encrypted_aes_key_size: number;
  nonce_size: number;
  auth_tag_size: number;
}

export interface VersionCount {
  count: number;
}

export const versionService = {
  /** List version history for a record. */
  async listVersions(recordId: string): Promise<RecordVersion[]> {
    const { data } = await apiClient.get<SuccessResponse<RecordVersion[]>>(`/records/${recordId}/versions`);
    return data.data;
  },

  /** Get a specific version of a record. */
  async getVersion(recordId: string, version: number): Promise<RecordVersionDetail> {
    const { data } = await apiClient.get<SuccessResponse<RecordVersionDetail>>(`/records/${recordId}/versions/${version}`);
    return data.data;
  },

  /** Get the latest version of a record. */
  async getLatestVersion(recordId: string): Promise<RecordVersion> {
    const { data } = await apiClient.get<SuccessResponse<RecordVersion>>(`/records/${recordId}/versions/latest`);
    return data.data;
  },

  /** Get the number of versions for a record. */
  async getVersionCount(recordId: string): Promise<number> {
    const { data } = await apiClient.get<SuccessResponse<VersionCount>>(`/records/${recordId}/versions/count`);
    return data.data.count;
  },
};
