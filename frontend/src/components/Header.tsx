import { Moon, Sun } from "lucide-react";
import { useTheme } from "@/contexts/ThemeContext";

export function Header() {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="flex h-14 items-center justify-between border-b bg-card px-6">
      <h1 className="text-sm font-medium text-muted-foreground">
        Electronic Health Records
      </h1>
      <button
        type="button"
        onClick={toggleTheme}
        aria-label="Toggle theme"
        className="rounded-md p-2 hover:bg-muted"
      >
        {theme === "light" ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
      </button>
    </header>
  );
}
