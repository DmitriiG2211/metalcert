"use client";

import { useState, useCallback } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useDebounce } from "use-debounce";
import api from "@/lib/api";
import Header from "@/components/layout/Header";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Certificate, PaginatedResponse } from "@/types";

const EXAMPLES = [
  "120х120", "Ст3", "ГОСТ 10704", "09Г2С", "труба профильная", "А500С 12",
];

export default function SearchPage() {
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const [debouncedQ] = useDebounce(q, 400);

  const { data, isFetching } = useQuery<PaginatedResponse<Certificate>>({
    queryKey: ["search", debouncedQ, page],
    queryFn: () =>
      api
        .get("/search", { params: { q: debouncedQ, page, page_size: 20 } })
        .then((r) => r.data),
    enabled: debouncedQ.length > 1,
  });

  return (
    <div className="flex-1 overflow-auto">
      <Header title="Поиск" />
      <div className="p-6 space-y-6">
        {/* Search bar */}
        <div className="relative">
          <svg
            className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400"
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            value={q}
            onChange={(e) => { setQ(e.target.value); setPage(1); }}
            placeholder="Поиск: труба 120, Ст3, ГОСТ 8639, 09Г2С..."
            className="w-full pl-12 pr-4 py-3.5 bg-slate-900 border border-slate-600 rounded-xl text-slate-100 text-base placeholder-slate-500 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 transition-colors"
            autoFocus
          />
          {isFetching && (
            <div className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
          )}
        </div>

        {/* Examples */}
        {!q && (
          <div>
            <p className="text-slate-500 text-sm mb-3">Примеры запросов:</p>
            <div className="flex flex-wrap gap-2">
              {EXAMPLES.map((ex) => (
                <button
                  key={ex}
                  onClick={() => setQ(ex)}
                  className="px-3 py-1.5 bg-slate-800 border border-slate-700 text-slate-300 rounded-lg text-sm hover:bg-slate-700 hover:border-slate-500 transition-colors"
                >
                  {ex}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Results */}
        {debouncedQ.length > 1 && (
          <div>
            {data?.total !== undefined && (
              <p className="text-slate-400 text-sm mb-3">
                {data.total > 0
                  ? `Найдено: ${data.total}`
                  : "Ничего не найдено"}
              </p>
            )}

            {data?.items.length ? (
              <>
                <div className="space-y-2">
                  {data.items.map((cert) => (
                    <Link
                      key={cert.id}
                      href={`/certificates/${cert.id}`}
                      className="block bg-slate-900 border border-slate-700/50 rounded-xl p-4 hover:border-amber-500/30 hover:bg-slate-800/50 transition-all"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <div className="text-slate-100 font-medium truncate">
                            {cert.normalized_product_name || cert.original_filename}
                          </div>
                          <div className="text-slate-400 text-sm mt-1 flex flex-wrap gap-3">
                            {cert.material && <span>Марка: <span className="text-slate-300">{cert.material}</span></span>}
                            {cert.gost && <span>ГОСТ: <span className="text-slate-300">{cert.gost}</span></span>}
                            {cert.manufacturer && <span>Производитель: <span className="text-slate-300">{cert.manufacturer}</span></span>}
                            {cert.certificate_date && (
                              <span>Дата: <span className="text-slate-300">{new Date(cert.certificate_date).toLocaleDateString("ru-RU")}</span></span>
                            )}
                          </div>
                        </div>
                        <StatusBadge status={cert.status} />
                      </div>
                    </Link>
                  ))}
                </div>

                {data.pages > 1 && (
                  <div className="flex items-center justify-between mt-4">
                    <span className="text-slate-400 text-sm">Стр. {page} из {data.pages}</span>
                    <div className="flex gap-2">
                      <button
                        disabled={page <= 1}
                        onClick={() => setPage(page - 1)}
                        className="px-3 py-1.5 bg-slate-800 border border-slate-600 rounded text-slate-300 text-sm disabled:opacity-40"
                      >
                        ←
                      </button>
                      <button
                        disabled={page >= data.pages}
                        onClick={() => setPage(page + 1)}
                        className="px-3 py-1.5 bg-slate-800 border border-slate-600 rounded text-slate-300 text-sm disabled:opacity-40"
                      >
                        →
                      </button>
                    </div>
                  </div>
                )}
              </>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}
