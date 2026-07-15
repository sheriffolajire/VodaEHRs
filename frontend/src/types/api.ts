/** API response envelope shared with the backend contract. */
export interface SuccessResponse<T> {
  success: true;
  message: string;
  data: T;
}

export interface ErrorDetail {
  field?: string;
  message: string;
}

export interface ErrorResponse {
  success: false;
  message: string;
  errors: ErrorDetail[];
}

export interface HealthData {
  status: string;
  environment: string;
}
