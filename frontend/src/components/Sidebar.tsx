import { LayoutDashboard, Users, UserRound, ShieldCheck, Shield, History, FileText, AlertTriangle } from "lucide-react";
import { NavLink } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import type { RoleName } from "@/types/auth";

interface NavItem {
  to: string;
  label: string;
  icon: typeof LayoutDashboard;
  roles?: RoleName[];
}

const navItems: NavItem[] = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  {
    to: "/patients",
    label: "Patients",
    icon: UserRound,
    roles: ["Admin", "Receptionist", "Doctor", "Nurse"],
  },
  { to: "/users", label: "Users", icon: Users, roles: ["Admin"] },
  // Phase 5: Patient-only routes
  {
    to: "/my-records",
    label: "My Records",
    icon: FileText,
    roles: ["Patient"],
  },
  {
    to: "/consent",
    label: "Consent",
    icon: Shield,
    roles: ["Patient"],
  },
  // Phase 5: Audit Logs (Admin only)
  {
    to: "/audit",
    label: "Audit Logs",
    icon: History,
    roles: ["Admin"],
  },
  // Phase 5: Emergency Access Management (Admin only)
  {
    to: "/emergency-access",
    label: "Emergency Access",
    icon: AlertTriangle,
    roles: ["Admin"],
  },
];

export function Sidebar() {
  const { user } = useAuth();

  const visibleItems = navItems.filter(
    (item) => !item.roles || (user && item.roles.includes(user.role.name)),
  );

  return (
    <aside className="w-60 border-r bg-card p-4">
      <div className="mb-8 flex items-center gap-2 px-2">
        <ShieldCheck className="h-6 w-6 text-primary" />
        <span className="text-lg font-semibold">Voda EHRs</span>
      </div>
      <nav className="space-y-1">
        {visibleItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={label}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-md px-3 py-2 text-sm hover:bg-muted hover:text-foreground ${
                isActive ? "bg-muted text-foreground" : "text-muted-foreground"
              }`
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
