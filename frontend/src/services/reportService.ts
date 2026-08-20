/**
 * Report Service - Phase 6
 * 
 * Provides PDF report generation and download functionality.
 */

import { apiClient } from "@/services/apiClient";

/**
 * Download a patient summary PDF report.
 * 
 * @param patientId - UUID of the patient
 * @returns Promise that resolves when download starts
 */
export async function downloadPatientSummaryReport(patientId: string): Promise<void> {
  const response = await apiClient.get(
    `/reports/patient/${patientId}/summary.pdf`,
    {
      responseType: "blob",
    }
  );
  
  // Create blob URL and trigger download
  const blob = new Blob([response.data], { type: "application/pdf" });
  const url = window.URL.createObjectURL(blob);
  
  // Extract filename from Content-Disposition header or generate default
  const contentDisposition = response.headers["content-disposition"];
  let filename = `patient_summary_${patientId}.pdf`;
  
  if (contentDisposition) {
    const filenameMatch = contentDisposition.match(/filename="(.+)"/);
    if (filenameMatch) {
      filename = filenameMatch[1];
    }
  }
  
  // Create temporary link and click
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  // Clean up
  window.URL.revokeObjectURL(url);
}

/**
 * Download a compliance audit PDF report.
 * 
 * @param options - Report options
 * @returns Promise that resolves when download starts
 */
export async function downloadComplianceReport(
  options: {
    fromDate?: Date;
    toDate?: Date;
    days?: number;
  } = {}
): Promise<void> {
  const params = new URLSearchParams();
  
  if (options.fromDate) {
    params.append("from_date", options.fromDate.toISOString());
  }
  
  if (options.toDate) {
    params.append("to_date", options.toDate.toISOString());
  }
  
  if (options.days) {
    params.append("days", options.days.toString());
  }
  
  const queryString = params.toString();
  const url = `/reports/compliance.pdf${queryString ? `?${queryString}` : ""}`;
  
  const response = await apiClient.get(url, {
    responseType: "blob",
  });
  
  // Create blob URL and trigger download
  const blob = new Blob([response.data], { type: "application/pdf" });
  const blobUrl = window.URL.createObjectURL(blob);
  
  // Extract filename from Content-Disposition header or generate default
  const contentDisposition = response.headers["content-disposition"];
  let filename = `compliance_report.pdf`;
  
  if (contentDisposition) {
    const filenameMatch = contentDisposition.match(/filename="(.+)"/);
    if (filenameMatch) {
      filename = filenameMatch[1];
    }
  }
  
  // Create temporary link and click
  const link = document.createElement("a");
  link.href = blobUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  // Clean up
  window.URL.revokeObjectURL(blobUrl);
}

/**
 * Check report service health.
 * 
 * @returns Health status of the report service
 */
export async function checkReportServiceHealth(): Promise<{
  status: string;
  service: string;
  timestamp: string;
  dependencies?: Record<string, string>;
  error?: string;
}> {
  const { data } = await apiClient.get("/reports/health");
  return data;
}

/**
 * Generate a report download URL (for preview or external use).
 * 
 * @param patientId - UUID of the patient
 * @returns URL string for the report
 */
export function getPatientSummaryReportUrl(patientId: string): string {
  // Get base URL from apiClient defaults or construct it
  const baseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
  return `${baseUrl}/reports/patient/${patientId}/summary.pdf`;
}

/**
 * Generate a compliance report URL.
 * 
 * @param options - Report options
 * @returns URL string for the report
 */
export function getComplianceReportUrl(
  options: {
    fromDate?: Date;
    toDate?: Date;
    days?: number;
  } = {}
): string {
  const baseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
  const params = new URLSearchParams();
  
  if (options.fromDate) {
    params.append("from_date", options.fromDate.toISOString());
  }
  
  if (options.toDate) {
    params.append("to_date", options.toDate.toISOString());
  }
  
  if (options.days) {
    params.append("days", options.days.toString());
  }
  
  const queryString = params.toString();
  return `${baseUrl}/reports/compliance.pdf${queryString ? `?${queryString}` : ""}`;
}
