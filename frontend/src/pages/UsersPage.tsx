import { useState, useMemo } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { 
  createUser, 
  listUsers, 
  setUserStatus, 
  updateUser, 
  deleteUser,
  listAssignments,
  listAssignmentsForClinician,
  listAssignmentsForPatient,
  createAssignment,
  revokeAssignment,
  type Assignment 
} from "@/services/userService";
import { listPatients, type Patient } from "@/services/patientService";
import type { RoleName, AuthUser } from "@/types/auth";
import { 
  Users, 
  UserPlus, 
  Search, 
  Edit,
  Trash2,
  Power,
  PowerOff,
  UserCheck,
  Stethoscope,
  ChevronDown,
  ChevronUp,
  X,
  Filter,
  Briefcase,
  Calendar,
  Mail,
  Shield,
  MoreHorizontal,
  AlertTriangle,
  Info
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const ROLES: RoleName[] = ["Admin", "Doctor", "Nurse", "Patient", "Receptionist", "Auditor"];

const ROLE_COLORS: Record<RoleName, string> = {
  Admin: "bg-red-100 text-red-800 border-red-200",
  Doctor: "bg-blue-100 text-blue-800 border-blue-200",
  Nurse: "bg-green-100 text-green-800 border-green-200",
  Patient: "bg-purple-100 text-purple-800 border-purple-200",
  Receptionist: "bg-amber-100 text-amber-800 border-amber-200",
  Auditor: "bg-gray-100 text-gray-800 border-gray-200",
};

const ROLE_ICONS: Record<RoleName, React.ReactNode> = {
  Admin: <Shield className="h-3 w-3" />,
  Doctor: <Stethoscope className="h-3 w-3" />,
  Nurse: <UserCheck className="h-3 w-3" />,
  Patient: <Users className="h-3 w-3" />,
  Receptionist: <Briefcase className="h-3 w-3" />,
  Auditor: <Shield className="h-3 w-3" />,
};

const createUserSchema = z.object({
  first_name: z.string().min(1, "Required"),
  last_name: z.string().min(1, "Required"),
  email: z.string().email("Enter a valid email"),
  password: z
    .string()
    .min(8, "At least 8 characters")
    .regex(/[A-Za-z]/, "Must contain a letter")
    .regex(/[0-9]/, "Must contain a number"),
  role: z.enum(["Admin", "Doctor", "Nurse", "Patient", "Receptionist", "Auditor"]),
});

const updateUserSchema = z.object({
  first_name: z.string().min(1, "Required"),
  last_name: z.string().min(1, "Required"),
  email: z.string().email("Enter a valid email"),
  role: z.enum(["Admin", "Doctor", "Nurse", "Patient", "Receptionist", "Auditor"]),
});

type CreateUserForm = z.infer<typeof createUserSchema>;
type UpdateUserForm = z.infer<typeof updateUserSchema>;

// User Stats Component
function UserStats({ users }: { users: AuthUser[] }) {
  const stats = useMemo(() => {
    const byRole = ROLES.reduce((acc, role) => {
      acc[role] = users.filter(u => u.role.name === role).length;
      return acc;
    }, {} as Record<RoleName, number>);
    
    const active = users.filter(u => u.status === "active").length;
    const disabled = users.filter(u => u.status === "disabled").length;
    const clinicians = users.filter(u => u.role.name === "Doctor" || u.role.name === "Nurse").length;
    const patients = users.filter(u => u.role.name === "Patient").length;
    
    return { byRole, active, disabled, clinicians, patients, total: users.length };
  }, [users]);

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Total Users</p>
              <p className="text-2xl font-bold">{stats.total}</p>
            </div>
            <Users className="h-8 w-8 text-muted-foreground opacity-50" />
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Active</p>
              <p className="text-2xl font-bold text-green-600">{stats.active}</p>
            </div>
            <Power className="h-8 w-8 text-green-500 opacity-50" />
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Clinicians</p>
              <p className="text-2xl font-bold text-blue-600">{stats.clinicians}</p>
            </div>
            <Stethoscope className="h-8 w-8 text-blue-500 opacity-50" />
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Patients</p>
              <p className="text-2xl font-bold text-purple-600">{stats.patients}</p>
            </div>
            <UserCheck className="h-8 w-8 text-purple-500 opacity-50" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Clinician Assignments Panel
function ClinicianAssignments({ clinicianId }: { clinicianId: string }) {
  const assignmentsQuery = useQuery({
    queryKey: ["assignments", clinicianId],
    queryFn: () => listAssignmentsForClinician(clinicianId),
  });

  if (assignmentsQuery.isLoading) {
    return <div className="text-sm text-muted-foreground">Loading assignments...</div>;
  }

  if (assignmentsQuery.isError) {
    return <div className="text-sm text-red-500">Failed to load assignments</div>;
  }

  const assignments = assignmentsQuery.data || [];

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium flex items-center gap-2">
          <UserCheck className="h-4 w-4" />
          Assigned Patients ({assignments.length})
        </h4>
      </div>
      
      {assignments.length === 0 ? (
        <p className="text-sm text-muted-foreground">No patients assigned</p>
      ) : (
        <div className="space-y-2">
          {assignments.map((assignment: Assignment) => (
            <div key={assignment.id} className="flex items-center justify-between p-2 rounded-md border bg-muted/50">
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                  <Users className="h-4 w-4 text-primary" />
                </div>
                <div>
                  <p className="text-sm font-medium">Patient ID: {assignment.patient_id.slice(0, 8)}...</p>
                  <p className="text-xs text-muted-foreground">
                    Assigned {new Date(assignment.assigned_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
              <Badge variant="outline" className="text-xs">Active</Badge>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function UsersPage() {
  const queryClient = useQueryClient();
  const [formError, setFormError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState<RoleName | "all">("all");
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "disabled">("all");
  const [selectedUser, setSelectedUser] = useState<AuthUser | null>(null);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("all");
  
  // Assignment management state
  const [isAssignmentDialogOpen, setIsAssignmentDialogOpen] = useState(false);
  const [selectedClinicianForAssignment, setSelectedClinicianForAssignment] = useState<AuthUser | null>(null);
  const [selectedPatientForAssignment, setSelectedPatientForAssignment] = useState<string>("");

  const usersQuery = useQuery({ queryKey: ["users"], queryFn: listUsers });
  const patientsQuery = useQuery({ queryKey: ["patients"], queryFn: listPatients });
  const assignmentsQuery = useQuery({ queryKey: ["assignments"], queryFn: listAssignments });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CreateUserForm>({
    resolver: zodResolver(createUserSchema),
    defaultValues: { role: "Doctor" },
  });

  const editForm = useForm<UpdateUserForm>({
    resolver: zodResolver(updateUserSchema),
  });

  const createMutation = useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      reset();
      setFormError(null);
    },
    onError: (error) => setFormError(error instanceof Error ? error.message : "Create failed"),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateUserForm }) => updateUser(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      setIsEditDialogOpen(false);
      setSelectedUser(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      setIsDeleteDialogOpen(false);
      setSelectedUser(null);
    },
  });

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: "active" | "disabled" }) =>
      setUserStatus(id, status),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["users"] }),
  });

  // Assignment mutations
  const createAssignmentMutation = useMutation({
    mutationFn: ({ patientId, clinicianId }: { patientId: string; clinicianId: string }) =>
      createAssignment(patientId, clinicianId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assignments"] });
      setIsAssignmentDialogOpen(false);
      setSelectedClinicianForAssignment(null);
      setSelectedPatientForAssignment("");
    },
  });

  const revokeAssignmentMutation = useMutation({
    mutationFn: revokeAssignment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assignments"] });
    },
  });

  // Filter users based on search and filters
  const filteredUsers = useMemo(() => {
    if (!usersQuery.data) return [];
    
    return usersQuery.data.filter((user) => {
      const matchesSearch = 
        searchQuery === "" ||
        user.first_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        user.last_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        user.email.toLowerCase().includes(searchQuery.toLowerCase());
      
      const matchesRole = roleFilter === "all" || user.role.name === roleFilter;
      const matchesStatus = statusFilter === "all" || user.status === statusFilter;
      const matchesTab = activeTab === "all" || user.role.name.toLowerCase() === activeTab;
      
      return matchesSearch && matchesRole && matchesStatus && matchesTab;
    });
  }, [usersQuery.data, searchQuery, roleFilter, statusFilter, activeTab]);

  // Group users by role for the tabs
  const usersByRole = useMemo(() => {
    if (!usersQuery.data) return {};
    return ROLES.reduce((acc, role) => {
      acc[role] = usersQuery.data.filter(u => u.role.name === role);
      return acc;
    }, {} as Record<RoleName, AuthUser[]>);
  }, [usersQuery.data]);

  const openEditDialog = (user: AuthUser) => {
    setSelectedUser(user);
    editForm.reset({
      first_name: user.first_name,
      last_name: user.last_name,
      email: user.email,
      role: user.role.name,
    });
    setIsEditDialogOpen(true);
  };

  const openDeleteDialog = (user: AuthUser) => {
    setSelectedUser(user);
    setIsDeleteDialogOpen(true);
  };

  const openDetailPanel = (user: AuthUser) => {
    setSelectedUser(user);
    setIsDetailOpen(true);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold">User Management</h2>
          <p className="text-sm text-muted-foreground">
            Manage users, roles, and patient assignments
          </p>
        </div>
        <Button onClick={() => document.getElementById('create-user-section')?.scrollIntoView({ behavior: 'smooth' })}>
          <UserPlus className="h-4 w-4 mr-2" />
          Create User
        </Button>
      </div>

      {/* Stats */}
      {usersQuery.data && <UserStats users={usersQuery.data} />}

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search users by name or email..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex gap-2">
              <Select value={roleFilter} onValueChange={(v) => setRoleFilter(v as RoleName | "all")}>
                <SelectTrigger className="w-[140px]">
                  <Filter className="h-4 w-4 mr-2" />
                  <SelectValue placeholder="Role" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Roles</SelectItem>
                  {ROLES.map((role) => (
                    <SelectItem key={role} value={role}>{role}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as "all" | "active" | "disabled")}>
                <SelectTrigger className="w-[140px]">
                  <Power className="h-4 w-4 mr-2" />
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="disabled">Disabled</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Users Table with Tabs */}
      <Card>
        <CardHeader className="pb-0">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid grid-cols-7">
              <TabsTrigger value="all">All</TabsTrigger>
              <TabsTrigger value="admin">Admin</TabsTrigger>
              <TabsTrigger value="doctor">Doctors</TabsTrigger>
              <TabsTrigger value="nurse">Nurses</TabsTrigger>
              <TabsTrigger value="patient">Patients</TabsTrigger>
              <TabsTrigger value="receptionist">Reception</TabsTrigger>
              <TabsTrigger value="auditor">Auditors</TabsTrigger>
            </TabsList>
          </Tabs>
        </CardHeader>
        <CardContent className="p-6">
          {usersQuery.isLoading && (
            <div className="flex items-center justify-center py-8">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            </div>
          )}
          
          {usersQuery.isError && (
            <Alert variant="destructive">
              <AlertDescription>Failed to load users.</AlertDescription>
            </Alert>
          )}

          {usersQuery.data && (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredUsers.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                        No users found matching your filters
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredUsers.map((user) => (
                      <TableRow key={user.id} className="cursor-pointer hover:bg-muted/50" onClick={() => openDetailPanel(user)}>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                              {user.first_name[0]}{user.last_name[0]}
                            </div>
                            <div>
                              <p className="font-medium">{user.first_name} {user.last_name}</p>
                              <p className="text-xs text-muted-foreground">ID: {user.id.slice(0, 8)}...</p>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>{user.email}</TableCell>
                        <TableCell>
                          <Badge className={ROLE_COLORS[user.role.name]}>
                            {ROLE_ICONS[user.role.name]}
                            <span className="ml-1">{user.role.name}</span>
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={user.status === "active" ? "default" : "secondary"}>
                            {user.status === "active" ? (
                              <><Power className="h-3 w-3 mr-1" /> Active</>
                            ) : (
                              <><PowerOff className="h-3 w-3 mr-1" /> Disabled</>
                            )}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end gap-1" onClick={(e) => e.stopPropagation()}>
                            {(user.role.name === "Doctor" || user.role.name === "Nurse") && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => {
                                  setSelectedClinicianForAssignment(user);
                                  setIsAssignmentDialogOpen(true);
                                }}
                                title="Assign patients"
                              >
                                <UserPlus className="h-4 w-4 text-blue-500" />
                              </Button>
                            )}
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => openEditDialog(user)}
                              title="Edit user"
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() =>
                                statusMutation.mutate({
                                  id: user.id,
                                  status: user.status === "active" ? "disabled" : "active",
                                })
                              }
                              title={user.status === "active" ? "Disable user" : "Enable user"}
                            >
                              {user.status === "active" ? (
                                <PowerOff className="h-4 w-4 text-amber-500" />
                              ) : (
                                <Power className="h-4 w-4 text-green-500" />
                              )}
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => openDeleteDialog(user)}
                              title="Disable user"
                            >
                              <Trash2 className="h-4 w-4 text-red-500" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create User Section */}
      <Card id="create-user-section">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <UserPlus className="h-5 w-5" />
            Create New User
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={handleSubmit((data) => createMutation.mutate(data))}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
          >
            <div>
              <label className="text-sm font-medium mb-1 block">First Name</label>
              <Input {...register("first_name")} placeholder="Enter first name" />
              {errors.first_name && (
                <p className="mt-1 text-xs text-red-500">{errors.first_name.message}</p>
              )}
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Last Name</label>
              <Input {...register("last_name")} placeholder="Enter last name" />
              {errors.last_name && (
                <p className="mt-1 text-xs text-red-500">{errors.last_name.message}</p>
              )}
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Email</label>
              <Input {...register("email")} type="email" placeholder="Enter email" />
              {errors.email && <p className="mt-1 text-xs text-red-500">{errors.email.message}</p>}
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Password</label>
              <Input {...register("password")} type="password" placeholder="Min 8 chars, letter + number" />
              {errors.password && (
                <p className="mt-1 text-xs text-red-500">{errors.password.message}</p>
              )}
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Role</label>
              <Select onValueChange={(v) => register("role").onChange({ target: { value: v } })} defaultValue="Doctor">
                <SelectTrigger>
                  <SelectValue placeholder="Select role" />
                </SelectTrigger>
                <SelectContent>
                  {ROLES.map((role) => (
                    <SelectItem key={role} value={role}>{role}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end">
              <Button 
                type="submit" 
                disabled={createMutation.isPending}
                className="w-full"
              >
                {createMutation.isPending ? "Creating..." : "Create User"}
              </Button>
            </div>
          </form>
          {formError && (
            <Alert variant="destructive" className="mt-4">
              <AlertDescription>{formError}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Edit User Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Edit User</DialogTitle>
            <DialogDescription>Update user information</DialogDescription>
          </DialogHeader>
          <form onSubmit={editForm.handleSubmit((data) => {
            if (selectedUser) {
              updateMutation.mutate({ id: selectedUser.id, data });
            }
          })}>
            <div className="space-y-4 py-4">
              <div>
                <label className="text-sm font-medium mb-1 block">First Name</label>
                <Input {...editForm.register("first_name")} />
              </div>
              <div>
                <label className="text-sm font-medium mb-1 block">Last Name</label>
                <Input {...editForm.register("last_name")} />
              </div>
              <div>
                <label className="text-sm font-medium mb-1 block">Email</label>
                <Input {...editForm.register("email")} type="email" />
              </div>
              <div>
                <label className="text-sm font-medium mb-1 block">Role</label>
                <Select 
                  onValueChange={(v) => editForm.setValue("role", v as RoleName)}
                  defaultValue={editForm.getValues("role")}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select role" />
                  </SelectTrigger>
                  <SelectContent>
                    {ROLES.map((role) => (
                      <SelectItem key={role} value={role}>{role}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsEditDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={updateMutation.isPending}>
                {updateMutation.isPending ? "Saving..." : "Save Changes"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Disable User Dialog */}
      <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="text-amber-600 flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" />
              Disable User
            </DialogTitle>
            <DialogDescription>
              This will disable the user account. The user will no longer be able to log in.
            </DialogDescription>
          </DialogHeader>
          {selectedUser && (
            <div className="py-4 space-y-2">
              <p className="text-sm">
                <strong>Name:</strong> {selectedUser.first_name} {selectedUser.last_name}
              </p>
              <p className="text-sm">
                <strong>Email:</strong> {selectedUser.email}
              </p>
              <p className="text-sm">
                <strong>Role:</strong> {selectedUser.role.name}
              </p>
              <div className="flex items-start gap-2 mt-4 p-3 bg-blue-50 rounded-md">
                <Info className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-blue-700">
                  <strong>Note:</strong> Users are soft-disabled for audit trail purposes. 
                  Their data remains in the system but they cannot access the platform.
                </p>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              variant="destructive" 
              onClick={() => selectedUser && deleteMutation.mutate(selectedUser.id)}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? "Disabling..." : "Disable User"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* User Detail Panel */}
      <Dialog open={isDetailOpen} onOpenChange={setIsDetailOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>User Details</DialogTitle>
          </DialogHeader>
          {selectedUser && (
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center text-xl font-bold">
                  {selectedUser.first_name[0]}{selectedUser.last_name[0]}
                </div>
                <div>
                  <h3 className="text-lg font-semibold">
                    {selectedUser.first_name} {selectedUser.last_name}
                  </h3>
                  <p className="text-sm text-muted-foreground flex items-center gap-1">
                    <Mail className="h-3 w-3" />
                    {selectedUser.email}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge className={ROLE_COLORS[selectedUser.role.name]}>
                      {selectedUser.role.name}
                    </Badge>
                    <Badge variant={selectedUser.status === "active" ? "default" : "secondary"}>
                      {selectedUser.status}
                    </Badge>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">User ID</p>
                  <p className="font-mono">{selectedUser.id}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Created</p>
                  <p>{new Date(selectedUser.created_at).toLocaleDateString()}</p>
                </div>
              </div>

              {/* Show assignments for clinicians */}
              {(selectedUser.role.name === "Doctor" || selectedUser.role.name === "Nurse") && (
                <ClinicianAssignments clinicianId={selectedUser.id} />
              )}

              <DialogFooter className="gap-2">
                <Button variant="outline" onClick={() => setIsDetailOpen(false)}>
                  Close
                </Button>
                <Button onClick={() => {
                  setIsDetailOpen(false);
                  openEditDialog(selectedUser);
                }}>
                  <Edit className="h-4 w-4 mr-2" />
                  Edit User
                </Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Assignment Management Dialog */}
      <Dialog open={isAssignmentDialogOpen} onOpenChange={setIsAssignmentDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <UserPlus className="h-5 w-5" />
              Assign Patients to Clinician
            </DialogTitle>
            <DialogDescription>
              {selectedClinicianForAssignment && (
                <>Assign patients to {selectedClinicianForAssignment.first_name} {selectedClinicianForAssignment.last_name}</>
              )}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            {/* Current Assignments */}
            {selectedClinicianForAssignment && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium">Current Assignments</h4>
                <div className="max-h-32 overflow-y-auto space-y-1">
                  {assignmentsQuery.data?.filter((a: Assignment) => a.clinician_id === selectedClinicianForAssignment.id).length === 0 ? (
                    <p className="text-sm text-muted-foreground">No patients assigned</p>
                  ) : (
                    assignmentsQuery.data
                      ?.filter((a: Assignment) => a.clinician_id === selectedClinicianForAssignment.id)
                      .map((assignment: Assignment) => {
                        const patient = patientsQuery.data?.find((p: Patient) => p.id === assignment.patient_id);
                        return (
                          <div key={assignment.id} className="flex items-center justify-between p-2 rounded-md border bg-muted/50">
                            <div className="flex items-center gap-2">
                              <div className="h-6 w-6 rounded-full bg-primary/10 flex items-center justify-center text-xs">
                                {patient?.first_name?.[0] || "P"}
                              </div>
                              <div>
                                <p className="text-sm font-medium">
                                  {patient ? `${patient.first_name} ${patient.last_name}` : `Patient ${assignment.patient_id.slice(0, 8)}...`}
                                </p>
                                <p className="text-xs text-muted-foreground">
                                  Assigned {new Date(assignment.assigned_at).toLocaleDateString()}
                                </p>
                              </div>
                            </div>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => revokeAssignmentMutation.mutate(assignment.id)}
                              disabled={revokeAssignmentMutation.isPending}
                            >
                              <X className="h-4 w-4 text-red-500" />
                            </Button>
                          </div>
                        );
                      })
                  )}
                </div>
              </div>
            )}

            {/* Assign New Patient */}
            <div className="space-y-2 pt-4 border-t">
              <h4 className="text-sm font-medium">Assign New Patient</h4>
              <Select 
                value={selectedPatientForAssignment} 
                onValueChange={setSelectedPatientForAssignment}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a patient to assign" />
                </SelectTrigger>
                <SelectContent>
                  {patientsQuery.data?.map((patient: Patient) => {
                    // Check if already assigned
                    const isAssigned = assignmentsQuery.data?.some(
                      (a: Assignment) => 
                        a.patient_id === patient.id && 
                        a.clinician_id === selectedClinicianForAssignment?.id
                    );
                    return (
                      <SelectItem 
                        key={patient.id} 
                        value={patient.id}
                        disabled={isAssigned}
                      >
                        {patient.first_name} {patient.last_name} {isAssigned && "(Already assigned)"}
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setIsAssignmentDialogOpen(false);
              setSelectedClinicianForAssignment(null);
              setSelectedPatientForAssignment("");
            }}>
              Cancel
            </Button>
            <Button 
              onClick={() => {
                if (selectedClinicianForAssignment && selectedPatientForAssignment) {
                  createAssignmentMutation.mutate({
                    patientId: selectedPatientForAssignment,
                    clinicianId: selectedClinicianForAssignment.id,
                  });
                }
              }}
              disabled={!selectedPatientForAssignment || createAssignmentMutation.isPending}
            >
              {createAssignmentMutation.isPending ? "Assigning..." : "Assign Patient"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
