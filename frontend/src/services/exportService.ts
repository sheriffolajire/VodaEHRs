/**
 * Export patient records to CSV format
 */
export function exportPatientsToCSV(patients: Array<{
  id: string;
  hospital_number: string;
  first_name: string;
  last_name: string;
  email?: string | null;
  phone?: string | null;
  dob?: string | null;
  gender?: string | null;
}>): void {
  const headers = ["ID", "Hospital Number", "First Name", "Last Name", "Email", "Phone", "Date of Birth", "Gender"];
  
  const rows = patients.map((p) => [
    p.id,
    p.hospital_number,
    p.first_name,
    p.last_name,
    p.email || "",
    p.phone || "",
    p.dob || "",
    p.gender || "",
  ]);

  const csvContent = [headers.join(","), ...rows.map((row) => row.map((cell) => `"${cell}"`).join(","))].join("\n");

  downloadFile(csvContent, "patients.csv", "text/csv");
}

/**
 * Export audit logs to CSV format
 */
export function exportAuditLogsToCSV(logs: Array<{
  id: string;
  action: string;
  user_id?: string;
  patient_id?: string;
  status: string;
  created_at: string;
}>): void {
  const headers = ["ID", "Action", "User ID", "Patient ID", "Status", "Timestamp"];
  
  const rows = logs.map((log) => [
    log.id,
    log.action,
    log.user_id || "",
    log.patient_id || "",
    log.status,
    log.created_at,
  ]);

  const csvContent = [headers.join(","), ...rows.map((row) => row.map((cell) => `"${cell}"`).join(","))].join("\n");

  downloadFile(csvContent, "audit_logs.csv", "text/csv");
}

/**
 * Download file helper
 */
function downloadFile(content: string, filename: string, contentType: string): void {
  const blob = new Blob([content], { type: contentType });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

/**
 * Export data as JSON
 */
export function exportToJSON(data: unknown, filename: string): void {
  const content = JSON.stringify(data, null, 2);
  downloadFile(content, filename, "application/json");
}
