/** Version History Component for Phase 5.
 *
 * Display immutable version history of records.
 */
import { useState, useEffect } from "react";
import { History, GitCommit, User, Clock, Hash, ChevronDown, ChevronUp } from "lucide-react";
import { versionService, type RecordVersion } from "@/services/versionService";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

interface VersionHistoryProps {
  recordId: string;
}

export function VersionHistory({ recordId }: VersionHistoryProps) {
  const [versions, setVersions] = useState<RecordVersion[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedVersion, setExpandedVersion] = useState<number | null>(null);

  useEffect(() => {
    fetchVersions();
  }, [recordId]);

  const fetchVersions = async () => {
    try {
      setIsLoading(true);
      const data = await versionService.listVersions(recordId);
      setVersions(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load versions");
    } finally {
      setIsLoading(false);
    }
  };

  const toggleExpand = (version: number) => {
    setExpandedVersion(expandedVersion === version ? null : version);
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

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  if (versions.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <History className="h-4 w-4" />
            Version History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-6 text-muted-foreground">
            <GitCommit className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No versions yet</p>
            <p className="text-xs">Versions are created when records are updated</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <History className="h-4 w-4" />
          Version History
          <Badge variant="secondary">{versions.length}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-4 top-0 bottom-0 w-px bg-border" />
          
          <div className="space-y-4">
            {versions.map((version, index) => (
              <Collapsible
                key={version.id}
                open={expandedVersion === version.version}
                onOpenChange={() => toggleExpand(version.version)}
              >
                <div className="relative pl-10">
                  {/* Timeline dot */}
                  <div className="absolute left-2 top-1.5 h-4 w-4 rounded-full border-2 border-background bg-primary" />
                  
                  <CollapsibleTrigger asChild>
                    <div className="flex items-center justify-between p-3 border rounded-lg bg-card hover:bg-muted/50 cursor-pointer transition-colors">
                      <div className="flex items-center gap-3">
                        <Badge variant={index === 0 ? "default" : "secondary"}>
                          v{version.version}
                        </Badge>
                        <div className="flex items-center gap-1 text-sm text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          {new Date(version.created_at).toLocaleString()}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {index === 0 && (
                          <Badge variant="outline" className="text-xs">
                            Latest
                          </Badge>
                        )}
                        <Button variant="ghost" size="sm">
                          {expandedVersion === version.version ? (
                            <ChevronUp className="h-4 w-4" />
                          ) : (
                            <ChevronDown className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    </div>
                  </CollapsibleTrigger>
                  
                  <CollapsibleContent>
                    <div className="mt-2 p-3 border rounded-lg bg-muted/50 space-y-2">
                      <div className="flex items-center gap-2 text-sm">
                        <User className="h-4 w-4 text-muted-foreground" />
                        <span className="text-muted-foreground">Created by:</span>
                        <span className="font-mono text-xs">
                          {version.created_by.slice(0, 8)}...
                        </span>
                      </div>
                      
                      <div className="flex items-start gap-2 text-sm">
                        <Hash className="h-4 w-4 text-muted-foreground mt-0.5" />
                        <div className="flex-1">
                          <span className="text-muted-foreground">Hash:</span>
                          <code className="block mt-1 p-2 bg-background rounded text-xs font-mono break-all">
                            {version.hash}
                          </code>
                        </div>
                      </div>
                      
                      <div className="pt-2 border-t">
                        <p className="text-xs text-muted-foreground">
                          This version snapshot contains the full encrypted record state
                          at the time of the update.
                        </p>
                      </div>
                    </div>
                  </CollapsibleContent>
                </div>
              </Collapsible>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
