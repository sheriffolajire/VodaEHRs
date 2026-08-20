import React, { useState } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useIdleTimeout } from "@/hooks/useIdleTimeout";
import type { RoleName } from "@/types/auth";

interface ProtectedRouteProps {
  /** When provided, only these roles may access the nested routes. */
  allowedRoles?: RoleName[];
  /** Alternative prop name for role checking. */
  requiredRole?: RoleName;
  /** Children to render if authorized. */
  children?: React.ReactNode;
}

/**
 * Session expiry warning dialog
 */
function SessionExpiryWarning({ 
  remainingSeconds, 
  onStayActive 
}: { 
  remainingSeconds: number; 
  onStayActive: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-sm rounded-lg border bg-card p-6 shadow-lg">
        <h3 className="mb-2 text-lg font-semibold text-amber-600">Session Expiring Soon</h3>
        <p className="mb-4 text-sm text-muted-foreground">
          Your session will expire in <strong>{remainingSeconds}</strong> seconds due to inactivity.
        </p>
        <button
          type="button"
          onClick={onStayActive}
          className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
        >
          Stay Active
        </button>
      </div>
    </div>
  );
}

/**
 * Guards nested routes. Unauthenticated users are sent to login; authenticated
 * users lacking the required role are sent to the dashboard. Server-side RBAC
 * remains the real enforcement; this only shapes the user experience.
 * 
 * Security: Also implements idle session timeout (15 minutes).
 */
export function ProtectedRoute({ allowedRoles, requiredRole, children }: ProtectedRouteProps) {
  const { user, isLoading, isAuthenticated } = useAuth();
  const [showWarning, setShowWarning] = useState(false);
  const [warningSeconds, setWarningSeconds] = useState(60);

  // Enable idle timeout for authenticated users
  const { resetTimer } = useIdleTimeout(
    (seconds) => {
      setWarningSeconds(seconds);
      setShowWarning(true);
    },
    () => {
      // Timeout occurred - will be handled by useIdleTimeout hook
      setShowWarning(false);
    }
  );

  const handleStayActive = () => {
    resetTimer();
    setShowWarning(false);
  };

  if (isLoading) {
    return <div className="p-6 text-sm text-muted-foreground">Loading…</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Check allowedRoles
  if (allowedRoles && user && !allowedRoles.includes(user.role.name)) {
    return <Navigate to="/dashboard" replace />;
  }

  // Check requiredRole
  if (requiredRole && user && user.role.name !== requiredRole) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <>
      {showWarning && (
        <SessionExpiryWarning 
          remainingSeconds={warningSeconds} 
          onStayActive={handleStayActive} 
        />
      )}
      {children ? <>{children}</> : <Outlet />}
    </>
  );
}
