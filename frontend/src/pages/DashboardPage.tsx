import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useQuery } from "@tanstack/react-query";
import { fetchHealth } from "@/services/healthService";

/**
 * DashboardPage - Phase 6
 * 
 * Acts as a router to redirect users to their role-specific dashboard.
 * Falls back to a generic dashboard if role is not recognized.
 */
export function DashboardPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
  });

  // Redirect to role-specific dashboard
  useEffect(() => {
    if (user?.role?.name) {
      switch (user.role.name) {
        case "Admin":
          navigate("/admin/dashboard", { replace: true });
          break;
        case "Doctor":
        case "Nurse":
          navigate("/doctor/dashboard", { replace: true });
          break;
        case "Patient":
          navigate("/patient/dashboard", { replace: true });
          break;
        case "Auditor":
          navigate("/auditor/dashboard", { replace: true });
          break;
        case "Receptionist":
          // Receptionists go directly to Patients page
          navigate("/patients", { replace: true });
          break;
        default:
          // Stay on generic dashboard for unrecognized roles
          break;
      }
    }
  }, [user, navigate]);

  // Show loading while redirecting
  if (user?.role?.name) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-sm text-muted-foreground">Redirecting to {user.role.name} dashboard...</p>
      </div>
    );
  }

  // Generic dashboard for users without a recognized role
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold">Dashboard</h2>
        <p className="text-sm text-muted-foreground">Welcome to Voda EHRs</p>
      </div>

      <div className="rounded-lg border bg-card p-6">
        <h3 className="mb-2 text-sm font-medium">Backend Connectivity</h3>
        {isLoading && <p className="text-sm text-muted-foreground">Checking backend…</p>}
        {isError && <p className="text-sm text-red-500">Backend unreachable: {error.message}</p>}
        {data && (
          <p className="text-sm text-green-600">
            Backend healthy — status: {data.status} ({data.environment})
          </p>
        )}
      </div>
    </div>
  );
}
