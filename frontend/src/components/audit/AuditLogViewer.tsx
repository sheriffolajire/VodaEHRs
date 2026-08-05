/** Audit Log Viewer Component for Phase 5.
 *
 * Admins can view and verify tamper-evident audit logs.
 */
import { useState, useEffect } from "react";
import { ShieldCheck, AlertTriangle, Search, Filter, RefreshCw, CheckCircle, XCircle, Hash } from "lucide-react";
import { auditService, type AuditLog, type ChainStatus } from "@/services/auditService";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

const actionLabels: Record<string, string> = {
  "record.view": "Record Viewed",
  "record.create": "Record Created",
  "record.update": "Record Updated",
  "consent.grant": "Consent Granted",
  "consent.revoke": "Consent Revoked",
  "emergency.access": "Emergency Access",
  "record.tamper_detected": "Tamper Detected",
  "auth.login.success": "Login Success",
  "auth.login.failure": "Login Failed",
  "auth.logout": "Logout",
  "auth.refresh": "Token Refreshed",
  "auth.password_reset_request": "Password Reset Requested",
  "auth.password_reset_confirm": "Password Reset Completed",
  "patient.register": "Patient Registered",
  "patient.view": "Patient Viewed",
  "patient.update": "Patient Updated",
  "patient.search": "Patient Search",
};

export function AuditLogViewer() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [actions, setActions] = useState<string[]>([]);
  const [chainStatus, setChainStatus] = useState<ChainStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isVerifying, setIsVerifying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  const [filterAction, setFilterAction] = useState<string>("");
  const [filterPriority, setFilterPriority] = useState<string>("");
  const [verifyResult, setVerifyResult] = useState<{ is_valid: boolean; message: string; broken_at?: number | null } | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  // Auto-verify chain on load
  useEffect(() => {
    if (logs.length > 0 && !verifyResult) {
      handleVerifyChain();
    }
  }, [logs]);

  const fetchData = async () => {
    try {
      setIsLoading(true);
      const [logsData, actionsData, statusData] = await Promise.all([
        auditService.listAuditLogs({ limit: 1000 }),
        auditService.listActions(),
        auditService.getChainStatus(),
      ]);
      setLogs(logsData);
      setActions(actionsData);
      setChainStatus(statusData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load audit logs");
    } finally {
      setIsLoading(false);
    }
  };

  const handleFilter = async () => {
    try {
      setIsLoading(true);
      const filters: { action?: string; priority?: string; limit: number } = { limit: 1000 };
      if (filterAction) filters.action = filterAction;
      if (filterPriority) filters.priority = filterPriority;
      
      const data = await auditService.listAuditLogs(filters);
      setLogs(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to filter logs");
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyChain = async () => {
    try {
      setIsVerifying(true);
      const result = await auditService.verifyChain();
      setVerifyResult(result);
      // Refresh chain status
      const status = await auditService.getChainStatus();
      setChainStatus(status);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to verify chain");
    } finally {
      setIsVerifying(false);
    }
  };

  const getActionBadge = (action: string) => {
    const colors: Record<string, string> = {
      "record.view": "bg-blue-100 text-blue-800",
      "record.create": "bg-green-100 text-green-800",
      "record.update": "bg-yellow-100 text-yellow-800",
      "consent.grant": "bg-purple-100 text-purple-800",
      "consent.revoke": "bg-orange-100 text-orange-800",
      "emergency.access": "bg-red-100 text-red-800",
      "record.tamper_detected": "bg-red-600 text-white",
      "auth.login.success": "bg-emerald-100 text-emerald-800",
      "auth.login.failure": "bg-red-100 text-red-800",
      "auth.logout": "bg-gray-100 text-gray-800",
      "auth.refresh": "bg-blue-50 text-blue-700",
      "auth.password_reset_request": "bg-amber-100 text-amber-800",
      "auth.password_reset_confirm": "bg-emerald-100 text-emerald-800",
      "patient.register": "bg-teal-100 text-teal-800",
      "patient.view": "bg-cyan-100 text-cyan-800",
      "patient.update": "bg-indigo-100 text-indigo-800",
      "patient.search": "bg-slate-100 text-slate-800",
    };
    return colors[action] || "bg-gray-100 text-gray-800";
  };

  const getPriorityBadge = (priority: string) => {
    if (priority === "HIGH") {
      return <Badge className="bg-red-600">HIGH</Badge>;
    }
    return <Badge variant="secondary">NORMAL</Badge>;
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Chain Status Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-primary" />
            Audit Chain Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {chainStatus && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 border rounded-lg">
                <div className="text-sm text-muted-foreground">Chain Status</div>
                <div className="flex items-center gap-2 mt-1">
                  {chainStatus.chain_ok ? (
                    <>
                      <CheckCircle className="h-5 w-5 text-green-600" />
                      <span className="font-medium text-green-600">Valid</span>
                    </>
                  ) : (
                    <>
                      <XCircle className="h-5 w-5 text-red-600" />
                      <span className="font-medium text-red-600">Broken</span>
                    </>
                  )}
                </div>
              </div>
              
              <div className="p-4 border rounded-lg">
                <div className="text-sm text-muted-foreground">Total Entries</div>
                <div className="text-2xl font-bold mt-1">
                  {chainStatus.total_entries.toLocaleString()}
                </div>
              </div>
              
              <div className="p-4 border rounded-lg">
                <div className="text-sm text-muted-foreground">Last Entry</div>
                <div className="text-sm font-medium mt-1">
                  {chainStatus.last_entry_time
                    ? new Date(chainStatus.last_entry_time).toLocaleDateString()
                    : "N/A"}
                </div>
              </div>
              
              <div className="p-4 border rounded-lg flex items-center justify-center">
                <Button
                  onClick={handleVerifyChain}
                  disabled={isVerifying}
                  className="w-full"
                >
                  {isVerifying ? (
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <ShieldCheck className="h-4 w-4 mr-2" />
                  )}
                  Verify Chain
                </Button>
              </div>
            </div>
          )}

          {verifyResult && (
            <Alert className={verifyResult.is_valid ? "bg-green-50 border-green-200 mt-4" : "bg-red-50 border-red-200 mt-4"}>
              {verifyResult.is_valid ? (
                <CheckCircle className="h-4 w-4 text-green-600" />
              ) : (
                <AlertTriangle className="h-4 w-4 text-red-600" />
              )}
              <AlertDescription className={verifyResult.is_valid ? "text-green-800" : "text-red-800"}>
                {verifyResult.message}
                {!verifyResult.is_valid && verifyResult.broken_at !== null && verifyResult.broken_at !== undefined && (
                  <span className="block mt-1 font-semibold">
                    Check log entry #{verifyResult.broken_at} (index {verifyResult.broken_at})
                  </span>
                )}
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Filter className="h-4 w-4" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <Select value={filterAction} onValueChange={setFilterAction}>
                <SelectTrigger>
                  <SelectValue placeholder="Filter by action" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Actions</SelectItem>
                  {actions.map((action) => (
                    <SelectItem key={action} value={action}>
                      {actionLabels[action] || action}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex-1 min-w-[200px]">
              <Select value={filterPriority} onValueChange={setFilterPriority}>
                <SelectTrigger>
                  <SelectValue placeholder="Filter by priority" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Priorities</SelectItem>
                  <SelectItem value="NORMAL">Normal</SelectItem>
                  <SelectItem value="HIGH">High</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <Button onClick={handleFilter}>
              <Search className="h-4 w-4 mr-2" />
              Apply Filters
            </Button>
            
            <Button variant="outline" onClick={fetchData}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Audit Logs */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Hash className="h-4 w-4" />
            Audit Logs
            <Badge variant="secondary">{logs.length}</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[500px]">
            <div className="space-y-2">
              {logs.map((log, index) => (
                <div
                  key={log.id}
                  onClick={() => setSelectedLog(log)}
                  className="p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge variant="outline" className="font-mono text-xs">
                          #{logs.length - index}
                        </Badge>
                        <Badge className={getActionBadge(log.action)}>
                          {actionLabels[log.action] || log.action}
                        </Badge>
                        {getPriorityBadge(log.priority)}
                        <span className="text-xs text-muted-foreground">
                          {new Date(log.timestamp).toLocaleString()}
                        </span>
                      </div>
                      
                      {log.reason && (
                        <p className="text-sm text-muted-foreground mt-2 truncate">
                          {log.reason}
                        </p>
                      )}
                      
                      <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                        {log.clinician_name ? (
                          <span className="font-medium text-foreground">User: {log.clinician_name}</span>
                        ) : log.clinician_id ? (
                          <span>User: {log.clinician_id.slice(0, 8)}...</span>
                        ) : null}
                        {log.patient_name ? (
                          <span className="font-medium text-foreground">Patient: {log.patient_name}</span>
                        ) : log.patient_id ? (
                          <span>Patient: {log.patient_id.slice(0, 8)}...</span>
                        ) : null}
                        <span className="font-mono">Hash: {log.hash.slice(0, 16)}...</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Log Detail Dialog */}
      <Dialog open={!!selectedLog} onOpenChange={() => setSelectedLog(null)}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Hash className="h-5 w-5" />
              Audit Log Details
            </DialogTitle>
            <DialogDescription>
              View complete audit log entry and hash chain information.
            </DialogDescription>
          </DialogHeader>
          
          {selectedLog && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-muted-foreground">Log Index</div>
                  <Badge variant="outline" className="font-mono">
                    #{logs.findIndex(l => l.id === selectedLog.id) !== -1 ? logs.length - logs.findIndex(l => l.id === selectedLog.id) : 'N/A'}
                  </Badge>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Priority</div>
                  {getPriorityBadge(selectedLog.priority)}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-muted-foreground">Action</div>
                  <Badge className={getActionBadge(selectedLog.action)}>
                    {actionLabels[selectedLog.action] || selectedLog.action}
                  </Badge>
                </div>
              </div>
              
              <div>
                <div className="text-sm text-muted-foreground">Timestamp</div>
                <div className="font-medium">
                  {new Date(selectedLog.timestamp).toLocaleString()}
                </div>
              </div>
              
              {selectedLog.reason && (
                <div>
                  <div className="text-sm text-muted-foreground">Reason</div>
                  <div className="text-sm">{selectedLog.reason}</div>
                </div>
              )}
              
              {(selectedLog.clinician_name || selectedLog.clinician_id) && (
                <div>
                  <div className="text-sm text-muted-foreground">User</div>
                  <div className="font-medium">
                    {selectedLog.clinician_name || selectedLog.clinician_id}
                  </div>
                </div>
              )}
              
              {(selectedLog.patient_name || selectedLog.patient_id) && (
                <div>
                  <div className="text-sm text-muted-foreground">Patient</div>
                  <div className="font-medium">
                    {selectedLog.patient_name || selectedLog.patient_id}
                  </div>
                </div>
              )}
              
              <Separator />
              
              <div>
                <div className="text-sm text-muted-foreground mb-2">Hash Chain</div>
                <div className="space-y-2">
                  <div>
                    <div className="text-xs text-muted-foreground">Previous Hash</div>
                    <code className="block p-2 bg-muted rounded text-xs font-mono break-all">
                      {selectedLog.prev_hash || "Genesis (none)"}
                    </code>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground">Entry Hash</div>
                    <code className="block p-2 bg-muted rounded text-xs font-mono break-all">
                      {selectedLog.hash}
                    </code>
                  </div>
                </div>
              </div>
              
              <div className="flex justify-end">
                <Button variant="outline" onClick={() => setSelectedLog(null)}>
                  Close
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
