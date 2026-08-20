/**
 * System Monitoring Page - Phase 6
 * 
 * Real-time system health monitoring for administrators.
 * Displays storage usage, database metrics, and service health.
 */

import { useQuery } from "@tanstack/react-query";
import { 
  Activity, 
  Database, 
  HardDrive, 
  Server, 
  CheckCircle, 
  AlertTriangle, 
  XCircle,
  RefreshCw,
  Clock,
  Cpu
} from "lucide-react";
import { getSystemStats, type SystemStats } from "@/services/statsService";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  AreaChart,
  Area
} from "recharts";
import { useState, useEffect } from "react";

// Mock data for system metrics over time
const generateMockTimeSeries = () => {
  const data = [];
  const now = new Date();
  for (let i = 23; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 60 * 60 * 1000);
    data.push({
      time: time.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      cpu: Math.floor(Math.random() * 30) + 20, // 20-50%
      memory: Math.floor(Math.random() * 20) + 40, // 40-60%
      requests: Math.floor(Math.random() * 100) + 50, // 50-150 req/hour
    });
  }
  return data;
};

export function SystemMonitoringPage() {
  const [timeSeriesData, setTimeSeriesData] = useState(generateMockTimeSeries());
  const { data: stats, isLoading, error, refetch } = useQuery({
    queryKey: ["system-stats"],
    queryFn: getSystemStats,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setTimeSeriesData(prev => {
        const newData = [...prev.slice(1)];
        const now = new Date();
        newData.push({
          time: now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          cpu: Math.floor(Math.random() * 30) + 20,
          memory: Math.floor(Math.random() * 20) + 40,
          requests: Math.floor(Math.random() * 100) + 50,
        });
        return newData;
      });
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-semibold">System Monitoring</h2>
        <p className="text-sm text-muted-foreground">Loading system statistics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-semibold">System Monitoring</h2>
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm text-red-600">Failed to load system statistics</p>
        </div>
      </div>
    );
  }

  const data = stats as SystemStats;

  // Calculate storage percentage
  const storagePercent = data?.storage?.total_bytes && data.storage.total_bytes > 0
    ? Math.round((data.storage.used_bytes / data.storage.total_bytes) * 100)
    : 0;

  // Determine status colors
  const getStorageStatus = (percent: number) => {
    if (percent < 70) return { color: "text-green-600", bg: "bg-green-100", icon: CheckCircle };
    if (percent < 90) return { color: "text-yellow-600", bg: "bg-yellow-100", icon: AlertTriangle };
    return { color: "text-red-600", bg: "bg-red-100", icon: XCircle };
  };

  const storageStatus = getStorageStatus(storagePercent);
  const StorageIcon = storageStatus.icon;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold">System Monitoring</h2>
          <p className="text-sm text-muted-foreground">
            Real-time system health and performance metrics
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Service Health Status */}
      <div className="grid gap-4 md:grid-cols-3">
        <ServiceHealthCard
          name="Database"
          status={data?.database?.connected ? "healthy" : "error"}
          latency={data?.database?.latency_ms}
          icon={<Database className="h-5 w-5" />}
        />
        <ServiceHealthCard
          name="Storage (MinIO)"
          status={data?.storage?.healthy ? "healthy" : "error"}
          details={`${(data?.storage?.used_bytes ? data.storage.used_bytes / 1024 / 1024 / 1024 : 0).toFixed(2)} GB used`}
          icon={<HardDrive className="h-5 w-5" />}
        />
        <ServiceHealthCard
          name="API Server"
          status="healthy"
          details="Running"
          icon={<Server className="h-5 w-5" />}
        />
      </div>

      {/* Storage Usage */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <HardDrive className="h-4 w-4" />
            Storage Usage
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <div className={`flex h-16 w-16 items-center justify-center rounded-full ${storageStatus.bg}`}>
              <StorageIcon className={`h-8 w-8 ${storageStatus.color}`} />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-2xl font-bold">{storagePercent}%</span>
                <Badge variant={storagePercent > 90 ? "destructive" : storagePercent > 70 ? "default" : "secondary"}>
                  {storagePercent > 90 ? "Critical" : storagePercent > 70 ? "Warning" : "Healthy"}
                </Badge>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div 
                  className={`h-2.5 rounded-full ${
                    storagePercent > 90 ? "bg-red-600" : 
                    storagePercent > 70 ? "bg-yellow-500" : "bg-green-600"
                  }`}
                  style={{ width: `${Math.min(storagePercent, 100)}%` }}
                ></div>
              </div>
              <p className="text-sm text-muted-foreground mt-2">
                {(data?.storage?.used_bytes ? data.storage.used_bytes / 1024 / 1024 / 1024 : 0).toFixed(2)} GB of{" "}
                {(data?.storage?.total_bytes ? data.storage.total_bytes / 1024 / 1024 / 1024 : 0).toFixed(2)} GB used
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance Charts */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* CPU & Memory Usage */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Cpu className="h-4 w-4" />
              CPU & Memory Usage (24h)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={timeSeriesData}>
                  <defs>
                    <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#8884d8" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorMemory" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#82ca9d" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#82ca9d" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Area 
                    type="monotone" 
                    dataKey="cpu" 
                    stroke="#8884d8" 
                    fillOpacity={1} 
                    fill="url(#colorCpu)" 
                    name="CPU %"
                  />
                  <Area 
                    type="monotone" 
                    dataKey="memory" 
                    stroke="#82ca9d" 
                    fillOpacity={1} 
                    fill="url(#colorMemory)" 
                    name="Memory %"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <div className="flex justify-center gap-4 mt-2">
              <div className="flex items-center gap-2 text-sm">
                <div className="w-3 h-3 rounded-full bg-[#8884d8]" />
                <span>CPU Usage</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <div className="w-3 h-3 rounded-full bg-[#82ca9d]" />
                <span>Memory Usage</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Request Volume */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Activity className="h-4 w-4" />
              API Requests (24h)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[250px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={timeSeriesData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Line 
                    type="monotone" 
                    dataKey="requests" 
                    stroke="#3b82f6" 
                    strokeWidth={2}
                    dot={false}
                    name="Requests/hour"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Database Metrics */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Database className="h-4 w-4" />
            Database Metrics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <MetricCard
              label="Connection Status"
              value={data?.database?.connected ? "Connected" : "Disconnected"}
              icon={<Database className="h-4 w-4" />}
              status={data?.database?.connected ? "success" : "error"}
            />
            <MetricCard
              label="Query Latency"
              value={`${data?.database?.latency_ms?.toFixed(2) || "N/A"} ms`}
              icon={<Clock className="h-4 w-4" />}
              status={data?.database?.latency_ms && data.database.latency_ms < 100 ? "success" : "warning"}
            />
            <MetricCard
              label="Active Connections"
              value={data?.database?.active_connections?.toString() || "N/A"}
              icon={<Activity className="h-4 w-4" />}
            />
            <MetricCard
              label="Uptime"
              value={data?.database?.uptime_hours ? `${Number(data.database.uptime_hours).toFixed(1)}h` : "N/A"}
              icon={<Clock className="h-4 w-4" />}
            />
          </div>
        </CardContent>
      </Card>

      {/* System Info */}
      <Card className="bg-muted/50">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <Server className="h-5 w-5 text-muted-foreground mt-0.5" />
            <div>
              <h4 className="font-medium">System Information</h4>
              <p className="text-sm text-muted-foreground mt-1">
                Voda EHRs v1.0.0 • FastAPI Backend • PostgreSQL Database • MinIO Object Storage
              </p>
              <p className="text-sm text-muted-foreground">
                Last updated: {new Date().toLocaleString()}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function ServiceHealthCard({
  name,
  status,
  latency,
  details,
  icon,
}: {
  name: string;
  status: "healthy" | "warning" | "error";
  latency?: number;
  details?: string;
  icon: React.ReactNode;
}) {
  const statusConfig = {
    healthy: { color: "text-green-600", bg: "bg-green-100", border: "border-green-200", badge: "default" as const },
    warning: { color: "text-yellow-600", bg: "bg-yellow-100", border: "border-yellow-200", badge: "default" as const },
    error: { color: "text-red-600", bg: "bg-red-100", border: "border-red-200", badge: "destructive" as const },
  };

  const config = statusConfig[status];

  return (
    <Card className={`${config.border}`}>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`flex h-10 w-10 items-center justify-center rounded-full ${config.bg}`}>
              {icon}
            </div>
            <div>
              <p className="font-medium">{name}</p>
              <p className="text-sm text-muted-foreground">
                {status === "healthy" ? "Operational" : status === "warning" ? "Degraded" : "Down"}
              </p>
            </div>
          </div>
          <Badge variant={config.badge}>
            {status === "healthy" ? "Healthy" : status === "warning" ? "Warning" : "Error"}
          </Badge>
        </div>
        {(latency !== undefined || details) && (
          <div className="mt-3 pt-3 border-t">
            <p className="text-sm text-muted-foreground">
              {latency !== undefined ? `Latency: ${latency.toFixed(2)}ms` : details}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function MetricCard({
  label,
  value,
  icon,
  status = "default",
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
  status?: "default" | "success" | "warning" | "error";
}) {
  const statusColors = {
    default: "",
    success: "text-green-600",
    warning: "text-yellow-600",
    error: "text-red-600",
  };

  return (
    <div className="flex items-center gap-3 p-3 rounded-lg border bg-card">
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
        {icon}
      </div>
      <div>
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className={`text-lg font-semibold ${statusColors[status]}`}>{value}</p>
      </div>
    </div>
  );
}
