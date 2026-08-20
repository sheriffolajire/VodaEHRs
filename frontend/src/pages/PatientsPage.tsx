import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Download, Search } from "lucide-react";
import { listPatients, registerPatient } from "@/services/patientService";
import { exportPatientsToCSV } from "@/services/exportService";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { showToast } from "@/lib/toast";

// Only these roles may register a patient (mirrors the backend rule).
const REGISTRAR_ROLES = ["Admin", "Receptionist"];

const registerSchema = z.object({
  first_name: z.string().min(1, "Required"),
  last_name: z.string().min(1, "Required"),
  dob: z.string().min(1, "Required"),
  gender: z.enum(["male", "female", "other", "unspecified"]),
  email: z.string().email("Invalid email").optional().or(z.literal("")),
  emergency_contact: z.string().min(1, "Required").optional().or(z.literal("")),
  phone: z.string().min(1, "Required").optional().or(z.literal("")),
  
});

type RegisterForm = z.infer<typeof registerSchema>;

export function PatientsPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  const canRegister = user != null && REGISTRAR_ROLES.includes(user.role.name);

  const patientsQuery = useQuery({
    queryKey: ["patients", search],
    queryFn: () => listPatients(search || undefined),
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: { gender: "unspecified" },
  });

  const registerMutation = useMutation({
    mutationFn: (data: RegisterForm) =>
      registerPatient({ ...data, email: data.email || null }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["patients"] });
      reset();
      setFormError(null);
      showToast.success("Patient registered", "New patient has been successfully registered");
    },
    onError: (error) => {
      const message = error instanceof Error ? error.message : "Failed";
      setFormError(message);
      showToast.error("Registration failed", message);
    },
  });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold">Patients</h2>
        <p className="text-sm text-muted-foreground">Register, search, and open patient records.</p>
      </div>

      {canRegister && (
        <div className="rounded-lg border bg-card p-6">
          <h3 className="mb-4 text-sm font-medium">Register patient</h3>
          <form
            onSubmit={handleSubmit((data) => registerMutation.mutate(data))}
            className="grid grid-cols-1 gap-3 sm:grid-cols-3"
          >
            <div>
              <input
                {...register("first_name")}
                placeholder="First name"
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
              />
              {errors.first_name && (
                <p className="mt-1 text-xs text-red-500">{errors.first_name.message}</p>
              )}
            </div>
            <div>
              <input
                {...register("last_name")}
                placeholder="Last name"
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
              />
              {errors.last_name && (
                <p className="mt-1 text-xs text-red-500">{errors.last_name.message}</p>
              )}
            </div>
            <div>
              <input
                type="date"
                {...register("dob")}
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
              />
              {errors.dob && <p className="mt-1 text-xs text-red-500">{errors.dob.message}</p>}
            </div>
            <div>
              <select
                {...register("gender")}
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
              >
                <option value="unspecified">Unspecified</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <input
                {...register("email")}
                placeholder="Email (optional)"
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
              />
              {errors.email && <p className="mt-1 text-xs text-red-500">{errors.email.message}</p>}
            </div>
            <div>
              <input
                {...register("emergency_contact")}
                placeholder="Emergency contact (optional)"
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
              />
              {errors.emergency_contact && (
                <p className="mt-1 text-xs text-red-500">{errors.emergency_contact.message}</p>
              )}
            </div>
            <div>
              <input
                {...register("phone")}
                placeholder="Phone (optional)"
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
              />
              {errors.phone && <p className="mt-1 text-xs text-red-500">{errors.phone.message}</p>}
            </div>
            <div className="flex items-end">
              <button
                type="submit"
                disabled={registerMutation.isPending}
                className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-60"
              >
                {registerMutation.isPending ? "Registering…" : "Register"}
              </button>
            </div>
          </form>
          {formError && <p className="mt-3 text-xs text-red-500">{formError}</p>}
        </div>
      )}

      <div className="rounded-lg border bg-card p-6">
        <div className="flex gap-2 mb-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search by name, hospital number, or email"
              className="w-full rounded-md border bg-background pl-10 pr-3 py-2 text-sm"
            />
          </div>
          <Button
            variant="outline"
            onClick={() => {
              if (patientsQuery.data) {
                exportPatientsToCSV(patientsQuery.data);
                showToast.success("Export complete", "Patient data exported to CSV");
              }
            }}
            disabled={!patientsQuery.data || patientsQuery.data.length === 0}
          >
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>
        </div>
        {patientsQuery.isLoading && <p className="text-sm text-muted-foreground">Loading…</p>}
        {patientsQuery.isError && <p className="text-sm text-red-500">Failed to load patients.</p>}
        {patientsQuery.data && patientsQuery.data.length === 0 && (
          <p className="text-sm text-muted-foreground">No patients found.</p>
        )}
        {patientsQuery.data && patientsQuery.data.length > 0 && (
          <table className="w-full text-left text-sm">
            <thead className="text-muted-foreground">
              <tr>
                <th className="pb-2">Hospital #</th>
                <th className="pb-2">Name</th>
                <th className="pb-2">DOB</th>
                <th className="pb-2"></th>
              </tr>
            </thead>
            <tbody>
              {patientsQuery.data.map((patient) => (
                <tr key={patient.id} className="border-t">
                  <td className="py-2">{patient.hospital_number}</td>
                  <td className="py-2">
                    {patient.first_name} {patient.last_name}
                  </td>
                  <td className="py-2">{patient.dob}</td>
                  <td className="py-2 text-right">
                    <button
                      type="button"
                      onClick={() => navigate(`/patients/${patient.id}`)}
                      className="rounded-md border px-2 py-1 text-xs hover:bg-muted"
                    >
                      Open
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
