import { LayoutDashboard, Users, ShieldCheck, FileText } from "lucide-react";
import { NavLink } from "react-router-dom";

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/dashboard", label: "Patients", icon: Users },
  { to: "/dashboard", label: "Records", icon: FileText },
  { to: "/dashboard", label: "Audit", icon: ShieldCheck },
];

export function Sidebar() {
  return (
    <aside className="w-60 border-r bg-card p-4">
      <div className="mb-8 flex items-center gap-2 px-2">
        <ShieldCheck className="h-6 w-6 text-primary" />
        <span className="text-lg font-semibold">Voda EHRs</span>
      </div>
      <nav className="space-y-1">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={label}
            to={to}
            className="flex items-center gap-3 rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
