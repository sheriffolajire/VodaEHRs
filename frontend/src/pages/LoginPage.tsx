import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useNavigate, Link } from "react-router-dom";
import { z } from "zod";
import {
  ShieldCheck,
  Lock,
  Eye,
  EyeOff,
  AlertCircle,
  ArrowLeft,
  Sun,
  Moon,
  Mail,

} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/contexts/AuthContext";
import { useTheme } from "@/contexts/ThemeContext";
import { showToast } from "@/lib/toast";

const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

type LoginForm = z.infer<typeof loginSchema>;

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [isChecking, setIsChecking] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({ resolver: zodResolver(loginSchema) });

  const onSubmit = async (data: LoginForm) => {
    setSubmitError(null);
    setIsChecking(true);
    try {
      await login(data.email, data.password);
      showToast.success("Login successful", "Welcome back to Voda EHRs!");
      navigate("/dashboard", { replace: true });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Login failed";
      setSubmitError(message);
      showToast.error("Login failed", message);
    } finally {
      setIsChecking(false);
    }
  };


  return (
    <div className="min-h-screen bg-background flex">
      {/* Left side - Visual/Branding */}
      <div className="hidden lg:flex lg:w-1/2 xl:w-[55%] relative overflow-hidden">
        {/* Background decorations */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-primary/5 to-secondary/10" />
        <div className="absolute top-0 right-0 h-[800px] w-[800px] rounded-full bg-gradient-to-br from-primary/20 to-purple-500/10 blur-3xl" />
        <div className="absolute bottom-0 left-0 h-[600px] w-[600px] rounded-full bg-gradient-to-tr from-blue-500/20 to-cyan-500/10 blur-3xl" />
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808008_1px,transparent_1px),linear-gradient(to_bottom,#80808008_1px,transparent_1px)] bg-[size:32px_32px]" />

      </div>

      {/* Right side - Login Form */}
      <div className="flex-1 flex flex-col relative">
        {/* Background */}
        <div className="absolute inset-0 -z-10 overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-muted/30" />
          <div className="absolute right-0 top-0 h-[500px] w-[500px] rounded-full bg-primary/5 blur-3xl" />
          <div className="absolute bottom-0 left-0 h-[400px] w-[400px] rounded-full bg-secondary/20 blur-3xl" />
        </div>

        {/* Header */}
        <header className="w-full">
          <div className="flex h-16 items-center justify-between px-6 lg:px-8">
            {/* Mobile logo */}
            <Link
              to="/"
              className="flex lg:hidden items-center gap-2 transition-opacity hover:opacity-80"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-primary/80">
                <ShieldCheck className="h-5 w-5 text-primary-foreground" />
              </div>
              <span className="text-xl font-bold">Voda EHRs</span>
            </Link>

            <div className="flex items-center gap-2 ml-auto">
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleTheme}
                className="h-10 w-10 rounded-full"
                aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
              >
                {theme === "light" ? (
                  <Moon className="h-5 w-5" />
                ) : (
                  <Sun className="h-5 w-5" />
                )}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate("/")}
                className="gap-2 rounded-full"
              >
                <ArrowLeft className="h-4 w-4" />
                Back to Home
              </Button>
            </div>
          </div>
        </header>

        {/* Main content */}
        <main className="flex-1 flex items-center justify-center p-6 lg:p-8">
          <div className="w-full max-w-md">
            {/* Login Card */}
            <div className="relative overflow-hidden rounded-3xl border bg-card/80 backdrop-blur-xl shadow-2xl shadow-primary/5">
              {/* Security badge */}
              <div className="absolute right-6 top-6">
                <div className="flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-3 py-1.5 text-xs font-medium text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                  <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  Secure
                </div>
              </div>

              <div className="p-8 lg:p-10">
                {/* Logo and title */}
                <div className="mb-8 text-center">
                  <div className="mx-auto mb-5 flex h-20 w-20 items-center justify-center rounded-3xl bg-gradient-to-br from-primary/20 to-primary/5 shadow-xl shadow-primary/10">
                    <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-primary/80 shadow-lg">
                      <ShieldCheck className="h-7 w-7 text-primary-foreground" />
                    </div>
                  </div>
                  <h1 className="text-3xl font-bold tracking-tight mb-2">
                    Welcome Back
                  </h1>
                  <p className="text-muted-foreground">
                    Sign in to access your secure healthcare portal
                  </p>
                </div>

                {/* Login form */}
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
                  <div className="space-y-2.5">
                    <Label htmlFor="email" className="text-sm font-medium flex items-center gap-2">
                      <Mail className="h-3.5 w-3.5 text-muted-foreground" />
                      Email Address
                    </Label>
                    <div className="relative">
                      <Input
                        id="email"
                        type="email"
                        {...register("email")}
                        placeholder="example@mail.org"
                        className="h-12 pl-4 rounded-xl"
                        // autoComplete="email"
                      />
                    </div>
                    {errors.email && (
                      <p className="flex items-center gap-1.5 text-xs text-destructive">
                        <AlertCircle className="h-3.5 w-3.5" />
                        {errors.email.message}
                      </p>
                    )}
                  </div>

                  <div className="space-y-2.5">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="password" className="text-sm font-medium flex items-center gap-2">
                        <Lock className="h-3.5 w-3.5 text-muted-foreground" />
                        Password
                      </Label>
                      <Link
                        to="/forgot-password"
                        className="text-xs text-muted-foreground hover:text-primary transition-colors"
                      >
                        Forgot password?
                      </Link>
                    </div>
                    <div className="relative">
                      <Input
                        id="password"
                        type={showPassword ? "text" : "password"}
                        {...register("password")}
                        placeholder="*********"
                        className="h-12 pl-4 pr-12 rounded-xl"
                        
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors p-1"
                        tabIndex={-1}
                      >
                        {showPassword ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                    {errors.password && (
                      <p className="flex items-center gap-1.5 text-xs text-destructive">
                        <AlertCircle className="h-3.5 w-3.5" />
                        {errors.password.message}
                      </p>
                    )}
                  </div>

                  {/* Error message */}
                  {submitError && (
                    <div className="rounded-xl bg-destructive/10 p-4 text-sm text-destructive border border-destructive/20">
                      <div className="flex items-start gap-3">
                        <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
                        <span>{submitError}</span>
                      </div>
                    </div>
                  )}

                  {/* Submit button */}
                  <Button
                    type="submit"
                    disabled={isSubmitting || isChecking}
                    className="w-full h-12 text-base font-medium rounded-xl shadow-lg shadow-primary/25 hover:shadow-primary/40 transition-all"
                  >
                    {isSubmitting || isChecking ? (
                      <div className="flex items-center gap-2">
                        <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                        Verifying...
                      </div>
                    ) : (
                      <>
                        Sign In
                      </>
                    )}
                  </Button>
                </form>
              </div>
            </div>
          </div>
        </main>

        {/* Footer */}
        <footer className="py-6 px-6">
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 text-xs text-muted-foreground">
            <p>© {new Date().getFullYear()} Voda EHRs</p>
          </div>
        </footer>
      </div>
    </div>
  );
}
