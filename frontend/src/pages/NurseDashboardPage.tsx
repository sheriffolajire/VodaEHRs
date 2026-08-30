/**
 * Nurse Dashboard Page - Phase 6
 *
 * Provides assigned patients, upcoming appointments, recent records,
 * and task management for nursing staff.
 */

import { useQuery } from "@tanstack/react-query";
import {
  Users,
  Calendar,
  FileText,
  ClipboardList,
  Clock,
  UserRound,
  HeartPulse,
  Activity,
} from "lucide-react";
import { getDoctorStats, type DoctorStats } from "@/services/statsService";
import { getTaskStats, type TaskStats } from "@/services/nursingTaskService";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

export function NurseDashboardPage() {
  const { data: stats, isLoading: statsLoading, error: statsError } = useQuery({
    queryKey: ["nurse-stats"],
    queryFn: getDoctorStats,
  });

  const { data: taskStats, isLoading: tasksLoading } = useQuery({
    queryKey: ["nurse-task-stats"],
    queryFn: getTaskStats,
  });

  const isLoading = statsLoading || tasksLoading;

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-semibold">Nurse Dashboard</h2>
        <p className="text-sm text-muted-foreground">Loading statistics...</p>
      </div>
    );
  }

  if (statsError) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-semibold">Nurse Dashboard</h2>
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm text-red-600">Failed to load statistics</p>
        </div>
      </div>
    );
  }

  const data = stats as DoctorStats;
  const tasks = taskStats as TaskStats | undefined;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold">Nurse Dashboard</h2>
        <p className="text-sm text-muted-foreground">
          Your assigned patients, tasks, and care activities
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={<Users className="h-4 w-4" />}
          title="Assigned Patients"
          value={data?.assigned_patients || 0}
          subtitle="Under your care"
          href="/patients"
        />
        <StatCard
          icon={<Calendar className="h-4 w-4" />}
          title="Today's Appointments"
          value={data?.upcoming_appointments?.length || 0}
          subtitle="Scheduled today"
        />
        <StatCard
          icon={<ClipboardList className="h-4 w-4" />}
          title="Pending Tasks"
          value={tasks?.pending_count || 0}
          subtitle="To be completed"
          href="/tasks"
          variant={tasks?.pending_count && tasks.pending_count > 0 ? "warning" : "default"}
        />
        <StatCard
          icon={<HeartPulse className="h-4 w-4" />}
          title="Vitals Due"
          value={tasks?.vitals_due_count || 0}
          subtitle="Patients needing check"
          href="/tasks"
          variant={tasks?.vitals_due_count && tasks.vitals_due_count > 0 ? "warning" : "default"}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Today's Schedule */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              Today's Schedule
            </CardTitle>
            <Button variant="outline" size="sm" asChild>
              <Link to="/patients">View All</Link>
            </Button>
          </CardHeader>
          <CardContent>
            {data?.upcoming_appointments && data.upcoming_appointments.length > 0 ? (
              <div className="space-y-3">
                {data.upcoming_appointments.slice(0, 5).map((apt) => (
                  <div
                    key={apt.id}
                    className="flex items-center justify-between rounded-md border p-3"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                        <UserRound className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <p className="font-medium text-sm">{apt.patient_name}</p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(apt.scheduled_at).toLocaleString()}
                        </p>
                        {apt.reason && (
                          <p className="text-xs text-muted-foreground truncate max-w-[200px]">
                            {apt.reason}
                          </p>
                        )}
                      </div>
                    </div>
                    <Badge variant="outline">
                      <Clock className="h-3 w-3 mr-1" />
                      {Math.ceil(
                        (new Date(apt.scheduled_at).getTime() - Date.now()) /
                          (1000 * 60 * 60)
                      )}h
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <Calendar className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
                <p className="text-sm text-muted-foreground">
                  No appointments scheduled today
                </p>
                <Button variant="outline" size="sm" className="mt-3" asChild>
                  <Link to="/patients">View Patients</Link>
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Patient Activity */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Recent Patient Activity
            </CardTitle>
            <Button variant="outline" size="sm" asChild>
              <Link to="/patients">View All</Link>
            </Button>
          </CardHeader>
          <CardContent>
            {data?.recent_records && data.recent_records.length > 0 ? (
              <div className="space-y-3">
                {data.recent_records.slice(0, 5).map((record) => (
                  <div
                    key={record.id}
                    className="flex items-center justify-between rounded-md border p-3"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100">
                        <FileText className="h-5 w-5 text-green-600" />
                      </div>
                      <div>
                        <p className="font-medium text-sm capitalize">
                          {record.record_type.replace("_", " ")}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(record.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm" asChild>
                      <Link to={`/patients/${record.patient_id}`}>View</Link>
                    </Button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <Activity className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
                <p className="text-sm text-muted-foreground">
                  No recent patient activity
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            <Button asChild>
              <Link to="/patients">View Patients</Link>
            </Button>
            <Button variant="outline" asChild>
              <Link to="/tasks">My Tasks</Link>
            </Button>
            <Button variant="outline" asChild>
              <Link to="/patients">Record Vitals</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

const VARIANT_STYLES = {
  default: "",
  warning: "border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/30",
  error: "border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950/30",
};

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
  value: number;
  subtitle: string;
  href?: string;
  variant?: "default" | "warning" | "error";
}) {
  const content = (
    <>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className={`text-2xl font-bold ${
          variant === "warning" ? "text-amber-600 dark:text-amber-400" :
          variant === "error" ? "text-red-600 dark:text-red-400" : ""
        }`}>
          {value.toLocaleString()}
        </div>
        <p className="text-xs text-muted-foreground">{subtitle}</p>
      </CardContent>
    </>
  );

  if (href) {
    return (
      <Link to={href} className="block">
        <Card className={`hover:bg-muted/50 transition-colors cursor-pointer ${VARIANT_STYLES[variant]}`}>
          {content}
        </Card>
      </Link>
    );
  }

  return <Card className={VARIANT_STYLES[variant]}>{content}</Card>;
}
