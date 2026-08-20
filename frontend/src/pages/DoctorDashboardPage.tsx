/**
 * Doctor/Nurse Dashboard Page - Phase 6
 * 
 * Provides assigned patients, upcoming appointments, recent records,
 * and emergency access status for clinicians.
 */

import { useQuery } from "@tanstack/react-query";
import { 
  Users, 
  Calendar, 
  FileText, 
  AlertTriangle,
  Clock,
  UserRound,
  Stethoscope
} from "lucide-react";
import { getDoctorStats, type DoctorStats } from "@/services/statsService";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

export function DoctorDashboardPage() {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ["doctor-stats"],
    queryFn: getDoctorStats,
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-semibold">Doctor Dashboard</h2>
        <p className="text-sm text-muted-foreground">Loading statistics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-semibold">Doctor Dashboard</h2>
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm text-red-600">Failed to load statistics</p>
        </div>
      </div>
    );
  }

  const data = stats as DoctorStats;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold">Doctor Dashboard</h2>
        <p className="text-sm text-muted-foreground">
          Your patients, appointments, and recent activity
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
          title="Upcoming Appointments"
          value={data?.upcoming_appointments?.length || 0}
          subtitle="Next 7 days"
        />
        <StatCard
          icon={<FileText className="h-4 w-4" />}
          title="Recent Records"
          value={data?.recent_records?.length || 0}
          subtitle="Last 10 records"
        />
        <Card className={data?.active_emergency_access ? "border-orange-200 bg-orange-50" : ""}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Emergency Access</CardTitle>
            <AlertTriangle className={`h-4 w-4 ${data?.active_emergency_access ? "text-orange-500" : "text-muted-foreground"}`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {data?.active_emergency_access ? (
                <span className="text-orange-600">Active</span>
              ) : (
                <span className="text-muted-foreground">Inactive</span>
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              {data?.active_emergency_access ? "Break-glass enabled" : "Normal access mode"}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Upcoming Appointments */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              Upcoming Appointments
            </CardTitle>
            <Button variant="outline" size="sm" asChild>
              <Link to="/patients">View All</Link>
            </Button>
          </CardHeader>
          <CardContent>
            {data?.upcoming_appointments && data.upcoming_appointments.length > 0 ? (
              <div className="space-y-3">
                {data.upcoming_appointments.map((apt) => (
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
                      {Math.ceil((new Date(apt.scheduled_at).getTime() - Date.now()) / (1000 * 60 * 60))}h
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <Calendar className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
                <p className="text-sm text-muted-foreground">No upcoming appointments</p>
                <Button variant="outline" size="sm" className="mt-3" asChild>
                  <Link to="/patients">Schedule Appointment</Link>
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Records */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Recent Records
            </CardTitle>
            <Button variant="outline" size="sm" asChild>
              <Link to="/patients">View All</Link>
            </Button>
          </CardHeader>
          <CardContent>
            {data?.recent_records && data.recent_records.length > 0 ? (
              <div className="space-y-3">
                {data.recent_records.map((record) => (
                  <div 
                    key={record.id} 
                    className="flex items-center justify-between rounded-md border p-3"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100">
                        <Stethoscope className="h-5 w-5 text-green-600" />
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
                <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
                <p className="text-sm text-muted-foreground">No recent records</p>
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
              <Link to="/emergency-access">Emergency Access</Link>
            </Button>
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
