export enum CertificateStatus {
  UPLOADED = "uploaded",
  PROCESSING = "processing",
  PARSED = "parsed",
  NEEDS_REVIEW = "needs_review",
  FAILED = "failed",
}

export enum UserRole {
  ADMIN = "admin",
  MANAGER = "manager",
  VIEWER = "viewer",
}

export interface Certificate {
  id: number;
  original_filename: string;
  file_path: string;
  preview_path: string | null;
  file_type: string;
  ocr_confidence: number | null;
  certificate_number: string | null;
  certificate_date: string | null;
  manufacturer: string | null;
  supplier: string | null;
  product_name: string | null;
  normalized_product_name: string | null;
  product_type: string | null;
  material: string | null;
  gost: string | null;
  dimensions: string | null;
  batch_number: string | null;
  heat_number: string | null;
  status: CertificateStatus;
  extracted_text: string | null;
  raw_data: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  created_by: number | null;
}

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface SearchParams {
  query?: string;
  product_type?: string;
  material?: string;
  gost?: string;
  status?: CertificateStatus;
  manufacturer?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface DashboardStats {
  total_certificates: number;
  parsed_count: number;
  needs_review_count: number;
  failed_count: number;
  processing_count: number;
  uploaded_count: number;
  by_product_type: Record<string, number>;
  by_manufacturer: Array<{ name: string; count: number }>;
  recent_uploads: Certificate[];
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface CertificateUpdateRequest {
  certificate_number?: string | null;
  certificate_date?: string | null;
  manufacturer?: string | null;
  supplier?: string | null;
  product_name?: string | null;
  normalized_product_name?: string | null;
  product_type?: string | null;
  material?: string | null;
  gost?: string | null;
  dimensions?: string | null;
  batch_number?: string | null;
  heat_number?: string | null;
  status?: CertificateStatus;
}

export interface UploadedFile {
  id: string;
  file: File;
  status: "pending" | "uploading" | "processing" | "done" | "error";
  progress: number;
  certificateId?: number;
  error?: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface ApiError {
  detail: string | Array<{ loc: string[]; msg: string; type: string }>;
}
