/**
 * Admin Dashboard Page - Phase 6
 * 
 * Provides system overview, user management stats, patient overview,
 * and recent audit events for administrators.
 */

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { 
  Users, 
  UserRound, 
  FileText, 
  Calendar, 
  Shield, 
  Activity,
  AlertTriangle,
  CheckCircle,
  Download,
  RefreshCw
} from "lucide-react";
import { getAdminStats, type AdminStats } from "@/services/statsService";
import { downloadComplianceReport } from "@/services/reportService";
import { DashboardSkeleton } from "@/components/DashboardSkeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { toast } from "sonner";
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from "recharts";

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884D8", "#82CA9D"];

export function AdminDashboardPage() {
  const { data: stats, isLoading, error, refetch } = useQuery({
    queryKey: ["admin-stats"],
    queryFn: getAdminStats,
  });

  // Date range state for compliance report
  const today = new Date().toISOString().split('T')[0];
  const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
  
  const [fromDate, setFromDate] = useState(thirtyDaysAgo);
  const [toDate, setToDate] = useState(today);

  const handleDownloadComplianceReport = async () => {
    try {
      const from = new Date(fromDate);
      const to = new Date(toDate);
      
      if (from > to) {
        toast.error("From date must be before To date");
        return;
      }
      
      await downloadComplianceReport({ 
        fromDate: from,
        toDate: to
      });
      toast.success("Compliance report downloaded successfully");
    } catch (err) {
      console.error("Failed to download report:", err);
      toast.error("Failed to download compliance report");
    }
  };

  if (isLoading) {
    return <DashboardSkeleton title="Admin Dashboard" subtitle="Loading system statistics..." />;
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-semibold">Admin Dashboard</h2>
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>
            Failed to load statistics. Please try again.
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => refetch()} 
              className="ml-2"
            >
              <RefreshCw className="h-3 w-3 mr-1" />
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const data = stats as AdminStats;

  // Prepare chart data
  const usersChartData = data?.users_by_role 
    ? Object.entries(data.users_by_role).map(([role, count]) => ({
        role: role.charAt(0).toUpperCase() + role.slice(1).toLowerCase(),
        count,
      }))
    : [];

  const appointmentsChartData = data?.appointments_by_status
    ? Object.entries(data.appointments_by_status).map(([status, count]) => ({
        status: status.charAt(0).toUpperCase() + status.slice(1).toLowerCase(),
        count,
      }))
    : [];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold">Admin Dashboard</h2>
        <p className="text-sm text-muted-foreground">
          System overview and management statistics
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={<Users className="h-4 w-4" />}
          title="Total Users"
          value={data?.users_by_role ? Object.values(data.users_by_role).reduce((a, b) => a + b, 0) : 0}
          subtitle="Across all roles"
        />
        <StatCard
          icon={<UserRound className="h-4 w-4" />}
          title="Patients"
          value={data?.patient_count || 0}
          subtitle="Registered patients"
        />
        <StatCard
          icon={<FileText className="h-4 w-4" />}
          title="Records"
          value={data?.record_count || 0}
          subtitle="Medical records"
        />
        <StatCard
          icon={<Calendar className="h-4 w-4" />}
          title="Appointments"
          value={data?.appointments_by_status ? Object.values(data.appointments_by_status).reduce((a, b) => a + b, 0) : 0}
          subtitle="Total appointments"
        />
      </div>

      {/* Charts Row */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Users by Role Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Users by Role</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[200px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={usersChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="role" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Appointments by Status Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Appointments by Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[200px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={appointmentsChartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="count"
                  >
                    {appointmentsChartData.map((_entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-2 flex flex-wrap gap-2 justify-center">
              {appointmentsChartData.map((entry, index) => (
                <div key={entry.status} className="flex items-center gap-1 text-xs">
                  <div 
                    className="w-3 h-3 rounded-full" 
                    style={{ backgroundColor: COLORS[index % COLORS.length] }}
                  />
                  <span>{entry.status}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Report Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Compliance Report</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-end gap-3">
            <div className="space-y-1">
              <Label htmlFor="admin-from-date" className="text-xs">From Date</Label>
              <Input
                id="admin-from-date"
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
                className="w-40"
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="admin-to-date" className="text-xs">To Date</Label>
              <Input
                id="admin-to-date"
                type="date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
                className="w-40"
              />
            </div>
            <Button onClick={handleDownloadComplianceReport}>
              <Download className="h-4 w-4 mr-2" />
              Download CSV
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Recent Audit Events */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Shield className="h-4 w-4" />
            Recent Audit Events
          </CardTitle>
        </CardHeader>
        <CardContent>
          {data?.recent_audit_events && data.recent_audit_events.length > 0 ? (
            <div className="space-y-2">
              {data.recent_audit_events.map((event) => (
                <div 
                  key={event.id} 
                  className="flex items-center justify-between rounded-md border p-3 text-sm"
                >
                  <div className="flex items-center gap-3">
                    {event.status === "success" ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : event.status === "error" ? (
                      <AlertTriangle className="h-4 w-4 text-red-500" />
                    ) : (
                      <Activity className="h-4 w-4 text-blue-500" />
                    )}
                    <div>
                      <p className="font-medium">{event.action}</p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(event.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <Badge variant={event.status === "success" ? "default" : "destructive"}>
                    {event.status}
                  </Badge>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No recent audit events</p>
          )}
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
}: {
  icon: React.ReactNode;
  title: string;
  value: number;
  subtitle: string;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value.toLocaleString()}</div>
        <p className="text-xs text-muted-foreground">{subtitle}</p>
      </CardContent>
    </Card>
  );
}
