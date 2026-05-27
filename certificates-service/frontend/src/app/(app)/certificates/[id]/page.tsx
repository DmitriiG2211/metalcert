"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api, { getErrorMessage } from "@/lib/api";
import Header from "@/components/layout/Header";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ConfidenceBar } from "@/components/ui/ConfidenceBar";
import { Certificate } from "@/types";

function Field({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div>
      <div className="text-xs text-slate-500 mb-0.5">{label}</div>
      <div className="text-slate-200 text-sm">{value || "—"}</div>
    </div>
  );
}

export default function CertificateDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const qc = useQueryClient();
  const [showText, setShowText] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(false);

  const { data: cert, isLoading } = useQuery<Certificate>({
    queryKey: ["certificate", id],
    queryFn: () => api.get(`/certificates/${id}`).then((r) => r.data),
  });

  const reprocess = useMutation({
    mutationFn: () => api.post(`/certificates/${id}/reprocess`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["certificate", id] }),
  });

  const deleteCert = useMutation({
    mutationFn: () => api.delete(`/certificates/${id}`),
    onSuccess: () => router.push("/certificates"),
  });

  if (isLoading) return (
    <div className="flex-1 overflow-auto">
      <Header title="Сертификат" />
      <div className="p-6 text-slate-400">Загрузка...</div>
    </div>
  );

  if (!cert) return (
    <div className="flex-1 overflow-auto">
      <Header title="Сертификат" />
      <div className="p-6 text-red-400">Сертификат не найден</div>
    </div>
  );

  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const fileUrl = `${apiBase}/api/v1/certificates/${id}/file`;
  const previewUrl = cert.preview_path
    ? `${apiBase}/uploads/previews/${cert.preview_path.split(/[/\\]/).pop()}`
    : null;

  return (
    <div className="flex-1 overflow-auto">
      <Header title="Сертификат" />
      <div className="p-6 space-y-4">
        {/* Breadcrumb + actions */}
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-2 text-sm">
            <Link href="/certificates" className="text-slate-400 hover:text-slate-200">Сертификаты</Link>
            <span className="text-slate-600">/</span>
            <span className="text-slate-200">{cert.original_filename}</span>
          </div>
          <div className="flex gap-2">
            <Link
              href={`/certificates/${id}/edit`}
              className="px-3 py-1.5 bg-slate-800 border border-slate-600 text-slate-300 hover:bg-slate-700 rounded-lg text-sm transition-colors"
            >
              Редактировать
            </Link>
            <button
              onClick={() => reprocess.mutate()}
              disabled={reprocess.isPending}
              className="px-3 py-1.5 bg-slate-800 border border-slate-600 text-slate-300 hover:bg-slate-700 rounded-lg text-sm transition-colors disabled:opacity-50"
            >
              {reprocess.isPending ? "..." : "Переобработать"}
            </button>
            <a
              href={fileUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-1.5 bg-slate-800 border border-slate-600 text-slate-300 hover:bg-slate-700 rounded-lg text-sm transition-colors"
            >
              Скачать ↓
            </a>
            {!deleteConfirm ? (
              <button
                onClick={() => setDeleteConfirm(true)}
                className="px-3 py-1.5 bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500/20 rounded-lg text-sm transition-colors"
              >
                Удалить
              </button>
            ) : (
              <div className="flex gap-1">
                <button
                  onClick={() => deleteCert.mutate()}
                  className="px-3 py-1.5 bg-red-600 text-white rounded-lg text-sm"
                >
                  Подтвердить
                </button>
                <button
                  onClick={() => setDeleteConfirm(false)}
                  className="px-3 py-1.5 bg-slate-800 text-slate-300 rounded-lg text-sm"
                >
                  Отмена
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Preview */}
          <div className="bg-slate-900 border border-slate-700/50 rounded-xl overflow-hidden">
            <div className="p-4 border-b border-slate-700/50 flex items-center justify-between">
              <span className="text-slate-300 font-medium text-sm">Предпросмотр</span>
              <StatusBadge status={cert.status} />
            </div>
            <div className="p-4 flex items-center justify-center min-h-[300px] bg-slate-950/50">
              {previewUrl ? (
                <img
                  src={previewUrl}
                  alt="Preview"
                  className="max-w-full max-h-[500px] object-contain rounded"
                />
              ) : (
                <div className="text-slate-500 text-sm text-center">
                  <svg className="w-12 h-12 mx-auto mb-2 text-slate-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Предпросмотр недоступен
                </div>
              )}
            </div>
          </div>

          {/* Data */}
          <div className="bg-slate-900 border border-slate-700/50 rounded-xl">
            <div className="p-4 border-b border-slate-700/50">
              <span className="text-slate-300 font-medium text-sm">Данные сертификата</span>
            </div>
            <div className="p-4 space-y-4">
              {cert.ocr_confidence !== null && (
                <div>
                  <div className="text-xs text-slate-500 mb-1">Точность OCR</div>
                  <ConfidenceBar value={cert.ocr_confidence} />
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <Field label="Номер сертификата" value={cert.certificate_number} />
                <Field label="Дата сертификата" value={cert.certificate_date ? new Date(cert.certificate_date).toLocaleDateString("ru-RU") : null} />
                <Field label="Тип продукции" value={cert.product_type} />
                <Field label="Размер" value={cert.dimensions} />
                <Field label="Марка стали" value={cert.material} />
                <Field label="ГОСТ / ТУ" value={cert.gost} />
                <Field label="Производитель" value={cert.manufacturer} />
                <Field label="Поставщик" value={cert.supplier} />
                <Field label="Номер партии" value={cert.batch_number} />
                <Field label="Номер плавки" value={cert.heat_number} />
              </div>

              {cert.normalized_product_name && (
                <div className="pt-2 border-t border-slate-700/50">
                  <div className="text-xs text-slate-500 mb-1">Полное наименование</div>
                  <div className="text-slate-100 font-medium text-sm">{cert.normalized_product_name}</div>
                </div>
              )}

              <div className="pt-2 border-t border-slate-700/50 text-xs text-slate-500 space-y-0.5">
                <div>Файл: {cert.original_filename}</div>
                <div>Загружен: {new Date(cert.created_at).toLocaleString("ru-RU")}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Extracted text */}
        {cert.extracted_text && (
          <div className="bg-slate-900 border border-slate-700/50 rounded-xl">
            <button
              onClick={() => setShowText(!showText)}
              className="w-full p-4 text-left flex items-center justify-between text-slate-300 text-sm font-medium"
            >
              Распознанный текст
              <svg
                className={`w-4 h-4 transition-transform ${showText ? "rotate-180" : ""}`}
                fill="none" viewBox="0 0 24 24" stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            {showText && (
              <div className="px-4 pb-4">
                <pre className="text-slate-400 text-xs whitespace-pre-wrap font-mono bg-slate-950/50 rounded-lg p-4 max-h-64 overflow-y-auto">
                  {cert.extracted_text}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
