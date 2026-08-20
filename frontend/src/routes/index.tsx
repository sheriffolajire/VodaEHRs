import { createBrowserRouter, Navigate } from "react-router-dom";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { LoginPage } from "@/pages/LoginPage";
import { ForgotPasswordPage } from "@/pages/ForgotPasswordPage";
import { ResetPasswordPage } from "@/pages/ResetPasswordPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { UsersPage } from "@/pages/UsersPage";
import { PatientsPage } from "@/pages/PatientsPage";
import { PatientProfilePage } from "@/pages/PatientProfilePage";
import { HealthPage } from "@/pages/HealthPage";
// Phase 5 imports
import { ConsentPage } from "@/pages/ConsentPage";
import { AuditPage } from "@/pages/AuditPage";
import { MyRecordsPage } from "@/pages/MyRecordsPage";
import { EmergencyAccessAdminPage } from "@/pages/EmergencyAccessAdminPage";
// Phase 6 imports - Role-based dashboards
import { AdminDashboardPage } from "@/pages/AdminDashboardPage";
import { DoctorDashboardPage } from "@/pages/DoctorDashboardPage";
import { PatientDashboardPage } from "@/pages/PatientDashboardPage";
import { AuditorDashboardPage } from "@/pages/AuditorDashboardPage";
import { SystemMonitoringPage } from "@/pages/SystemMonitoringPage";
import { ProfilePage } from "@/pages/ProfilePage";

export const router = createBrowserRouter([
  { path: "/", element: <Navigate to="/dashboard" replace /> },
  { path: "/login", element: <LoginPage /> },
  { path: "/forgot-password", element: <ForgotPasswordPage /> },
  { path: "/reset-password", element: <ResetPasswordPage /> },
  { path: "/health", element: <HealthPage /> },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <DashboardLayout />,
        children: [
          // Phase 6: Role-based dashboards
          { path: "/dashboard", element: <DashboardPage /> },
          { path: "/admin/dashboard", element: <AdminDashboardPage /> },
          { path: "/doctor/dashboard", element: <DoctorDashboardPage /> },
          { path: "/patient/dashboard", element: <PatientDashboardPage /> },
          { path: "/auditor/dashboard", element: <AuditorDashboardPage /> },
          // Phase 6: System Monitoring (Admin only)
          { path: "/system-monitoring", element: <SystemMonitoringPage /> },
          // User Profile (all authenticated users)
          { path: "/profile", element: <ProfilePage /> },
          {
            element: <ProtectedRoute allowedRoles={["Admin", "Receptionist", "Doctor", "Nurse"]} />,
            children: [
              { path: "/patients", element: <PatientsPage /> },
              { path: "/patients/:patientId", element: <PatientProfilePage /> },
            ],
          },
          {
            element: <ProtectedRoute allowedRoles={["Admin"]} />,
            children: [
              { path: "/users", element: <UsersPage /> },
              // Phase 5: Audit Logs (Admin only)
              { path: "/audit", element: <AuditPage /> },
              // Phase 5: Emergency Access Management (Admin only)
              { path: "/emergency-access", element: <EmergencyAccessAdminPage /> },
            ],
          },
          // Phase 5: Patient-only routes
          {
            element: <ProtectedRoute allowedRoles={["Patient"]} />,
            children: [
              { path: "/consent", element: <ConsentPage /> },
              { path: "/my-records", element: <MyRecordsPage /> },
            ],
          },
        ],
      },
    ],
  },
]);
