import { Outlet } from "react-router-dom";
import { Header } from "@/components/Header";
import { Sidebar } from "@/components/Sidebar";
import { MobileNav } from "@/components/MobileNav";

export function DashboardLayout() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col">
        <Header />
        {/* Mobile Navigation - Only visible on small screens */}
        <div className="md:hidden border-b bg-card px-4 py-2">
          <MobileNav />
        </div>
        <main 
          className="flex-1 p-4 md:p-6"
          role="main"
          aria-label="Dashboard content"
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
}
