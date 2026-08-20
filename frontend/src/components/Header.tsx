import { LogOut, Moon, Sun, User } from "lucide-react";
import { useNavigate, Link } from "react-router-dom";
import { useTheme } from "@/contexts/ThemeContext";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";

export function Header() {
  const { theme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <header 
      className="flex h-14 items-center justify-between border-b bg-card px-4 md:px-6"
      role="banner"
    >
      <h1 className="text-sm font-medium text-muted-foreground truncate">
        Zero-Trust Electronic Health Records
      </h1>
      
      {/* Desktop Navigation */}
      <div className="hidden md:flex items-center gap-4">
        {user && (
          <span className="text-sm text-muted-foreground">
            {user.first_name} {user.last_name} · {user.role.name}
          </span>
        )}
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          aria-label={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}
          title={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}
        >
          {theme === "light" ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
        </Button>
        <Button
          variant="ghost"
          size="sm"
          asChild
        >
          <Link to="/profile" className="flex items-center gap-1">
            <User className="h-4 w-4" aria-hidden="true" />
            Profile
          </Link>
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleLogout}
          aria-label="Log out"
        >
          <LogOut className="h-4 w-4 mr-1" aria-hidden="true" />
          Logout
        </Button>
      </div>

      {/* Mobile Menu - Simplified */}
      <div className="flex md:hidden items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          aria-label={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}
        >
          {theme === "light" ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
        </Button>
        <Button
          variant="ghost"
          size="icon"
          asChild
          aria-label="Profile"
        >
          <Link to="/profile">
            <User className="h-4 w-4" />
          </Link>
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleLogout}
          aria-label="Log out"
        >
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </header>
  );
}
