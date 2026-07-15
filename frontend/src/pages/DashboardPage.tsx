import { useQuery } from "@tanstack/react-query";
import { fetchHealth } from "@/services/healthService";

export function DashboardPage() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
  });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold">Dashboard</h2>
        <p className="text-sm text-muted-foreground">Phase 1 foundation shell.</p>
      </div>

      <div className="rounded-lg border bg-card p-6">
        <h3 className="mb-2 text-sm font-medium">Backend Connectivity</h3>
        {isLoading && <p className="text-sm text-muted-foreground">Checking backend…</p>}
        {isError && <p className="text-sm text-red-500">Backend unreachable: {error.message}</p>}
        {data && (
          <p className="text-sm text-green-600">
            Backend healthy — status: {data.status} ({data.environment})
          </p>
        )}
      </div>
    </div>
  );
}
