import React from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/contexts/ThemeContext";
import {
  Shield,
  ShieldCheck,
  Lock,
  Users,
  Activity,
  FileText,
  ChevronRight,
  Stethoscope,
  Building2,
  UserCircle,
  Eye,
  Heart,
  Sun,
  Moon,
  Layers,
} from "lucide-react";

export function LandingPage() {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();

  const features = [
    {
      icon: Shield,
      title: "HIPAA-Compliant Security",
      description:
        "Enterprise-grade encryption and security measures to protect sensitive patient data.",
      color: "from-emerald-500/20 to-emerald-500/5",
      iconBg: "bg-emerald-500/10",
      iconColor: "text-emerald-600 dark:text-emerald-400",
    },
    {
      icon: Users,
      title: "Role-Based Access Control",
      description:
        "Granular permissions ensure users only access data relevant to their role.",
      color: "from-blue-500/20 to-blue-500/5",
      iconBg: "bg-blue-500/10",
      iconColor: "text-blue-600 dark:text-blue-400",
    },
    {
      icon: Heart,
      title: "Patient-Centered Care",
      description:
        "Empower patients with controlled access to their own medical records.",
      color: "from-rose-500/20 to-rose-500/5",
      iconBg: "bg-rose-500/10",
      iconColor: "text-rose-600 dark:text-rose-400",
    },
    {
      icon: Lock,
      title: "Consent Management",
      description:
        "Digital consent workflows ensure patient data is only shared with authorization.",
      color: "from-amber-500/20 to-amber-500/5",
      iconBg: "bg-amber-500/10",
      iconColor: "text-amber-600 dark:text-amber-400",
    },
    {
      icon: Activity,
      title: "Real-Time Monitoring",
      description:
        "Comprehensive audit logs track every access and modification to patient records.",
      color: "from-purple-500/20 to-purple-500/5",
      iconBg: "bg-purple-500/10",
      iconColor: "text-purple-600 dark:text-purple-400",
    },
    {
      icon: FileText,
      title: "Digital Signatures",
      description:
        "Cryptographically secure signatures for medical records and documents.",
      color: "from-cyan-500/20 to-cyan-500/5",
      iconBg: "bg-cyan-500/10",
      iconColor: "text-cyan-600 dark:text-cyan-400",
    },
  ];

  const userRoles = [
    {
      icon: Building2,
      role: "Administrators",
      description: "Manage users, roles, and system-wide settings",
      stats: "Full Control",
    },
    {
      icon: Stethoscope,
      role: "Healthcare Providers",
      description: "Access patient records and manage medical data",
      stats: "Clinical Access",
    },
    {
      icon: UserCircle,
      role: "Patients",
      description: "View your records and manage consent preferences",
      stats: "Self-Service",
    },
    {
      icon: Eye,
      role: "Auditors",
      description: "Monitor system activity and ensure compliance",
      stats: "Read-Only",
    },
  ];



  

  return (
    <div className="min-h-screen bg-background overflow-x-hidden">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 w-full border-b bg-background/80 backdrop-blur-xl supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto flex h-16 items-center justify-between px-4 lg:px-8">
          <div className="flex items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-primary/80 shadow-lg shadow-primary/20">
              <ShieldCheck className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text">Voda EHRs</span>
          </div>
          <div className="flex items-center gap-2">
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
              onClick={() => navigate("/login")}
              className="hidden sm:inline-flex rounded-full"
            >
              Sign In
            </Button>
            <Button 
              onClick={() => navigate("/login")}
              className="rounded-full shadow-lg shadow-primary/25"
            >
              Get Started
            </Button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden px-4 pt-32 pb-20 lg:px-8">
        {/* Animated background */}
        <div className="absolute inset-0 -z-10">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/[0.03] via-background to-secondary/[0.05]" />
          <div className="absolute right-0 top-0 h-[700px] w-[700px] rounded-full bg-gradient-to-br from-primary/10 to-purple-500/5 blur-3xl animate-pulse" />
          <div className="absolute bottom-0 left-0 h-[500px] w-[500px] rounded-full bg-gradient-to-tr from-blue-500/10 to-cyan-500/5 blur-3xl" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[800px] w-[800px] rounded-full bg-gradient-to-r from-emerald-500/5 to-rose-500/5 blur-3xl" />
        </div>

        {/* Grid pattern overlay */}
        <div className="absolute inset-0 -z-10 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]" />

        <div className="container mx-auto max-w-7xl">
          <div className="grid gap-12 lg:grid-cols-2 lg:gap-16 items-center">
            <div className="flex flex-col justify-center space-y-8">
              <div className="space-y-6">
                <h1 className="text-5xl font-bold tracking-tight sm:text-6xl lg:text-7xl leading-[1.1]">
                  Secure
                  <span className="bg-gradient-to-r from-primary via-primary/80 to-primary/60 bg-clip-text text-transparent"> Electronic</span>
                  <br />
                  Health Records
                </h1>
                <p className="text-xl text-muted-foreground max-w-xl leading-relaxed">
                  A modern, secure platform for managing patient health records
                  with role-based access control, consent management, and
                  comprehensive audit trails.
                </p>
              </div>
              <div className="flex flex-col sm:flex-row gap-4">
                <Button
                  size="lg"
                  onClick={() => navigate("/login")}
                  className="group rounded-full h-12 px-8 text-base shadow-xl shadow-primary/25 hover:shadow-primary/40 transition-all"
                >
                  Access Portal
                  <ChevronRight className="ml-2 h-5 w-5 transition-transform group-hover:translate-x-1" />
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  onClick={() => {
                    document
                      .getElementById("features")
                      ?.scrollIntoView({ behavior: "smooth" });
                  }}
                  className="rounded-full h-12 px-8 text-base"
                >
                  Explore Features
                </Button>
              </div>

              
            </div>

            {/* Right side - Encryption Animation */}
            <div className="hidden lg:flex relative lg:pl-8 items-center justify-center">
              <EncryptionAnimation />
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 px-4 lg:px-8 relative">
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,#80808008,transparent_50%)]" />
        <div className="container mx-auto max-w-7xl">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 rounded-full border bg-background/50 backdrop-blur px-4 py-1.5 text-sm font-medium text-muted-foreground mb-6">
              <Layers className="h-4 w-4 text-primary" />
              <span>Core Capabilities</span>
            </div>
            <h2 className="text-4xl font-bold tracking-tight sm:text-5xl mb-6">
              Built for Healthcare Security
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
              Comprehensive features designed to meet the stringent security
              and compliance requirements of modern healthcare organizations.
            </p>
          </div>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature, index) => (
              <div
                key={index}
                className="group relative rounded-2xl border bg-card/50 backdrop-blur-sm p-8 transition-all duration-300 hover:shadow-2xl hover:shadow-primary/5 hover:-translate-y-1 hover:bg-card"
              >
                <div className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${feature.color} opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />
                <div className="relative">
                  <div className={`mb-5 flex h-14 w-14 items-center justify-center rounded-xl ${feature.iconBg} transition-transform duration-300 group-hover:scale-110`}>
                    <feature.icon className={`h-7 w-7 ${feature.iconColor}`} />
                  </div>
                  <h3 className="mb-3 text-lg font-semibold">{feature.title}</h3>
                  <p className="text-muted-foreground leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* User Roles Section */}
      <section className="py-24 px-4 lg:px-8 relative overflow-hidden">
        <div className="absolute inset-0 -z-10 bg-gradient-to-b from-muted/50 via-background to-background" />
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_bottom,#80808008,transparent_50%)]" />
        <div className="container mx-auto max-w-7xl">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 rounded-full border bg-background/50 backdrop-blur px-4 py-1.5 text-sm font-medium text-muted-foreground mb-6">
              <Users className="h-4 w-4 text-primary" />
              <span>Role-Based Access</span>
            </div>
            <h2 className="text-4xl font-bold tracking-tight sm:text-5xl mb-6">
              Designed for Every Role
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
              Tailored experiences for administrators, healthcare providers,
              patients, and auditors with granular permission controls.
            </p>
          </div>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {userRoles.map((role, index) => (
              <div
                key={index}
                className="group relative rounded-2xl border bg-card/50 backdrop-blur-sm p-8 text-center transition-all duration-300 hover:shadow-2xl hover:shadow-primary/5 hover:-translate-y-1 hover:bg-card overflow-hidden"
              >
                <div className="absolute inset-0 bg-gradient-to-br from-primary/[0.03] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                <div className="relative">
                  <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/10 to-primary/5 shadow-lg shadow-primary/10 transition-transform duration-300 group-hover:scale-110">
                    <role.icon className="h-8 w-8 text-primary" />
                  </div>
                  
                  <h3 className="mb-2 text-lg font-semibold">{role.role}</h3>
                  <p className="text-muted-foreground leading-relaxed">
                    {role.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-4 lg:px-8">
        <div className="container mx-auto max-w-5xl">
          <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-primary via-primary/95 to-primary/90 px-8 py-20 text-center text-primary-foreground shadow-2xl shadow-primary/20">
            {/* Background decorations */}
            <div className="absolute inset-0 -z-10">
              <div className="absolute right-0 top-0 h-96 w-96 rounded-full bg-white/10 blur-3xl" />
              <div className="absolute bottom-0 left-0 h-72 w-72 rounded-full bg-white/10 blur-3xl" />
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[500px] w-[500px] rounded-full bg-white/5 blur-3xl" />
            </div>
            {/* Grid pattern */}
            <div className="absolute inset-0 -z-10 bg-[linear-gradient(to_right,#ffffff08_1px,transparent_1px),linear-gradient(to_bottom,#ffffff08_1px,transparent_1px)] bg-[size:32px_32px]" />

            <div className="relative">
              
              <h2 className="text-4xl font-bold tracking-tight sm:text-5xl mb-6">
                Ready to Secure Your
                <br />
                Healthcare Data?
              </h2>
              <p className="text-xl text-primary-foreground/80 mb-10 max-w-2xl mx-auto leading-relaxed">
                Join healthcare organizations trusting Voda EHRs for secure,
                compliant, and efficient patient record management.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button
                  size="lg"
                  variant="secondary"
                  onClick={() => navigate("/login")}
                  className="group rounded-full h-12 px-8 text-base shadow-xl"
                >
                  Access Your Portal
                  <ChevronRight className="ml-2 h-5 w-5 transition-transform group-hover:translate-x-1" />
                </Button>
              </div>

            
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-muted/30 py-16 px-4 lg:px-8">
        <div className="container mx-auto max-w-7xl">
          <div className="border-t pt-8 flex flex-col md:flex-row items-center justify-between gap-4">  
             <div className="flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-emerald-500" />
                 <span className="text-xl font-bold">Voda EHRs</span>   
              </div>  
            <div className="flex items-center gap-6 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <p className="text-sm text-muted-foreground">
              © {new Date().getFullYear()} Voda EHRs. All rights reserved.
            </p>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

// Encryption Animation Component
function EncryptionAnimation() {
  const [step, setStep] = React.useState(0);

  React.useEffect(() => {
    const interval = setInterval(() => {
      setStep((prev) => (prev + 1) % 4);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const steps = [
    { label: "Upload", description: "Secure file transmission" },
    { label: "Process", description: "System validation" },
    { label: "Encrypt", description: "AES-256 encryption" },
    { label: "Secure", description: "Encrypted storage" },
  ];

  return (
    <div className="relative w-full max-w-lg">
      {/* Ambient background effects */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="h-80 w-80 rounded-full bg-gradient-to-br from-primary/10 via-emerald-500/10 to-blue-500/10 blur-3xl animate-pulse" style={{ animationDuration: '4s' }} />
      </div>
      
      {/* Main animation container */}
      <div className="relative p-8">
        {/* Progress steps - Connected */}
        <div className="flex items-center justify-between mb-10 relative">
          {/* Connection line */}
          <div className="absolute left-0 right-0 top-[11px] h-0.5 bg-muted">
            <div 
              className="h-full bg-gradient-to-r from-primary to-emerald-500 transition-all duration-700"
              style={{ width: `${(step / 3) * 100}%` }}
            />
          </div>
          
          {steps.map((s, i) => (
            <div key={i} className="relative flex flex-col items-center z-10">
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center transition-all duration-500 border-2 ${
                  i < step
                    ? "bg-emerald-500 border-emerald-500 shadow-lg shadow-emerald-500/30"
                    : i === step
                    ? "bg-primary border-primary shadow-lg shadow-primary/30 scale-110"
                    : "bg-card border-muted"
                }`}
              >
                {i < step && (
                  <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                  </svg>
                )}
                {i === step && (
                  <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
                )}
              </div>
              <span
                className={`text-[11px] mt-2 font-semibold uppercase tracking-wider transition-colors duration-300 ${
                  i <= step ? "text-foreground" : "text-muted-foreground"
                }`}
              >
                {s.label}
              </span>
            </div>
          ))}
        </div>

        {/* Animation stage */}
        <div className="relative h-56 flex items-center justify-center">
            {/* Animated particles background */}
            <div className="absolute inset-0 overflow-hidden rounded-2xl">
              {[...Array(6)].map((_, i) => (
                <div
                  key={i}
                  className="absolute w-1 h-1 bg-primary/30 rounded-full animate-ping"
                  style={{
                    left: `${15 + i * 15}%`,
                    top: `${20 + (i % 3) * 25}%`,
                    animationDelay: `${i * 0.3}s`,
                    animationDuration: '2s',
                  }}
                />
              ))}
            </div>

            {/* Step 0: File Upload */}
            <div
              className={`absolute transition-all duration-1000 ${
                step === 0
                  ? "opacity-100 translate-x-0"
                  : "opacity-0 pointer-events-none"
              }`}
            >
              <div className="relative">
                {/* File card with glow */}
                <div className="relative">
                  <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 to-blue-600 rounded-xl blur opacity-30" />
                  <div className="relative w-20 h-24 bg-gradient-to-br from-blue-500 to-blue-700 rounded-xl shadow-2xl flex flex-col items-center justify-center border border-white/10">
                    <div className="w-10 h-12 border-2 border-white/30 rounded mb-1 flex items-center justify-center">
                      <span className="text-[10px] text-white/60 font-mono">PDF</span>
                    </div>
                    <div className="w-8 h-1 bg-white/20 rounded" />
                    <div className="w-6 h-1 bg-white/20 rounded mt-1" />
                  </div>
                </div>
                {/* Upload indicator */}
                <div className="absolute -right-3 -top-3">
                  <div className="w-8 h-8 bg-emerald-500 rounded-full flex items-center justify-center shadow-lg shadow-emerald-500/40 animate-bounce">
                    <ChevronRight className="h-4 w-4 text-white -rotate-90" />
                  </div>
                </div>
                {/* Data stream effect */}
                <div className="absolute right-0 top-1/2 translate-x-full">
                  <div className="flex gap-1">
                    {[...Array(4)].map((_, i) => (
                      <div
                        key={i}
                        className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse"
                        style={{ animationDelay: `${i * 0.1}s` }}
                      />
                    ))}
                  </div>
                </div>
              </div>
              <p className="text-xs text-center mt-4 font-medium text-blue-500">
                Medical Record
              </p>
            </div>

            {/* Step 1: Processing */}
            <div
              className={`absolute transition-all duration-1000 ${
                step === 1
                  ? "opacity-100 scale-100"
                  : "opacity-0 scale-75 pointer-events-none"
              }`}
            >
              <div className="relative">
                {/* Central processing hub */}
                <div className="w-28 h-28 relative">
                  {/* Outer rotating ring */}
                  <div className="absolute inset-0 border-2 border-dashed border-primary/30 rounded-full animate-spin" style={{ animationDuration: '8s' }} />
                  {/* Middle ring */}
                  <div className="absolute inset-2 border border-primary/20 rounded-full animate-spin" style={{ animationDuration: '6s', animationDirection: 'reverse' }} />
                  {/* Inner glow */}
                  <div className="absolute inset-4 bg-gradient-to-br from-primary/20 to-primary/5 rounded-full flex items-center justify-center">
                    <Activity className="h-8 w-8 text-primary animate-pulse" />
                  </div>
                  {/* Orbiting dots */}
                  {[0, 1, 2, 3].map((i) => (
                    <div
                      key={i}
                      className="absolute w-2 h-2 bg-primary rounded-full"
                      style={{
                        top: '50%',
                        left: '50%',
                        transform: `rotate(${i * 90}deg) translateX(52px) translateY(-50%)`,
                        transformOrigin: '0 0',
                      }}
                    >
                      <div className="w-full h-full bg-primary rounded-full animate-ping" style={{ animationDelay: `${i * 0.2}s` }} />
                    </div>
                  ))}
                </div>
              </div>
              <p className="text-xs text-center mt-4 font-medium text-primary">
                Validating...
              </p>
            </div>

            {/* Step 2: Encryption */}
            <div
              className={`absolute transition-all duration-1000 ${
                step === 2
                  ? "opacity-100 scale-100"
                  : "opacity-0 scale-75 pointer-events-none"
              }`}
            >
              <div className="relative">
                {/* Encryption core */}
                <div className="w-32 h-32 relative">
                  {/* Energy rings */}
                  <div className="absolute inset-0 border-2 border-amber-500/40 rounded-full animate-ping" style={{ animationDuration: '1.5s' }} />
                  <div className="absolute inset-2 border-2 border-amber-500/30 rounded-full animate-ping" style={{ animationDuration: '1.5s', animationDelay: '0.2s' }} />
                  
                  {/* Rotating cipher rings */}
                  <div className="absolute inset-0 animate-spin" style={{ animationDuration: '4s' }}>
                    <svg className="w-full h-full" viewBox="0 0 100 100">
                      <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="0.5" className="text-amber-500/30" strokeDasharray="4 4" />
                    </svg>
                  </div>
                  <div className="absolute inset-0 animate-spin" style={{ animationDuration: '3s', animationDirection: 'reverse' }}>
                    <svg className="w-full h-full" viewBox="0 0 100 100">
                      <circle cx="50" cy="50" r="38" fill="none" stroke="currentColor" strokeWidth="0.5" className="text-amber-500/20" strokeDasharray="8 4" />
                    </svg>
                  </div>
                  
                  {/* Central lock */}
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="relative">
                      <div className="absolute -inset-2 bg-amber-500/20 rounded-xl blur-lg" />
                      <div className="relative w-16 h-16 bg-gradient-to-br from-amber-400 to-amber-600 rounded-2xl shadow-2xl shadow-amber-500/30 flex items-center justify-center">
                        <Lock className="h-8 w-8 text-white" />
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Binary code effect */}
                <div className="absolute -bottom-8 left-1/2 -translate-x-1/2 whitespace-nowrap">
                  <span className="text-[10px] font-mono text-amber-500/60 tracking-widest">
                    {["1010", "0101", "1100", "0011"][step % 4]}
                  </span>
                </div>
              </div>
              <p className="text-xs text-center mt-6 font-medium text-amber-500">
                Encrypting...
              </p>
            </div>

            {/* Step 3: Secure Storage */}
            <div
              className={`absolute transition-all duration-1000 ${
                step === 3
                  ? "opacity-100 scale-100"
                  : "opacity-0 scale-75 pointer-events-none"
              }`}
            >
              <div className="relative">
                {/* Success shield with glow */}
                <div className="relative">
                  <div className="absolute -inset-4 bg-emerald-500/20 rounded-3xl blur-2xl animate-pulse" />
                  <div className="relative w-24 h-24 bg-gradient-to-br from-emerald-400 via-emerald-500 to-emerald-600 rounded-2xl shadow-2xl shadow-emerald-500/40 flex items-center justify-center border border-white/20">
                    <ShieldCheck className="h-12 w-12 text-white" strokeWidth={2} />
                  </div>
                  {/* Success particles */}
                  {[...Array(8)].map((_, i) => (
                    <div
                      key={i}
                      className="absolute w-1.5 h-1.5 bg-emerald-400 rounded-full"
                      style={{
                        top: '50%',
                        left: '50%',
                        transform: `rotate(${i * 45}deg) translateX(50px)`,
                        transformOrigin: '0 0',
                        animation: 'ping 1s ease-out infinite',
                        animationDelay: `${i * 0.1}s`,
                      }}
                    />
                  ))}
                </div>
                {/* Check badge */}
                <div className="absolute -bottom-2 -right-2 w-8 h-8 bg-white dark:bg-card rounded-full flex items-center justify-center shadow-lg">
                  <div className="w-6 h-6 bg-emerald-500 rounded-full flex items-center justify-center">
                    <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                </div>
              </div>
              <p className="text-xs text-center mt-5 font-semibold text-emerald-500">
                Secured
              </p>
            </div>
          </div>
        </div>

        
    </div>
  );
}
