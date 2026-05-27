"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import Header from "@/components/layout/Header";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Certificate, CertificateStatus, PaginatedResponse } from "@/types";

const STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: "", label: "Все статусы" },
  { value: "parsed", label: "Распознан" },
  { value: "needs_review", label: "Требует проверки" },
  { value: "processing", label: "Обработка" },
  { value: "failed", label: "Ошибка" },
  { value: "uploaded", label: "Загружен" },
];

export default function CertificatesPage() {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("");
  const [productTypeFilter, setProductTypeFilter] = useState("");
  const [materialFilter, setMaterialFilter] = useState("");
  const [sortDesc, setSortDesc] = useState(true);

  const { data, isLoading } = useQuery<PaginatedResponse<Certificate>>({
    queryKey: ["certificates", page, statusFilter, productTypeFilter, materialFilter, sortDesc],
    queryFn: () =>
      api
        .get("/certificates", {
          params: {
            page,
            page_size: 20,
            ...(statusFilter && { status: statusFilter }),
            ...(productTypeFilter && { product_type: productTypeFilter }),
            ...(materialFilter && { material: materialFilter }),
            sort_desc: sortDesc,
          },
        })
        .then((r) => r.data),
  });

  const handleExport = async () => {
    const res = await api.get("/export/excel", {
      responseType: "blob",
      params: {
        ...(statusFilter && { status: statusFilter }),
        ...(productTypeFilter && { product_type: productTypeFilter }),
        ...(materialFilter && { material: materialFilter }),
      },
    });
    const url = URL.createObjectURL(res.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = "certificates.xlsx";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex-1 overflow-auto">
      <Header title="Сертификаты" />
      <div className="p-6 space-y-4">
        {/* Filters */}
        <div className="flex flex-wrap gap-3 items-center">
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-200 text-sm focus:outline-none focus:border-amber-500"
          >
            {STATUS_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>

          <input
            value={productTypeFilter}
            onChange={(e) => { setProductTypeFilter(e.target.value); setPage(1); }}
            placeholder="Тип продукции..."
            className="px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-200 text-sm focus:outline-none focus:border-amber-500 w-44"
          />

          <input
            value={materialFilter}
            onChange={(e) => { setMaterialFilter(e.target.value); setPage(1); }}
            placeholder="Марка стали..."
            className="px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-200 text-sm focus:outline-none focus:border-amber-500 w-40"
          />

          <button
            onClick={() => setSortDesc(!sortDesc)}
            className="px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-300 text-sm hover:bg-slate-700 transition-colors"
          >
            {sortDesc ? "Новые сначала ↓" : "Старые сначала ↑"}
          </button>

          <div className="ml-auto flex gap-2">
            <Link
              href="/upload"
              className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold rounded-lg text-sm transition-colors"
            >
              + Загрузить
            </Link>
            <button
              onClick={handleExport}
              className="px-4 py-2 bg-slate-800 border border-slate-600 text-slate-300 hover:bg-slate-700 rounded-lg text-sm transition-colors"
            >
              Excel ↓
            </button>
          </div>
        </div>

        {/* Table */}
        <div className="bg-slate-900 border border-slate-700/50 rounded-xl overflow-hidden">
          {isLoading ? (
            <div className="p-8 text-slate-400 text-center">Загрузка...</div>
          ) : !data?.items.length ? (
            <div className="p-8 text-slate-400 text-center">
              Сертификаты не найдены
              <div className="mt-2">
                <Link href="/upload" className="text-amber-400 hover:text-amber-300 text-sm">
                  Загрузить первый сертификат →
                </Link>
              </div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-800/50 border-b border-slate-700">
                  <tr className="text-slate-400">
                    <th className="text-left px-4 py-3 font-medium">Наименование</th>
                    <th className="text-left px-4 py-3 font-medium">Тип</th>
                    <th className="text-left px-4 py-3 font-medium">Размер</th>
                    <th className="text-left px-4 py-3 font-medium">Марка</th>
                    <th className="text-left px-4 py-3 font-medium">ГОСТ</th>
                    <th className="text-left px-4 py-3 font-medium">Дата</th>
                    <th className="text-left px-4 py-3 font-medium">Производитель</th>
                    <th className="text-left px-4 py-3 font-medium">Статус</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((cert) => (
                    <tr
                      key={cert.id}
                      className="border-b border-slate-800 hover:bg-slate-800/40 cursor-pointer transition-colors"
                      onClick={() => window.location.href = `/certificates/${cert.id}`}
                    >
                      <td className="px-4 py-3">
                        <div className="text-slate-200 font-medium truncate max-w-[200px]">
                          {cert.normalized_product_name || cert.original_filename}
                        </div>
                        <div className="text-slate-500 text-xs truncate max-w-[200px]">
                          {cert.original_filename}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-slate-300">{cert.product_type ?? "—"}</td>
                      <td className="px-4 py-3 text-slate-300">{cert.dimensions ?? "—"}</td>
                      <td className="px-4 py-3 text-slate-300">{cert.material ?? "—"}</td>
                      <td className="px-4 py-3 text-slate-400 text-xs">{cert.gost ?? "—"}</td>
                      <td className="px-4 py-3 text-slate-400 text-xs">
                        {cert.certificate_date
                          ? new Date(cert.certificate_date).toLocaleDateString("ru-RU")
                          : "—"}
                      </td>
                      <td className="px-4 py-3 text-slate-300 text-xs truncate max-w-[150px]">
                        {cert.manufacturer ?? "—"}
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={cert.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Pagination */}
        {data && data.pages > 1 && (
          <div className="flex items-center justify-between">
            <span className="text-slate-400 text-sm">
              Показано {(page - 1) * 20 + 1}–{Math.min(page * 20, data.total)} из {data.total}
            </span>
            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
                className="px-3 py-1.5 bg-slate-800 border border-slate-600 rounded text-slate-300 text-sm disabled:opacity-40 hover:bg-slate-700 transition-colors"
              >
                ← Назад
              </button>
              <button
                disabled={page >= data.pages}
                onClick={() => setPage(page + 1)}
                className="px-3 py-1.5 bg-slate-800 border border-slate-600 rounded text-slate-300 text-sm disabled:opacity-40 hover:bg-slate-700 transition-colors"
              >
                Вперёд →
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
