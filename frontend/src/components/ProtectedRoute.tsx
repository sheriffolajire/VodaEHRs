import React, { useState } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useIdleTimeout } from "@/hooks/useIdleTimeout";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { AlertTriangle } from "lucide-react";
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
    <Dialog open={true} onOpenChange={() => {}}>
      <DialogContent className="sm:max-w-md" onPointerDownOutside={(e) => e.preventDefault()}>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-amber-600">
            <AlertTriangle className="h-5 w-5" />
            Session Expiring Soon
          </DialogTitle>
          <DialogDescription>
            Your session will expire in <strong>{remainingSeconds}</strong> seconds due to inactivity.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button onClick={onStayActive} className="w-full">
            Stay Active
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
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
