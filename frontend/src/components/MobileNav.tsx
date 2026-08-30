/**
 * Mobile Navigation Component
 * 
 * Provides a responsive navigation menu for mobile devices.
 * Uses the DropdownMenu component for accessibility.
 */

import { Menu, LayoutDashboard, Users, UserRound, Shield, History, FileText, AlertTriangle, Activity } from "lucide-react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { RoleName } from "@/types/auth";

interface NavItem {
  to: string;
  label: string;
  icon: typeof LayoutDashboard;
  roles?: RoleName[];
}

const navItems: NavItem[] = [
  { to: "/admin/dashboard", label: "Admin Dashboard", icon: LayoutDashboard, roles: ["Admin"] },
  { to: "/doctor/dashboard", label: "Doctor Dashboard", icon: LayoutDashboard, roles: ["Doctor"] },
  { to: "/nurse/dashboard", label: "Nurse Dashboard", icon: LayoutDashboard, roles: ["Nurse"] },
  { to: "/patient/dashboard", label: "My Dashboard", icon: LayoutDashboard, roles: ["Patient"] },
  { to: "/auditor/dashboard", label: "Auditor Dashboard", icon: LayoutDashboard, roles: ["Auditor"] },
  { to: "/patients", label: "Patients", icon: UserRound, roles: ["Admin", "Receptionist", "Doctor", "Nurse"] },
  { to: "/users", label: "Users", icon: Users, roles: ["Admin"] },
  { to: "/my-records", label: "My Records", icon: FileText, roles: ["Patient"] },
  { to: "/consent", label: "Consent", icon: Shield, roles: ["Patient"] },
  { to: "/audit", label: "Audit Logs", icon: History, roles: ["Admin"] },
  { to: "/emergency-access", label: "Emergency Access", icon: AlertTriangle, roles: ["Admin"] },
  { to: "/system-monitoring", label: "System Monitoring", icon: Activity, roles: ["Admin"] },
];

export function MobileNav() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const visibleItems = navItems.filter(
    (item) => !item.roles || (user && item.roles.includes(user.role.name)),
  );

  const currentItem = visibleItems.find(item => location.pathname === item.to);
  const currentLabel = currentItem?.label || "Menu";

  return (
    <div className="md:hidden flex items-center gap-2">
      <DropdownMenu>
        <DropdownMenuTrigger
          className="flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-md hover:bg-muted focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
          aria-label="Open navigation menu"
        >
          <Menu className="h-4 w-4" aria-hidden="true" />
          <span>{currentLabel}</span>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-56">
          {visibleItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.to;
            
            return (
              <DropdownMenuItem
                key={`${item.to}-${item.label}`}
                onClick={() => navigate(item.to)}
                className={isActive ? "bg-muted font-medium" : ""}
                aria-current={isActive ? "page" : undefined}
              >
                <Icon className="h-4 w-4 mr-2" aria-hidden="true" />
                {item.label}
              </DropdownMenuItem>
            );
          })}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
