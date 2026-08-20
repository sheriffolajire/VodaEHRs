import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

type Theme = "light" | "dark";

interface ThemeContextValue {
  theme: Theme;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(
    () => (localStorage.getItem("voda-theme") as Theme) ?? "light",
  );

  useEffect(() => {
    const root = document.documentElement;
    const isDark = theme === "dark";
    
    // Toggle dark class
    root.classList.toggle("dark", isDark);
    
    // Also set data-theme attribute for CSS selectors
    root.setAttribute("data-theme", theme);
    
    // Store in localStorage
    localStorage.setItem("voda-theme", theme);
    
    // Force a repaint to ensure styles are applied
    root.style.colorScheme = isDark ? "dark" : "light";
  }, [theme]);

  const toggleTheme = () => setTheme((prev) => (prev === "light" ? "dark" : "light"));

  return <ThemeContext.Provider value={{ theme, toggleTheme }}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}
