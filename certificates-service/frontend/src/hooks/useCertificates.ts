"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import {
  Certificate,
  PaginatedResponse,
  SearchParams,
  CertificateUpdateRequest,
  DashboardStats,
} from "@/types";

export const certificateKeys = {
  all: ["certificates"] as const,
  lists: () => [...certificateKeys.all, "list"] as const,
  list: (params: SearchParams) =>
    [...certificateKeys.lists(), params] as const,
  details: () => [...certificateKeys.all, "detail"] as const,
  detail: (id: number) => [...certificateKeys.details(), id] as const,
  stats: () => [...certificateKeys.all, "stats"] as const,
  search: (q: string) => [...certificateKeys.all, "search", q] as const,
};

export function useCertificates(params: SearchParams = {}) {
  return useQuery({
    queryKey: certificateKeys.list(params),
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<Certificate>>(
        "/certificates",
        { params }
      );
      return data;
    },
    staleTime: 30_000,
  });
}

export function useCertificate(id: number) {
  return useQuery({
    queryKey: certificateKeys.detail(id),
    queryFn: async () => {
      const { data } = await api.get<Certificate>(`/certificates/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useDashboardStats() {
  return useQuery({
    queryKey: certificateKeys.stats(),
    queryFn: async () => {
      const { data } = await api.get<DashboardStats>("/certificates/stats");
      return data;
    },
    staleTime: 60_000,
  });
}

export function useSearchCertificates(params: SearchParams) {
  return useQuery({
    queryKey: certificateKeys.list(params),
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<Certificate>>(
        "/certificates/search",
        { params }
      );
      return data;
    },
    enabled: !!(params.query || params.product_type || params.material || params.gost || params.status || params.manufacturer),
    staleTime: 15_000,
  });
}

export function useUploadCertificate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      file,
      onUploadProgress,
    }: {
      file: File;
      onUploadProgress?: (progress: number) => void;
    }) => {
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await api.post<Certificate>(
        "/certificates/upload",
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
          onUploadProgress: (evt) => {
            if (evt.total) {
              onUploadProgress?.(Math.round((evt.loaded / evt.total) * 100));
            }
          },
        }
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: certificateKeys.all });
    },
  });
}

export function useUpdateCertificate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      data,
    }: {
      id: number;
      data: CertificateUpdateRequest;
    }) => {
      const { data: updated } = await api.patch<Certificate>(
        `/certificates/${id}`,
        data
      );
      return updated;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: certificateKeys.detail(variables.id),
      });
      queryClient.invalidateQueries({ queryKey: certificateKeys.lists() });
    },
  });
}

export function useDeleteCertificate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/certificates/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: certificateKeys.all });
    },
  });
}

export function useReprocessCertificate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.post<Certificate>(
        `/certificates/${id}/reprocess`
      );
      return data;
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: certificateKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: certificateKeys.lists() });
    },
  });
}

export function usePollCertificateStatus(
  id: number | null,
  enabled: boolean = false
) {
  return useQuery({
    queryKey: certificateKeys.detail(id ?? 0),
    queryFn: async () => {
      const { data } = await api.get<Certificate>(`/certificates/${id}`);
      return data;
    },
    enabled: !!id && enabled,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (
        data?.status === "processing" ||
        data?.status === "uploaded"
      ) {
        return 3000;
      }
      return false;
    },
  });
}
