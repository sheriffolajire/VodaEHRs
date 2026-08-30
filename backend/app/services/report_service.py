"""

Provides CSV report generation for patient summaries and compliance reports.
"""

import csv
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional
from io import BytesIO, StringIO

from sqlalchemy.orm import Session

from app.repositories import patient_repository
from app.repositories import record_repository
from app.repositories import appointment_repository
from app.repositories import audit_log_repository
from app.repositories import user_repository


@dataclass
class ReportResult:
    """Result of report generation containing buffer and format info."""
    buffer: BytesIO
    content_type: str
    extension: str


def _make_timezone_aware(dt: datetime) -> datetime:
    """Convert a naive datetime to UTC timezone-aware."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class ReportService:
    """Service for generating PDF reports."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_patient_summary_pdf(
        self,
        patient_id: str,
        current_user_id: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> ReportResult:
        """
        Generate a comprehensive patient summary CSV report.
        
        Includes:
        - Patient demographics
        - Medical history summary
        - Recent health records (filtered by date range if provided)
        - Upcoming appointments
        
        Args:
            patient_id: UUID of the patient
            current_user_id: UUID of the user generating the report
            from_date: Optional start date for records filter
            to_date: Optional end date for records filter
            
        Returns:
            ReportResult containing the buffer and content type info
        """
        import uuid
        
        # Fetch patient data
        patient = patient_repository.get_by_id(self.db, uuid.UUID(patient_id))
        if not patient:
            raise ValueError(f"Patient {patient_id} not found")
        
        # Fetch current user to check role
        current_user = user_repository.get_by_id(self.db, uuid.UUID(current_user_id))
        if not current_user:
            raise ValueError(f"User {current_user_id} not found")
        
        # Patients can only download their own summary
        # Check if the patient's email matches the user's email
        # or if the patient's name matches the user's name
        if current_user.role == "Patient":
            patient_belongs_to_user = False
            
            # Check email match
            if patient.email and current_user.email:
                if patient.email.lower() == current_user.email.lower():
                    patient_belongs_to_user = True
            
            # Check name match (fallback)
            if not patient_belongs_to_user and patient.first_name and patient.last_name:
                if (patient.first_name.lower() == current_user.first_name.lower() and
                    patient.last_name.lower() == current_user.last_name.lower()):
                    patient_belongs_to_user = True
            
            if not patient_belongs_to_user:
                raise ValueError("Patients can only download their own health summary")
        
        # Fetch related data with optional date filtering
        all_records = record_repository.list_for_patient(self.db, uuid.UUID(patient_id))
        
        # Filter records by date range if provided
        records = all_records
        if from_date or to_date:
            records = []
            for record in all_records:
                record_date = _make_timezone_aware(record.created_at)
                if from_date and to_date:
                    if from_date <= record_date <= to_date:
                        records.append(record)
                elif from_date:
                    if record_date >= from_date:
                        records.append(record)
                elif to_date:
                    if record_date <= to_date:
                        records.append(record)
        
        appointments = appointment_repository.list_for_patient(self.db, uuid.UUID(patient_id))
        
        # Build CSV content
        csv_buffer = self._build_patient_summary_csv(
            patient=patient,
            records=records,
            appointments=appointments,
            generated_by=current_user_id,
            generated_at=datetime.utcnow(),
            from_date=from_date,
            to_date=to_date
        )
        
        return ReportResult(
            buffer=csv_buffer,
            content_type="text/csv",
            extension="csv"
        )
    
    def generate_compliance_report_pdf(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        current_user_id: Optional[str] = None
    ) -> ReportResult:
        """
        Generate a compliance audit report PDF.
        
        Includes:
        - Audit summary statistics
        - Chain integrity verification
        - Break-glass access events
        - User access patterns
        - Data access violations
        
        Args:
            from_date: Start date for report period (default: 30 days ago)
            to_date: End date for report period (default: now)
            current_user_id: UUID of the user generating the report
            
        Returns:
            ReportResult containing the buffer and content type info
        """
        # Set default date range (timezone-aware UTC)
        if to_date is None:
            to_date = datetime.now(timezone.utc)
        else:
            to_date = _make_timezone_aware(to_date)
        if from_date is None:
            from_date = to_date - timedelta(days=30)
        else:
            from_date = _make_timezone_aware(from_date)
        
        # Fetch audit data - get all events and filter by date
        all_events = audit_log_repository.list_all(self.db, skip=0, limit=10000)
        
        # Debug logging
        import logging
        logging.getLogger(__name__).info(f"ReportService - from_date: {from_date}, to_date: {to_date}")
        logging.getLogger(__name__).info(f"ReportService - Total events in DB: {len(all_events)}")
        if all_events:
            logging.getLogger(__name__).info(f"ReportService - First event date: {all_events[0].created_at}, Last event date: {all_events[-1].created_at}")
        
        events = [e for e in all_events if from_date <= _make_timezone_aware(e.created_at) <= to_date]
        
        logging.getLogger(__name__).info(f"ReportService - Filtered events: {len(events)}")
        chain_ok, _ = audit_log_repository.verify_chain(self.db)
        break_glass_events = [e for e in events if "break_glass" in e.action.lower() or (e.priority and e.priority.value == "high")]
        
        # Calculate statistics
        total_events = len(events)
        events_by_action = {}
        events_by_user = {}
        failed_events = 0
        
        for event in events:
            action = event.action
            events_by_action[action] = events_by_action.get(action, 0) + 1
            
            user_id = str(event.user_id) if event.user_id else "anonymous"
            events_by_user[user_id] = events_by_user.get(user_id, 0) + 1
            
            if event.status == "failure":
                failed_events += 1
        
        # Get user details for top users
        top_users = sorted(events_by_user.items(), key=lambda x: x[1], reverse=True)[:10]
        user_details = []
        for uid, count in top_users:
            if uid != "anonymous":
                user = user_repository.get_by_id(self.db, uuid.UUID(uid))
                if user:
                    user_details.append({
                        "name": f"{user.first_name} {user.last_name}",
                        "email": user.email,
                        "count": count
                    })
                else:
                    user_details.append({
                        "name": "Unknown User",
                        "email": uid,
                        "count": count
                    })
            else:
                user_details.append({
                    "name": "Anonymous",
                    "email": "N/A",
                    "count": count
                })
        
        # Debug logging before CSV generation
        logging.getLogger(__name__).info(f"ReportService - Before CSV: total_events={total_events}, chain_ok={chain_ok}, break_glass={len(break_glass_events)}, failed={failed_events}")
        logging.getLogger(__name__).info(f"ReportService - Before CSV: events_by_action={events_by_action}, user_details={user_details}")
        logging.getLogger(__name__).info(f"ReportService - Before CSV: events count={len(events)}")
        
        # Build CSV content
        csv_buffer = self._build_compliance_report_csv(
            from_date=from_date,
            to_date=to_date,
            total_events=total_events,
            chain_ok=chain_ok,
            break_glass_count=len(break_glass_events),
            events_by_action=events_by_action,
            failed_events=failed_events,
            top_users=user_details,
            events=events,
            generated_by=current_user_id,
            generated_at=datetime.utcnow()
        )
        
        return ReportResult(
            buffer=csv_buffer,
            content_type="text/csv",
            extension="csv"
        )
    
    def _build_patient_summary_html(
        self,
        patient,
        records,
        appointments,
        record_count: int,
        upcoming_appointments: int,
        records_by_type: dict,
        generated_by: str,
        generated_at: datetime
    ) -> str:
        """Build HTML content for patient summary report."""
        
        # Patient info
        patient_name = f"{patient.first_name} {patient.last_name}"
        patient_dob = patient.dob.strftime("%Y-%m-%d") if patient.dob else "N/A"
        patient_age = self._calculate_age(patient.dob) if patient.dob else "N/A"
        
        # Records table rows
        records_rows = ""
        for record in records[:20]:  # Limit to 20 most recent
            record_date = record.created_at.strftime("%Y-%m-%d %H:%M") if record.created_at else "N/A"
            record_type = record.record_type.value if hasattr(record.record_type, 'value') else str(record.record_type)
            records_rows += f"""
                <tr>
                    <td>{record_date}</td>
                    <td>{record_type}</td>
                    <td>{record.created_by or "N/A"}</td>
                </tr>
            """
        
        # Appointments table rows
        appointments_rows = ""
        for appt in appointments[:10]:  # Limit to 10 upcoming
            appt_date = appt.scheduled_at.strftime("%Y-%m-%d %H:%M") if appt.scheduled_at else "N/A"
            appointments_rows += f"""
                <tr>
                    <td>{appt_date}</td>
                    <td>{appt.reason or "N/A"}</td>
                    <td>{appt.status.value if hasattr(appt.status, 'value') else str(appt.status)}</td>
                </tr>
            """
        
        # Records by type summary
        records_by_type_rows = ""
        for rtype, count in sorted(records_by_type.items(), key=lambda x: x[1], reverse=True):
            records_by_type_rows += f"""
                <tr>
                    <td>{rtype}</td>
                    <td>{count}</td>
                </tr>
            """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Patient Summary Report - {patient_name}</title>
            <style>
                @page {{
                    size: A4;
                    margin: 2cm;
                }}
                body {{
                    font-family: Arial, sans-serif;
                    font-size: 11pt;
                    line-height: 1.5;
                    color: #333;
                }}
                h1 {{
                    color: #2563eb;
                    font-size: 24pt;
                    margin-bottom: 0.5cm;
                    border-bottom: 2px solid #2563eb;
                    padding-bottom: 0.3cm;
                }}
                h2 {{
                    color: #374151;
                    font-size: 14pt;
                    margin-top: 1cm;
                    margin-bottom: 0.3cm;
                }}
                .header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    margin-bottom: 1cm;
                }}
                .logo {{
                    font-size: 18pt;
                    font-weight: bold;
                    color: #2563eb;
                }}
                .report-meta {{
                    text-align: right;
                    font-size: 9pt;
                    color: #6b7280;
                }}
                .patient-info {{
                    background: #f3f4f6;
                    padding: 0.5cm;
                    border-radius: 4px;
                    margin-bottom: 1cm;
                }}
                .patient-info table {{
                    width: 100%;
                }}
                .patient-info td {{
                    padding: 0.2cm 0;
                }}
                .patient-info td:first-child {{
                    font-weight: bold;
                    width: 30%;
                }}
                .stats-grid {{
                    display: flex;
                    gap: 0.5cm;
                    margin-bottom: 1cm;
                }}
                .stat-box {{
                    flex: 1;
                    background: #eff6ff;
                    border: 1px solid #bfdbfe;
                    padding: 0.5cm;
                    border-radius: 4px;
                    text-align: center;
                }}
                .stat-value {{
                    font-size: 24pt;
                    font-weight: bold;
                    color: #2563eb;
                }}
                .stat-label {{
                    font-size: 9pt;
                    color: #6b7280;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 0.3cm;
                }}
                th {{
                    background: #f3f4f6;
                    padding: 0.3cm;
                    text-align: left;
                    font-weight: bold;
                    border-bottom: 2px solid #d1d5db;
                }}
                td {{
                    padding: 0.3cm;
                    border-bottom: 1px solid #e5e7eb;
                }}
                tr:nth-child(even) {{
                    background: #f9fafb;
                }}
                .footer {{
                    margin-top: 1cm;
                    padding-top: 0.5cm;
                    border-top: 1px solid #e5e7eb;
                    font-size: 8pt;
                    color: #6b7280;
                    text-align: center;
                }}
                .confidential {{
                    background: #fef3c7;
                    border: 1px solid #f59e0b;
                    padding: 0.3cm;
                    border-radius: 4px;
                    margin-top: 1cm;
                    font-size: 9pt;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="logo">Voda EHRs</div>
                <div class="report-meta">
                    <div>Patient Summary Report</div>
                    <div>Generated: {generated_at.strftime("%Y-%m-%d %H:%M UTC")}</div>
                    <div>Report ID: PS-{generated_at.strftime("%Y%m%d")}-{patient.id[:8]}</div>
                </div>
            </div>
            
            <h1>Patient Summary</h1>
            
            <div class="patient-info">
                <table>
                    <tr>
                        <td>Patient Name:</td>
                        <td>{patient_name}</td>
                    </tr>
                    <tr>
                        <td>Patient ID:</td>
                        <td>{patient.id}</td>
                    </tr>
                    <tr>
                        <td>Date of Birth:</td>
                        <td>{patient_dob} (Age: {patient_age})</td>
                    </tr>
                    <tr>
                        <td>Email:</td>
                        <td>{patient.email or "N/A"}</td>
                    </tr>
                    <tr>
                        <td>Phone:</td>
                        <td>{patient.phone or "N/A"}</td>
                    </tr>
                </table>
            </div>
            
            <div class="stats-grid">
                <div class="stat-box">
                    <div class="stat-value">{record_count}</div>
                    <div class="stat-label">Total Records</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{upcoming_appointments}</div>
                    <div class="stat-label">Upcoming Appointments</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{len(records_by_type)}</div>
                    <div class="stat-label">Record Types</div>
                </div>
            </div>
            
            <h2>Records by Type</h2>
            <table>
                <thead>
                    <tr>
                        <th>Record Type</th>
                        <th>Count</th>
                    </tr>
                </thead>
                <tbody>
                    {records_by_type_rows}
                </tbody>
            </table>
            
            <h2>Recent Health Records</h2>
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Type</th>
                        <th>Created By</th>
                    </tr>
                </thead>
                <tbody>
                    {records_rows}
                </tbody>
            </table>
            
            <h2>Upcoming Appointments</h2>
            <table>
                <thead>
                    <tr>
                        <th>Date & Time</th>
                        <th>Reason</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {appointments_rows if appointments_rows else '<tr><td colspan="3" style="text-align: center;">No upcoming appointments</td></tr>'}
                </tbody>
            </table>
            
            <div class="confidential">
                <strong>CONFIDENTIAL:</strong> This report contains protected health information (PHI) 
                and is intended solely for authorized healthcare providers. Unauthorized disclosure is 
                prohibited under HIPAA regulations.
            </div>
            
            <div class="footer">
                Voda EHRs - Patient Summary Report | Page 1 of 1<br>
                This report was generated by the Voda EHRs system and is digitally signed for integrity.
            </div>
        </body>
        </html>
        """
    
    def _build_compliance_report_html(
        self,
        from_date: datetime,
        to_date: datetime,
        total_events: int,
        chain_ok: bool,
        break_glass_count: int,
        events_by_action: dict,
        failed_events: int,
        top_users: list,
        generated_by: Optional[str],
        generated_at: datetime
    ) -> str:
        """Build HTML content for compliance report."""
        
        # Events by action rows
        events_by_action_rows = ""
        for action, count in sorted(events_by_action.items(), key=lambda x: x[1], reverse=True)[:20]:
            percentage = (count / total_events * 100) if total_events > 0 else 0
            events_by_action_rows += f"""
                <tr>
                    <td>{action}</td>
                    <td>{count}</td>
                    <td>{percentage:.1f}%</td>
                </tr>
            """
        
        # Top users rows
        top_users_rows = ""
        for user in top_users:
            top_users_rows += f"""
                <tr>
                    <td>{user['name']}</td>
                    <td>{user['email']}</td>
                    <td>{user['count']}</td>
                </tr>
            """
        
        chain_status_class = "success" if chain_ok else "error"
        chain_status_text = "VALID" if chain_ok else "COMPROMISED"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Compliance Audit Report</title>
            <style>
                @page {{
                    size: A4;
                    margin: 2cm;
                }}
                body {{
                    font-family: Arial, sans-serif;
                    font-size: 11pt;
                    line-height: 1.5;
                    color: #333;
                }}
                h1 {{
                    color: #2563eb;
                    font-size: 24pt;
                    margin-bottom: 0.5cm;
                    border-bottom: 2px solid #2563eb;
                    padding-bottom: 0.3cm;
                }}
                h2 {{
                    color: #374151;
                    font-size: 14pt;
                    margin-top: 1cm;
                    margin-bottom: 0.3cm;
                }}
                .header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    margin-bottom: 1cm;
                }}
                .logo {{
                    font-size: 18pt;
                    font-weight: bold;
                    color: #2563eb;
                }}
                .report-meta {{
                    text-align: right;
                    font-size: 9pt;
                    color: #6b7280;
                }}
                .report-period {{
                    background: #f3f4f6;
                    padding: 0.5cm;
                    border-radius: 4px;
                    margin-bottom: 1cm;
                    text-align: center;
                }}
                .stats-grid {{
                    display: flex;
                    gap: 0.5cm;
                    margin-bottom: 1cm;
                }}
                .stat-box {{
                    flex: 1;
                    background: #eff6ff;
                    border: 1px solid #bfdbfe;
                    padding: 0.5cm;
                    border-radius: 4px;
                    text-align: center;
                }}
                .stat-box.warning {{
                    background: #fef3c7;
                    border-color: #f59e0b;
                }}
                .stat-box.error {{
                    background: #fee2e2;
                    border-color: #ef4444;
                }}
                .stat-box.success {{
                    background: #d1fae5;
                    border-color: #10b981;
                }}
                .stat-value {{
                    font-size: 24pt;
                    font-weight: bold;
                    color: #2563eb;
                }}
                .stat-box.warning .stat-value {{
                    color: #d97706;
                }}
                .stat-box.error .stat-value {{
                    color: #dc2626;
                }}
                .stat-box.success .stat-value {{
                    color: #059669;
                }}
                .stat-label {{
                    font-size: 9pt;
                    color: #6b7280;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 0.3cm;
                }}
                th {{
                    background: #f3f4f6;
                    padding: 0.3cm;
                    text-align: left;
                    font-weight: bold;
                    border-bottom: 2px solid #d1d5db;
                }}
                td {{
                    padding: 0.3cm;
                    border-bottom: 1px solid #e5e7eb;
                }}
                tr:nth-child(even) {{
                    background: #f9fafb;
                }}
                .chain-status {{
                    padding: 0.5cm;
                    border-radius: 4px;
                    text-align: center;
                    font-weight: bold;
                    margin-bottom: 1cm;
                }}
                .chain-status.success {{
                    background: #d1fae5;
                    color: #065f46;
                    border: 2px solid #10b981;
                }}
                .chain-status.error {{
                    background: #fee2e2;
                    color: #991b1b;
                    border: 2px solid #ef4444;
                }}
                .footer {{
                    margin-top: 1cm;
                    padding-top: 0.5cm;
                    border-top: 1px solid #e5e7eb;
                    font-size: 8pt;
                    color: #6b7280;
                    text-align: center;
                }}
                .certification {{
                    background: #eff6ff;
                    border: 1px solid #bfdbfe;
                    padding: 0.5cm;
                    border-radius: 4px;
                    margin-top: 1cm;
                    font-size: 9pt;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="logo">Voda EHRs</div>
                <div class="report-meta">
                    <div>Compliance Audit Report</div>
                    <div>Generated: {generated_at.strftime("%Y-%m-%d %H:%M UTC")}</div>
                    <div>Report ID: CR-{generated_at.strftime("%Y%m%d")}-{generated_at.strftime("%H%M%S")}</div>
                </div>
            </div>
            
            <h1>Compliance Audit Report</h1>
            
            <div class="report-period">
                <strong>Report Period:</strong> {from_date.strftime("%Y-%m-%d")} to {to_date.strftime("%Y-%m-%d")}
            </div>
            
            <div class="chain-status {chain_status_class}">
                Audit Chain Status: {chain_status_text}
            </div>
            
            <div class="stats-grid">
                <div class="stat-box">
                    <div class="stat-value">{total_events}</div>
                    <div class="stat-label">Total Audit Events</div>
                </div>
                <div class="stat-box {'error' if break_glass_count > 0 else 'success'}">
                    <div class="stat-value">{break_glass_count}</div>
                    <div class="stat-label">Break-Glass Events</div>
                </div>
                <div class="stat-box {'error' if failed_events > 0 else 'success'}">
                    <div class="stat-value">{failed_events}</div>
                    <div class="stat-label">Failed Actions</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{len(events_by_action)}</div>
                    <div class="stat-label">Unique Actions</div>
                </div>
            </div>
            
            <h2>Events by Action Type</h2>
            <table>
                <thead>
                    <tr>
                        <th>Action</th>
                        <th>Count</th>
                        <th>Percentage</th>
                    </tr>
                </thead>
                <tbody>
                    {events_by_action_rows}
                </tbody>
            </table>
            
            <h2>Top Users by Activity</h2>
            <table>
                <thead>
                    <tr>
                        <th>User Name</th>
                        <th>Email</th>
                        <th>Event Count</th>
                    </tr>
                </thead>
                <tbody>
                    {top_users_rows if top_users_rows else '<tr><td colspan="3" style="text-align: center;">No user activity recorded</td></tr>'}
                </tbody>
            </table>
            
            <div class="certification">
                <strong>Audit Certification:</strong> This report certifies that the audit log chain has been 
                verified for integrity. All events recorded in this report are cryptographically signed and 
                tamper-evident. The audit trail meets HIPAA and healthcare compliance requirements for 
                electronic health record systems.
            </div>
            
            <div class="footer">
                Voda EHRs - Compliance Audit Report | Page 1 of 1<br>
                This report was generated by the Voda EHRs system and is digitally signed for integrity.
            </div>
        </body>
        </html>
        """

    def _build_patient_summary_csv(
        self,
        patient,
        records,
        appointments,
        generated_by: str,
        generated_at: datetime,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> BytesIO:
        """Build CSV content for patient summary report."""
        output = StringIO()
        writer = csv.writer(output)
        
        # Patient info section
        writer.writerow(["PATIENT SUMMARY REPORT"])
        writer.writerow(["Generated:", generated_at.strftime("%Y-%m-%d %H:%M UTC")])
        writer.writerow(["Report ID:", f"PS-{generated_at.strftime('%Y%m%d')}-{str(patient.id)[:8]}"])
        
        # Add date range if provided
        if from_date or to_date:
            from_str = from_date.strftime("%Y-%m-%d") if from_date else "All Time"
            to_str = to_date.strftime("%Y-%m-%d") if to_date else "Now"
            writer.writerow(["Records Period:", f"{from_str} to {to_str}"])
        
        writer.writerow([])
        
        # Patient demographics
        writer.writerow(["PATIENT DEMOGRAPHICS"])
        writer.writerow(["Name:", f"{patient.first_name} {patient.last_name}"])
        writer.writerow(["Patient ID:", str(patient.id)])
        writer.writerow(["Date of Birth:", patient.dob.strftime("%Y-%m-%d") if patient.dob else "N/A"])
        writer.writerow(["Email:", patient.email or "N/A"])
        writer.writerow(["Phone:", patient.phone or "N/A"])
        writer.writerow([])
        
        # Records section
        writer.writerow(["MEDICAL RECORDS"])
        writer.writerow(["Date", "Type", "Created By"])
        for record in records[:50]:  # Limit to 50 most recent
            record_date = record.created_at.strftime("%Y-%m-%d %H:%M") if record.created_at else "N/A"
            record_type = record.record_type.value if hasattr(record.record_type, 'value') else str(record.record_type)
            writer.writerow([record_date, record_type, record.created_by or "N/A"])
        writer.writerow([])
        
        # Appointments section
        writer.writerow(["APPOINTMENTS"])
        writer.writerow(["Date", "Reason", "Status"])
        for appt in appointments[:50]:  # Limit to 50
            appt_date = appt.scheduled_at.strftime("%Y-%m-%d %H:%M") if appt.scheduled_at else "N/A"
            status = appt.status.value if hasattr(appt.status, 'value') else str(appt.status)
            writer.writerow([appt_date, appt.reason or "N/A", status])
        writer.writerow([])
        
        # Footer
        writer.writerow(["CONFIDENTIAL - Authorized Use Only"])
        writer.writerow(["Generated by:", generated_by])
        
        # Convert to BytesIO
        output.seek(0)
        buffer = BytesIO(output.getvalue().encode('utf-8'))
        return buffer

    def _build_compliance_report_csv(
        self,
        from_date: datetime,
        to_date: datetime,
        total_events: int,
        chain_ok: bool,
        break_glass_count: int,
        events_by_action: dict,
        failed_events: int,
        top_users: list,
        events: list,
        generated_by: str,
        generated_at: datetime
    ) -> BytesIO:
        """Build CSV content for compliance report."""
        # Debug logging
        import logging
        logging.getLogger(__name__).info(f"CSV Builder - Received: total_events={total_events}, chain_ok={chain_ok}, break_glass={break_glass_count}, failed={failed_events}")
        logging.getLogger(__name__).info(f"CSV Builder - events_by_action count={len(events_by_action)}, top_users count={len(top_users)}, events count={len(events)}")
        
        try:
            output = StringIO()
            writer = csv.writer(output)
            
            # Report header
            writer.writerow(["COMPLIANCE AUDIT REPORT"])
            writer.writerow(["Generated:", generated_at.strftime("%Y-%m-%d %H:%M UTC")])
            writer.writerow(["Report ID:", f"CA-{generated_at.strftime('%Y%m%d')}-{generated_by[:8]}"])
            writer.writerow(["Period:", f"{from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')}"])
            writer.writerow([])
            
            # Summary section
            writer.writerow(["SUMMARY STATISTICS"])
            writer.writerow(["Total Events:", total_events])
            writer.writerow(["Chain Integrity:", "VERIFIED" if chain_ok else "COMPROMISED"])
            writer.writerow(["Break-Glass Events:", break_glass_count])
            writer.writerow(["Failed Events:", failed_events])
            writer.writerow([])
            
            # Events by action
            writer.writerow(["EVENTS BY ACTION"])
            writer.writerow(["Action", "Count"])
            for action, count in sorted(events_by_action.items(), key=lambda x: x[1], reverse=True):
                writer.writerow([action, count])
            writer.writerow([])
            
            # Top users
            writer.writerow(["TOP USERS BY ACTIVITY"])
            writer.writerow(["Name", "Email", "Event Count"])
            for user in top_users:
                writer.writerow([user.get("name", "N/A"), user.get("email", "N/A"), user.get("count", 0)])
            writer.writerow([])
            
            # Detailed events
            writer.writerow(["DETAILED EVENT LOG"])
            writer.writerow(["Timestamp", "Action", "User", "Status", "Priority", "Details"])
            
            # Debug: Log first event to see its structure
            if events:
                first_event = events[0]
                logging.getLogger(__name__).info(f"First event type: {type(first_event)}, priority type: {type(first_event.priority)}, priority value: {first_event.priority}")
            
            for event in events[:100]:  # Limit to 100 events
                try:
                    event_time = event.created_at.strftime("%Y-%m-%d %H:%M:%S") if event.created_at else "N/A"
                    user_id = str(event.user_id) if event.user_id else "anonymous"
                    
                    # Handle priority - could be enum or string
                    priority = "N/A"
                    if event.priority:
                        if hasattr(event.priority, 'value'):
                            priority = event.priority.value
                        else:
                            priority = str(event.priority)
                    
                    # Get reason/details - the model uses 'reason' not 'details'
                    details = event.reason or "N/A" if hasattr(event, 'reason') else "N/A"
                    
                    writer.writerow([
                        event_time,
                        event.action,
                        user_id,
                        event.status,
                        priority,
                        details
                    ])
                except Exception as e:
                    logging.getLogger(__name__).error(f"Error writing event to CSV: {e}")
                    # Write a placeholder row
                    writer.writerow(["ERROR", "ERROR", "ERROR", "ERROR", "ERROR", str(e)])
            writer.writerow([])
            
            # Footer
            writer.writerow(["CONFIDENTIAL - Authorized Use Only"])
            writer.writerow(["Generated by:", generated_by])
            
            # Convert to BytesIO
            output.seek(0)
            buffer = BytesIO(output.getvalue().encode('utf-8'))
            return buffer
            
        except Exception as e:
            logging.getLogger(__name__).error(f"CRITICAL ERROR in CSV generation: {e}")
            # Return error CSV
            error_output = StringIO()
            error_writer = csv.writer(error_output)
            error_writer.writerow(["ERROR GENERATING REPORT"])
            error_writer.writerow([str(e)])
            error_output.seek(0)
            return BytesIO(error_output.getvalue().encode('utf-8'))
