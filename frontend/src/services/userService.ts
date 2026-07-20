import { apiClient } from "@/services/apiClient";
import type { SuccessResponse } from "@/types/api";
import type { AuthUser, Role, RoleName, UserStatus } from "@/types/auth";

export interface CreateUserInput {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  role: RoleName;
}

export async function listUsers(): Promise<AuthUser[]> {
  const { data } = await apiClient.get<SuccessResponse<AuthUser[]>>("/users");
  return data.data;
}

export async function listRoles(): Promise<Role[]> {
  const { data } = await apiClient.get<SuccessResponse<Role[]>>("/roles");
  return data.data;
}

export async function createUser(input: CreateUserInput): Promise<AuthUser> {
  const { data } = await apiClient.post<SuccessResponse<AuthUser>>("/users", input);
  return data.data;
}

export async function setUserStatus(userId: string, status: UserStatus): Promise<AuthUser> {
  const { data } = await apiClient.patch<SuccessResponse<AuthUser>>(`/users/${userId}`, {
    status,
  });
  return data.data;
}
