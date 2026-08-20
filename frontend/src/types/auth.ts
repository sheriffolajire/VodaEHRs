/** Domain types for identity and access, mirroring the backend contract. */

export type RoleName = "Admin" | "Doctor" | "Nurse" | "Patient" | "Receptionist" | "Auditor";

export type UserStatus = "active" | "disabled";

export interface Role {
  id: string;
  name: RoleName;
}

export interface AuthUser {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  role: Role;
  status: UserStatus;
  created_at: string;
}

/** Response shape for the cookie-auth login endpoint. */
export interface LoginResponse {
  user: AuthUser;
}
