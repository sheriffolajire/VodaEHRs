/**
 * Create Task Dialog
 * 
 * Dialog for creating new nursing tasks.
 */
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Calendar, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import { createTask } from "@/services/nursingTaskService";
import { listPatients, type Patient } from "@/services/patientService";

const TASK_TYPES = [
  { value: "vitals", label: "Vitals Check" },
  { value: "medication", label: "Medication" },
  { value: "wound_care", label: "Wound Care" },
  { value: "patient_education", label: "Patient Education" },
  { value: "assessment", label: "Assessment" },
  { value: "documentation", label: "Documentation" },
  { value: "other", label: "Other" },
];

const PRIORITIES = [
  { value: "low", label: "Low" },
  { value: "normal", label: "Normal" },
  { value: "high", label: "High" },
  { value: "urgent", label: "Urgent" },
];

export function CreateTaskDialog() {
  const [open, setOpen] = useState(false);
  const queryClient = useQueryClient();
  
  const [formData, setFormData] = useState({
    patient_id: "",
    title: "",
    description: "",
    task_type: "",
    priority: "normal",
    due_date: "",
  });

  // Fetch patients for dropdown
  const { data: patients, isLoading: patientsLoading } = useQuery<Patient[]>({
    queryKey: ["patients"],
    queryFn: () => listPatients(),
    enabled: open,
  });

  const createMutation = useMutation({
    mutationFn: createTask,
    onSuccess: () => {
      toast.success("Task created successfully");
      queryClient.invalidateQueries({ queryKey: ["nursing-tasks"] });
      setOpen(false);
      setFormData({
        patient_id: "",
        title: "",
        description: "",
        task_type: "",
        priority: "normal",
        due_date: "",
      });
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to create task");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.patient_id || !formData.title || !formData.task_type) {
      toast.error("Please fill in all required fields");
      return;
    }

    createMutation.mutate({
      patient_id: formData.patient_id,
      title: formData.title,
      description: formData.description || undefined,
      task_type: formData.task_type,
      priority: formData.priority,
      due_date: formData.due_date ? new Date(formData.due_date) : undefined,
    });
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Create Task
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Create New Task</DialogTitle>
          <DialogDescription>
            Create a new nursing task for a patient. All fields marked with * are required.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Patient Selection */}
          <div className="space-y-2">
            <Label htmlFor="patient">
              <User className="mr-1 inline h-4 w-4" />
              Patient *
            </Label>
            <Select
              value={formData.patient_id}
              onValueChange={(value) =>
                setFormData((prev) => ({ ...prev, patient_id: value }))
              }
              disabled={patientsLoading}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a patient" />
              </SelectTrigger>
              <SelectContent>
                {patients?.map((patient) => (
                  <SelectItem key={patient.id} value={patient.id}>
                    {patient.first_name} {patient.last_name} ({patient.hospital_number})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Task Title */}
          <div className="space-y-2">
            <Label htmlFor="title">Task Title *</Label>
            <Input
              id="title"
              value={formData.title}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, title: e.target.value }))
              }
              placeholder="e.g., Morning vitals check"
              required
            />
          </div>

          {/* Task Type */}
          <div className="space-y-2">
            <Label htmlFor="task_type">Task Type *</Label>
            <Select
              value={formData.task_type}
              onValueChange={(value) =>
                setFormData((prev) => ({ ...prev, task_type: value }))
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Select task type" />
              </SelectTrigger>
              <SelectContent>
                {TASK_TYPES.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Priority */}
          <div className="space-y-2">
            <Label htmlFor="priority">Priority</Label>
            <Select
              value={formData.priority}
              onValueChange={(value) =>
                setFormData((prev) => ({ ...prev, priority: value }))
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {PRIORITIES.map((priority) => (
                  <SelectItem key={priority.value} value={priority.value}>
                    {priority.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Due Date */}
          <div className="space-y-2">
            <Label htmlFor="due_date">
              <Calendar className="mr-1 inline h-4 w-4" />
              Due Date
            </Label>
            <Input
              id="due_date"
              type="datetime-local"
              value={formData.due_date}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, due_date: e.target.value }))
              }
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, description: e.target.value }))
              }
              placeholder="Additional details about the task..."
              rows={3}
            />
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
              disabled={createMutation.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? "Creating..." : "Create Task"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
