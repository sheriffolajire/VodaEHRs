import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import type { RoleName } from "@/types/auth";

interface ProtectedRouteProps {
  /** When provided, only these roles may access the nested routes. */
  allowedRoles?: RoleName[];
}

/**
 * Guards nested routes. Unauthenticated users are sent to login; authenticated
 * users lacking the required role are sent to the dashboard. Server-side RBAC
 * remains the real enforcement; this only shapes the user experience.
 */
export function ProtectedRoute({ allowedRoles }: ProtectedRouteProps) {
  const { user, isLoading, isAuthenticated } = useAuth();

  if (isLoading) {
    return <div className="p-6 text-sm text-muted-foreground">Loading…</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && user && !allowedRoles.includes(user.role.name)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}
