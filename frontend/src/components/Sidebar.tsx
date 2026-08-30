import { LayoutDashboard, Users, UserRound, ShieldCheck, Shield, History, FileText, AlertTriangle, Activity, ClipboardList } from "lucide-react";
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
  // Phase 6: Role-specific dashboards
  { to: "/admin/dashboard", label: "Dashboard", icon: LayoutDashboard, roles: ["Admin"] },
  { to: "/doctor/dashboard", label: "Dashboard", icon: LayoutDashboard, roles: ["Doctor"] },
  { to: "/nurse/dashboard", label: "Dashboard", icon: LayoutDashboard, roles: ["Nurse"] },
  { to: "/patient/dashboard", label: "Dashboard", icon: LayoutDashboard, roles: ["Patient"] },
  { to: "/auditor/dashboard", label: "Dashboard", icon: LayoutDashboard, roles: ["Auditor"] },
  {
    to: "/patients",
    label: "Patients",
    icon: UserRound,
    roles: ["Admin", "Receptionist", "Doctor", "Nurse"],
  },
  // Phase 6: Nursing Tasks (Nurse only)
  {
    to: "/tasks",
    label: "My Tasks",
    icon: ClipboardList,
    roles: ["Nurse"],
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
  // Phase 5: Audit Logs (Admin and Auditor)
  {
    to: "/audit",
    label: "Audit Logs",
    icon: History,
    roles: ["Admin", "Auditor"],
  },
  // Phase 5: Emergency Access Management (Admin and Auditor)
  {
    to: "/emergency-access",
    label: "Emergency Access",
    icon: AlertTriangle,
    roles: ["Admin", "Auditor"],
  },
  // Phase 6: Compliance Reports (Auditor only)
  {
    to: "/compliance-reports",
    label: "Compliance Reports",
    icon: FileText,
    roles: ["Auditor"],
  },
  // Phase 6: System Monitoring (Admin only)
  {
    to: "/system-monitoring",
    label: "System Monitoring",
    icon: Activity,
    roles: ["Admin"],
  },
];

export function Sidebar() {
  const { user } = useAuth();

  const visibleItems = navItems.filter(
    (item) => !item.roles || (user && item.roles.includes(user.role.name)),
  );

  return (
    <aside 
      className="w-60 border-r bg-card p-4 hidden md:block"
      role="navigation"
      aria-label="Main navigation"
    >
      <div className="mb-8 flex items-center gap-2 px-2">
        <ShieldCheck className="h-6 w-6 text-primary" aria-hidden="true" />
        <span className="text-lg font-semibold">Voda EHRs</span>
      </div>
      <nav className="space-y-1" aria-label="Dashboard navigation">
        {visibleItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={`${to}-${label}`}
            to={to}
            className={({ isActive }: { isActive: boolean }) =>
              `flex items-center gap-3 rounded-md px-3 py-2 text-sm hover:bg-muted hover:text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 ${
                isActive ? "bg-muted text-foreground font-medium" : "text-muted-foreground"
              }`
            }
          >
            {({ isActive }: { isActive: boolean }) => (
              <>
                <Icon className="h-4 w-4" aria-hidden="true" />
                <span aria-current={isActive ? "page" : undefined}>{label}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
