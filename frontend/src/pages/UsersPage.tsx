import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createUser, listUsers, setUserStatus } from "@/services/userService";
import type { RoleName } from "@/types/auth";

const ROLES: RoleName[] = ["Admin", "Doctor", "Nurse", "Patient", "Receptionist", "Auditor"];

const createUserSchema = z.object({
  first_name: z.string().min(1, "Required"),
  last_name: z.string().min(1, "Required"),
  email: z.string().email("Enter a valid email"),
  // Mirrors the backend password policy so users get immediate feedback.
  password: z
    .string()
    .min(8, "At least 8 characters")
    .regex(/[A-Za-z]/, "Must contain a letter")
    .regex(/[0-9]/, "Must contain a number"),
  role: z.enum(["Admin", "Doctor", "Nurse", "Patient", "Receptionist", "Auditor"]),
});

type CreateUserForm = z.infer<typeof createUserSchema>;

export function UsersPage() {
  const queryClient = useQueryClient();
  const [formError, setFormError] = useState<string | null>(null);

  const usersQuery = useQuery({ queryKey: ["users"], queryFn: listUsers });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CreateUserForm>({
    resolver: zodResolver(createUserSchema),
    defaultValues: { role: "Doctor" },
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

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: "active" | "disabled" }) =>
      setUserStatus(id, status),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["users"] }),
  });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold">User Management</h2>
        <p className="text-sm text-muted-foreground">Create staff accounts and assign roles.</p>
      </div>

      <div className="rounded-lg border bg-card p-6">
        <h3 className="mb-4 text-sm font-medium">Create user</h3>
        <form
          onSubmit={handleSubmit((data) => createMutation.mutate(data))}
          className="grid grid-cols-1 gap-3 sm:grid-cols-2"
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
              {...register("email")}
              placeholder="Email"
              className="w-full rounded-md border bg-background px-3 py-2 text-sm"
            />
            {errors.email && <p className="mt-1 text-xs text-red-500">{errors.email.message}</p>}
          </div>
          <div>
            <input
              {...register("password")}
              type="password"
              placeholder="Temporary password"
              className="w-full rounded-md border bg-background px-3 py-2 text-sm"
            />
            {errors.password && (
              <p className="mt-1 text-xs text-red-500">{errors.password.message}</p>
            )}
          </div>
          <div>
            <select
              {...register("role")}
              className="w-full rounded-md border bg-background px-3 py-2 text-sm"
            >
              {ROLES.map((role) => (
                <option key={role} value={role}>
                  {role}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-60"
            >
              {createMutation.isPending ? "Creating…" : "Create user"}
            </button>
          </div>
        </form>
        {formError && <p className="mt-3 text-xs text-red-500">{formError}</p>}
      </div>

      <div className="rounded-lg border bg-card p-6">
        <h3 className="mb-4 text-sm font-medium">Users</h3>
        {usersQuery.isLoading && <p className="text-sm text-muted-foreground">Loading…</p>}
        {usersQuery.isError && <p className="text-sm text-red-500">Failed to load users.</p>}
        {usersQuery.data && (
          <table className="w-full text-left text-sm">
            <thead className="text-muted-foreground">
              <tr>
                <th className="pb-2">Name</th>
                <th className="pb-2">Email</th>
                <th className="pb-2">Role</th>
                <th className="pb-2">Status</th>
                <th className="pb-2"></th>
              </tr>
            </thead>
            <tbody>
              {usersQuery.data.map((user) => (
                <tr key={user.id} className="border-t">
                  <td className="py-2">
                    {user.first_name} {user.last_name}
                  </td>
                  <td className="py-2">{user.email}</td>
                  <td className="py-2">{user.role.name}</td>
                  <td className="py-2">{user.status}</td>
                  <td className="py-2 text-right">
                    <button
                      type="button"
                      onClick={() =>
                        statusMutation.mutate({
                          id: user.id,
                          status: user.status === "active" ? "disabled" : "active",
                        })
                      }
                      className="rounded-md border px-2 py-1 text-xs hover:bg-muted"
                    >
                      {user.status === "active" ? "Disable" : "Enable"}
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
