/**
 * Compliance Reports Page
 * 
 * Dedicated page for auditors to generate and download
 * compliance audit reports with date range selection.
 */

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { 
  FileText, 
  Download, 
  Calendar,
  Filter,
  Clock,
  Shield,
  AlertCircle,
  CheckCircle2
} from "lucide-react";
import { downloadComplianceReport } from "@/services/reportService";
import { getAuditorStats } from "@/services/statsService";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";

// Preset date ranges
const PRESETS = [
  { label: "Last 7 Days", days: 7 },
  { label: "Last 30 Days", days: 30 },
  { label: "Last 90 Days", days: 90 },
  { label: "Last Year", days: 365 },
];

export function ComplianceReportsPage() {
  // Date range state
  const today = new Date();
  const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
  
  const [fromDate, setFromDate] = useState(thirtyDaysAgo.toISOString().split('T')[0]);
  const [toDate, setToDate] = useState(today.toISOString().split('T')[0]);
  const [isGenerating, setIsGenerating] = useState(false);

  // Fetch stats for context
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["auditor-stats"],
    queryFn: getAuditorStats,
  });

  const handlePresetClick = (days: number) => {
    const end = new Date();
    const start = new Date(Date.now() - days * 24 * 60 * 60 * 1000);
    setFromDate(start.toISOString().split('T')[0]);
    setToDate(end.toISOString().split('T')[0]);
  };

  const handleDownload = async () => {
    try {
      const from = new Date(fromDate);
      const to = new Date(toDate);
      
      if (from > to) {
        toast.error("From date must be before To date");
        return;
      }
      
      setIsGenerating(true);
      await downloadComplianceReport({ 
        fromDate: from,
        toDate: to
      });
      toast.success("Compliance report downloaded successfully");
    } catch (err) {
      console.error("Failed to download report:", err);
      toast.error("Failed to download compliance report");
    } finally {
      setIsGenerating(false);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Compliance Reports</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Generate and download compliance audit reports for regulatory review
          </p>
        </div>
        <Badge variant="secondary" className="flex items-center gap-1">
          <Shield className="h-3 w-3" />
          Auditor Access
        </Badge>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Report Generation Panel */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-primary" />
              <CardTitle>Generate Report</CardTitle>
            </div>
            <CardDescription>
              Select a date range to generate a compliance audit report
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Preset Buttons */}
            <div className="space-y-2">
              <Label className="text-xs font-medium uppercase text-muted-foreground">
                Quick Select
              </Label>
              <div className="flex flex-wrap gap-2">
                {PRESETS.map((preset) => (
                  <Button
                    key={preset.days}
                    variant="outline"
                    size="sm"
                    onClick={() => handlePresetClick(preset.days)}
                  >
                    <Clock className="h-3 w-3 mr-1" />
                    {preset.label}
                  </Button>
                ))}
              </div>
            </div>

            <Separator />

            {/* Date Range Inputs */}
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="from-date" className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  From Date
                </Label>
                <Input
                  id="from-date"
                  type="date"
                  value={fromDate}
                  onChange={(e) => setFromDate(e.target.value)}
                  max={toDate}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="to-date" className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  To Date
                </Label>
                <Input
                  id="to-date"
                  type="date"
                  value={toDate}
                  onChange={(e) => setToDate(e.target.value)}
                  min={fromDate}
                />
              </div>
            </div>

            {/* Selected Range Display */}
            <div className="rounded-lg bg-muted p-4">
              <div className="flex items-center gap-2 text-sm">
                <Filter className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">Report period:</span>
                <span className="font-medium">
                  {formatDate(fromDate)} — {formatDate(toDate)}
                </span>
              </div>
            </div>

            {/* Generate Button */}
            <Button 
              onClick={handleDownload} 
              disabled={isGenerating}
              className="w-full"
              size="lg"
            >
              {isGenerating ? (
                <>
                  <Clock className="mr-2 h-4 w-4 animate-spin" />
                  Generating Report...
                </>
              ) : (
                <>
                  <Download className="mr-2 h-4 w-4" />
                  Download Compliance Report (CSV)
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Info Panel */}
        <div className="space-y-6">
          {/* Report Contents */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Report Contents</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="h-4 w-4 text-green-500 dark:text-green-400 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium">Audit Summary Statistics</p>
                  <p className="text-muted-foreground">Total events, access patterns, and trends</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <CheckCircle2 className="h-4 w-4 text-green-500 dark:text-green-400 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium">Emergency Access Events</p>
                  <p className="text-muted-foreground">Break-glass usage and approvals</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <CheckCircle2 className="h-4 w-4 text-green-500 dark:text-green-400 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium">Chain Integrity Status</p>
                  <p className="text-muted-foreground">Verification results and issues</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <CheckCircle2 className="h-4 w-4 text-green-500 dark:text-green-400 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium">User Activity Logs</p>
                  <p className="text-muted-foreground">Detailed audit trail for the period</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Current Stats Preview */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Current Audit Status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {statsLoading ? (
                <p className="text-sm text-muted-foreground">Loading...</p>
              ) : stats ? (
                <>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Total Entries</span>
                    <Badge variant="secondary">{stats.total_entries.toLocaleString()}</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Break-Glass Events</span>
                    <Badge variant={stats.break_glass_count > 0 ? "destructive" : "secondary"}>
                      {stats.break_glass_count}
                    </Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Chain Integrity</span>
                    <Badge variant={stats.chain_ok ? "default" : "destructive"}>
                      {stats.chain_ok ? "Verified" : "Issues"}
                    </Badge>
                  </div>
                  {stats.last_entry_time && (
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Last Entry</span>
                      <span className="text-xs text-muted-foreground">
                        {new Date(stats.last_entry_time).toLocaleString()}
                      </span>
                    </div>
                  )}
                </>
              ) : (
                <div className="flex items-center gap-2 text-sm text-amber-600">
                  <AlertCircle className="h-4 w-4" />
                  Failed to load stats
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
