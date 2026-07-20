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

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginResponse extends TokenPair {
  user: AuthUser;
}
