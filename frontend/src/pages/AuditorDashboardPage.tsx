/**
 * Auditor Dashboard Page - Phase 6
 * 
 * Provides audit volume, break-glass events, chain integrity,
 * and compliance metrics for auditors.
 */

import { useQuery } from "@tanstack/react-query";
import { 
  Shield, 
  AlertTriangle, 
  CheckCircle, 
  Activity,
  FileText,
  Clock,
  Link as LinkIcon,
  History,
  Download
} from "lucide-react";
import { getAuditorStats, type AuditorStats } from "@/services/statsService";
import { downloadComplianceReport } from "@/services/reportService";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
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

const COLORS = {
  ok: "#22c55e",
  warning: "#f59e0b",
  error: "#ef4444",
};

export function AuditorDashboardPage() {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ["auditor-stats"],
    queryFn: getAuditorStats,
  });

  const handleDownloadComplianceReport = async () => {
    try {
      await downloadComplianceReport({ days: 30 });
    } catch (err) {
      console.error("Failed to download report:", err);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-semibold">Auditor Dashboard</h2>
        <p className="text-sm text-muted-foreground">Loading audit statistics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-semibold">Auditor Dashboard</h2>
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm text-red-600">Failed to load audit statistics</p>
        </div>
      </div>
    );
  }

  const data = stats as AuditorStats;

  // Prepare chart data
  const eventsChartData = data?.events_by_action
    ? Object.entries(data.events_by_action)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10)
        .map(([action, count]) => ({
          action: action.length > 20 ? action.substring(0, 20) + "..." : action,
          count,
        }))
    : [];

  const chainStatusData = [
    { name: "Valid", value: data?.chain_ok ? 1 : 0, color: COLORS.ok },
    { name: "Broken", value: data?.chain_ok ? 0 : 1, color: COLORS.error },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold">Auditor Dashboard</h2>
        <p className="text-sm text-muted-foreground">
          Audit trail overview and compliance metrics
        </p>
      </div>

      {/* Chain Integrity Status */}
      <Card className={data?.chain_ok ? "border-green-200 bg-green-50/50" : "border-red-200 bg-red-50/50"}>
        <CardContent className="pt-6">
          <div className="flex items-start gap-4">
            <div className={`flex h-12 w-12 items-center justify-center rounded-full ${data?.chain_ok ? "bg-green-100" : "bg-red-100"}`}>
              {data?.chain_ok ? (
                <CheckCircle className="h-6 w-6 text-green-600" />
              ) : (
                <AlertTriangle className="h-6 w-6 text-red-600" />
              )}
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-semibold">
                  Audit Chain {data?.chain_ok ? "Valid" : "Compromised"}
                </h3>
                <Badge variant={data?.chain_ok ? "default" : "destructive"}>
                  {data?.chain_ok ? "OK" : "ALERT"}
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                {data?.chain_ok 
                  ? "The audit log chain is intact and verified. All entries are tamper-evident."
                  : "CRITICAL: The audit log chain has been compromised. Immediate investigation required."
                }
              </p>
              <div className="flex flex-wrap gap-4 mt-3 text-sm">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  <span>{data?.total_entries?.toLocaleString() || 0} total entries</span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <span>
                    Last entry: {data?.last_entry_time 
                      ? new Date(data.last_entry_time).toLocaleString() 
                      : "N/A"
                    }
                  </span>
                </div>
              </div>
            </div>
            <Button variant={data?.chain_ok ? "outline" : "destructive"} asChild>
              <Link to="/audit">View Audit Logs</Link>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={<Activity className="h-4 w-4" />}
          title="Total Events"
          value={data?.total_entries || 0}
          subtitle="Audit log entries"
          href="/audit"
        />
        <StatCard
          icon={<AlertTriangle className="h-4 w-4" />}
          title="Break-Glass Events"
          value={data?.break_glass_count || 0}
          subtitle="Last 30 days"
          variant={data?.break_glass_count && data.break_glass_count > 0 ? "warning" : "default"}
        />
        <StatCard
          icon={<History className="h-4 w-4" />}
          title="Event Types"
          value={Object.keys(data?.events_by_action || {}).length}
          subtitle="Unique actions"
        />
        <StatCard
          icon={<Shield className="h-4 w-4" />}
          title="Chain Status"
          value={data?.chain_ok ? "Valid" : "Broken"}
          subtitle="Integrity check"
          variant={data?.chain_ok ? "success" : "error"}
        />
      </div>

      {/* Charts Row */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Events by Action Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Top Event Types (Last 30 Days)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {eventsChartData.length > 0 ? (
              <div className="h-[250px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={eventsChartData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" tick={{ fontSize: 12 }} />
                    <YAxis 
                      dataKey="action" 
                      type="category" 
                      width={120} 
                      tick={{ fontSize: 11 }}
                    />
                    <Tooltip />
                    <Bar dataKey="count" fill="#8884d8" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="text-center py-8">
                <Activity className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
                <p className="text-sm text-muted-foreground">No events in last 30 days</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Chain Status Visualization */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <LinkIcon className="h-4 w-4" />
              Chain Integrity
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[200px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={chainStatusData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {chainStatusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-2 flex justify-center gap-4">
              {chainStatusData.map((entry) => (
                <div key={entry.name} className="flex items-center gap-2 text-sm">
                  <div 
                    className="w-3 h-3 rounded-full" 
                    style={{ backgroundColor: entry.color }}
                  />
                  <span>{entry.name}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Audit Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            <Button asChild>
              <Link to="/audit">View Full Audit Log</Link>
            </Button>
            <Button variant="outline" asChild>
              <Link to="/emergency-access">Review Emergency Access</Link>
            </Button>
            <Button variant="outline" onClick={handleDownloadComplianceReport}>
              <Download className="h-4 w-4 mr-2" />
              Download Compliance Report
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Compliance Notice */}
      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <Shield className="h-5 w-5 text-blue-600 mt-0.5" />
            <div>
              <h4 className="font-medium text-blue-900">Audit Trail Compliance</h4>
              <p className="text-sm text-blue-700 mt-1">
                The audit log maintains a cryptographic hash chain ensuring tamper-evidence. 
                All access to patient data is logged with user identity, timestamp, and action details.
              </p>
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
  variant = "default",
}: {
  icon: React.ReactNode;
  title: string;
  value: string | number;
  subtitle: string;
  href?: string;
  variant?: "default" | "success" | "warning" | "error";
}) {
  const variantStyles = {
    default: "",
    success: "border-green-200 bg-green-50",
    warning: "border-yellow-200 bg-yellow-50",
    error: "border-red-200 bg-red-50",
  };

  const content = (
    <>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className={`text-2xl font-bold ${
          variant === "success" ? "text-green-600" :
          variant === "warning" ? "text-yellow-600" :
          variant === "error" ? "text-red-600" : ""
        }`}>
          {value}
        </div>
        <p className="text-xs text-muted-foreground">{subtitle}</p>
      </CardContent>
    </>
  );

  if (href) {
    return (
      <Link to={href} className="block">
        <Card className={`hover:bg-muted/50 transition-colors cursor-pointer ${variantStyles[variant]}`}>
          {content}
        </Card>
      </Link>
    );
  }

  return <Card className={variantStyles[variant]}>{content}</Card>;
}
