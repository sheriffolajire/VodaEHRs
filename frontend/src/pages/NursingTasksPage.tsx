/**
 * Nursing Tasks Page
 * 
 * Provides task management for nursing staff including:
 * - Viewing assigned tasks
 * - Updating task status
 * - Recording task completion
 */

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ClipboardList,
  CheckCircle2,
  Circle,
  Clock,
  AlertCircle,
  Calendar,
  User,
  ArrowRight,
} from "lucide-react";
import { listTasks, completeTask, startTask, type NursingTask } from "@/services/nursingTaskService";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { Link } from "react-router-dom";
import { CreateTaskDialog } from "@/components/tasks/CreateTaskDialog";

const TASK_TYPE_ICONS: Record<string, React.ReactNode> = {
  vitals: <ClipboardList className="h-4 w-4" />,
  medication: <AlertCircle className="h-4 w-4" />,
  wound_care: <ClipboardList className="h-4 w-4" />,
  patient_education: <User className="h-4 w-4" />,
  assessment: <ClipboardList className="h-4 w-4" />,
  documentation: <ClipboardList className="h-4 w-4" />,
  other: <ClipboardList className="h-4 w-4" />,
};

const PRIORITY_COLORS: Record<string, string> = {
  low: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
  normal: "bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400",
  high: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
  urgent: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
};

const STATUS_ICONS: Record<string, React.ReactNode> = {
  pending: <Circle className="h-5 w-5 text-muted-foreground" />,
  in_progress: <Clock className="h-5 w-5 text-amber-500" />,
  completed: <CheckCircle2 className="h-5 w-5 text-green-500" />,
  cancelled: <AlertCircle className="h-5 w-5 text-gray-500" />,
};

function formatDueDate(dueDate: string | null): string {
  if (!dueDate) return "No due date";
  const date = new Date(dueDate);
  const now = new Date();
  const diffHours = Math.ceil((date.getTime() - now.getTime()) / (1000 * 60 * 60));
  
  if (diffHours < 0) return `Overdue by ${Math.abs(diffHours)} hours`;
  if (diffHours < 24) return `Due in ${diffHours} hours`;
  return `Due ${date.toLocaleDateString()}`;
}

export function NursingTasksPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState("pending");

  // Fetch tasks for the active tab
  const { data: tasks, isLoading } = useQuery({
    queryKey: ["nursing-tasks", activeTab],
    queryFn: () => listTasks(activeTab === "all" ? undefined : activeTab),
  });

  // Fetch all tasks for stats (always unfiltered)
  const { data: allTasks } = useQuery({
    queryKey: ["nursing-tasks", "stats"],
    queryFn: () => listTasks(),
  });

  // Complete task mutation
  const completeMutation = useMutation({
    mutationFn: completeTask,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["nursing-tasks"], exact: false });
      queryClient.invalidateQueries({ queryKey: ["nursing-tasks", "stats"] });
      toast.success("Task completed successfully");
    },
    onError: () => {
      toast.error("Failed to complete task");
    },
  });

  // Start task mutation
  const startMutation = useMutation({
    mutationFn: startTask,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["nursing-tasks"], exact: false });
      queryClient.invalidateQueries({ queryKey: ["nursing-tasks", "stats"] });
      toast.success("Task started");
    },
    onError: () => {
      toast.error("Failed to start task");
    },
  });

  const handleComplete = (taskId: string) => {
    completeMutation.mutate(taskId);
  };

  const handleStart = (taskId: string) => {
    startMutation.mutate(taskId);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold">My Tasks</h2>
          <p className="text-sm text-muted-foreground">
            Manage your assigned nursing tasks and care activities
          </p>
        </div>
        <CreateTaskDialog />
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Tasks</CardTitle>
            <ClipboardList className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{allTasks?.length || 0}</div>
            <p className="text-xs text-muted-foreground">Assigned to you</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending</CardTitle>
            <Circle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {allTasks?.filter((t) => t.status === "pending").length || 0}
            </div>
            <p className="text-xs text-muted-foreground">Awaiting action</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">In Progress</CardTitle>
            <Clock className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {allTasks?.filter((t) => t.status === "in_progress").length || 0}
            </div>
            <p className="text-xs text-muted-foreground">Currently working</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {allTasks?.filter((t) => t.status === "completed").length || 0}
            </div>
            <p className="text-xs text-muted-foreground">Done today</p>
          </CardContent>
        </Card>
      </div>

      {/* Tasks List */}
      <Card>
        <CardHeader>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList>
              <TabsTrigger value="pending">Pending</TabsTrigger>
              <TabsTrigger value="in_progress">In Progress</TabsTrigger>
              <TabsTrigger value="completed">Completed</TabsTrigger>
              <TabsTrigger value="all">All Tasks</TabsTrigger>
            </TabsList>
          </Tabs>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8">
              <p className="text-sm text-muted-foreground">Loading tasks...</p>
            </div>
          ) : tasks && tasks.length > 0 ? (
            <div className="space-y-3">
              {tasks.map((task) => (
                <TaskCard
                  key={task.id}
                  task={task}
                  onStart={handleStart}
                  onComplete={handleComplete}
                  isLoading={
                    startMutation.isPending || completeMutation.isPending
                  }
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <ClipboardList className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
              <p className="text-sm text-muted-foreground">No tasks found</p>
              <p className="text-xs text-muted-foreground mt-1">
                Tasks assigned to you will appear here
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function TaskCard({
  task,
  onStart,
  onComplete,
  isLoading,
}: {
  task: NursingTask;
  onStart: (id: string) => void;
  onComplete: (id: string) => void;
  isLoading: boolean;
}) {
  return (
    <div className="flex items-start justify-between rounded-lg border p-4 hover:bg-muted/50 transition-colors">
      <div className="flex items-start gap-4">
        <div className="mt-1">{STATUS_ICONS[task.status]}</div>
        <div>
          <div className="flex items-center gap-2">
            <h4 className="font-medium">{task.title}</h4>
            <Badge
              variant="secondary"
              className={PRIORITY_COLORS[task.priority]}
            >
              {task.priority}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            {task.description || "No description"}
          </p>
          <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <User className="h-3 w-3" />
              {task.patient_name}
            </span>
            <span className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              {formatDueDate(task.due_date)}
            </span>
            <Badge variant="outline" className="text-xs">
              {TASK_TYPE_ICONS[task.task_type]}
              <span className="ml-1 capitalize">
                {task.task_type.replace("_", " ")}
              </span>
            </Badge>
          </div>
        </div>
      </div>
      <div className="flex items-center gap-2">
        {task.status === "pending" && (
          <Button
            size="sm"
            variant="outline"
            onClick={() => onStart(task.id)}
            disabled={isLoading}
          >
            Start
          </Button>
        )}
        {task.status === "in_progress" && (
          <Button
            size="sm"
            onClick={() => onComplete(task.id)}
            disabled={isLoading}
          >
            <CheckCircle2 className="mr-1 h-4 w-4" />
            Complete
          </Button>
        )}
        <Button size="sm" variant="ghost" asChild>
          <Link to={`/patients/${task.patient_id}`}>
            <ArrowRight className="h-4 w-4" />
          </Link>
        </Button>
      </div>
    </div>
  );
}
