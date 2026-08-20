/**
 * Patient Dashboard Page - Phase 6
 * 
 * Provides personal health overview, records summary, appointments,
 * and consent management for patients.
 */

import { useQuery } from "@tanstack/react-query";
import { 
  FileText, 
  Calendar, 
  Shield, 
  FolderOpen,
  UserRound,
  ChevronRight,
  Download
} from "lucide-react";
import { getPatientStats, type PatientStats } from "@/services/statsService";
import { downloadPatientSummaryReport } from "@/services/reportService";
import { useAuth } from "@/contexts/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from "recharts";

export function PatientDashboardPage() {
  const { user } = useAuth();
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ["patient-stats"],
    queryFn: getPatientStats,
  });

  const handleDownloadSummary = async () => {
    if (!user?.id) return;
    try {
      await downloadPatientSummaryReport(user.id);
    } catch (err) {
      console.error("Failed to download report:", err);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-semibold">My Health Dashboard</h2>
        <p className="text-sm text-muted-foreground">Loading your health information...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-semibold">My Health Dashboard</h2>
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm text-red-600">Failed to load your health information</p>
        </div>
      </div>
    );
  }

  const data = stats as PatientStats;

  // Prepare chart data
  const recordsChartData = data?.record_count_by_type
    ? Object.entries(data.record_count_by_type)
        .filter(([_, count]) => count > 0)
        .map(([type, count]) => ({
          type: type.replace("_", " ").charAt(0).toUpperCase() + type.replace("_", " ").slice(1),
          count,
        }))
    : [];

  const totalRecords = data?.record_count_by_type 
    ? Object.values(data.record_count_by_type).reduce((a, b) => a + b, 0) 
    : 0;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold">My Health Dashboard</h2>
        <p className="text-sm text-muted-foreground">
          Your personal health overview and records
        </p>
      </div>

      {/* Welcome Banner */}
      <div className="rounded-lg bg-gradient-to-r from-primary/10 to-primary/5 border p-6">
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/20">
            <UserRound className="h-6 w-6 text-primary" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold">Welcome to Your Health Portal</h3>
            <p className="text-sm text-muted-foreground mt-1">
              View your medical records, manage appointments, and control who can access your health data.
            </p>
            <div className="flex flex-wrap gap-2 mt-3">
              <Button size="sm" asChild>
                <Link to="/my-records">View My Records</Link>
              </Button>
              <Button size="sm" variant="outline" asChild>
                <Link to="/consent">Manage Consent</Link>
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={<FileText className="h-4 w-4" />}
          title="Medical Records"
          value={totalRecords}
          subtitle="Total records"
          href="/my-records"
        />
        <StatCard
          icon={<Calendar className="h-4 w-4" />}
          title="Upcoming Appointments"
          value={data?.upcoming_appointments || 0}
          subtitle="Scheduled visits"
        />
        <StatCard
          icon={<Shield className="h-4 w-4" />}
          title="Active Consents"
          value={data?.active_consents || 0}
          subtitle="Clinicians with access"
          href="/consent"
        />
        <StatCard
          icon={<FolderOpen className="h-4 w-4" />}
          title="Documents"
          value={data?.document_count || 0}
          subtitle="Uploaded files"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Records by Type Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Records by Type</CardTitle>
          </CardHeader>
          <CardContent>
            {recordsChartData.length > 0 ? (
              <div className="h-[250px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={recordsChartData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" tick={{ fontSize: 12 }} />
                    <YAxis dataKey="type" type="category" width={100} tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#8884d8" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="text-center py-8">
                <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
                <p className="text-sm text-muted-foreground">No records yet</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Quick Links */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Quick Links</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <QuickLink 
                icon={<FileText className="h-4 w-4" />}
                title="View My Records"
                description="Access your medical history"
                href="/my-records"
              />
              <QuickLink 
                icon={<Shield className="h-4 w-4" />}
                title="Manage Consent"
                description="Control who can see your data"
                href="/consent"
              />
              <QuickLink 
                icon={<Calendar className="h-4 w-4" />}
                title="Upcoming Appointments"
                description="View scheduled visits"
                href="/my-records"
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Download Report */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Reports</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            <Button onClick={handleDownloadSummary}>
              <Download className="h-4 w-4 mr-2" />
              Download My Health Summary
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Privacy Notice */}
      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <Shield className="h-5 w-5 text-blue-600 mt-0.5" />
            <div>
              <h4 className="font-medium text-blue-900">Your Privacy is Protected</h4>
              <p className="text-sm text-blue-700 mt-1">
                Your health data is encrypted and only accessible to clinicians you have granted consent to. 
                You can revoke access at any time from the Consent Management page.
              </p>
              <Button variant="link" size="sm" className="text-blue-700 p-0 mt-2" asChild>
                <Link to="/consent">Manage Your Consent →</Link>
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function StatCard({
  icon,
  title,
  value,
  subtitle,
  href,
}: {
  icon: React.ReactNode;
  title: string;
  value: number;
  subtitle: string;
  href?: string;
}) {
  const content = (
    <>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value.toLocaleString()}</div>
        <p className="text-xs text-muted-foreground">{subtitle}</p>
      </CardContent>
    </>
  );

  if (href) {
    return (
      <Link to={href} className="block">
        <Card className="hover:bg-muted/50 transition-colors cursor-pointer">
          {content}
        </Card>
      </Link>
    );
  }

  return <Card>{content}</Card>;
}

function QuickLink({
  icon,
  title,
  description,
  href,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  href: string;
}) {
  return (
    <Link 
      to={href}
      className="flex items-center justify-between rounded-md border p-3 hover:bg-muted/50 transition-colors"
    >
      <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
          {icon}
        </div>
        <div>
          <p className="font-medium text-sm">{title}</p>
          <p className="text-xs text-muted-foreground">{description}</p>
        </div>
      </div>
      <ChevronRight className="h-4 w-4 text-muted-foreground" />
    </Link>
  );
}
