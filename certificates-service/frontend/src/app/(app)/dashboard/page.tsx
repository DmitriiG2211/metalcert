"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import api from "@/lib/api";
import Header from "@/components/layout/Header";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { CertificateStatus } from "@/types";

function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="bg-slate-900 border border-slate-700/50 rounded-xl p-5">
      <div className={`text-3xl font-bold ${color}`}>{value}</div>
      <div className="text-slate-400 text-sm mt-1">{label}</div>
    </div>
  );
}

export default function DashboardPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: () => api.get("/dashboard/stats").then((r) => r.data),
    refetchInterval: 30000,
  });

  if (isLoading) {
    return (
      <div className="flex-1 overflow-auto">
        <Header title="Дашборд" />
        <div className="p-6 text-slate-400">Загрузка...</div>
      </div>
    );
  }

  const byStatus: Record<string, number> = stats?.by_status ?? {};

  return (
    <div className="flex-1 overflow-auto">
      <Header title="Дашборд" />
      <div className="p-6 space-y-6">
        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard label="Всего сертификатов" value={stats?.total ?? 0} color="text-slate-100" />
          <StatCard label="Распознано" value={byStatus.parsed ?? 0} color="text-emerald-400" />
          <StatCard label="Требует проверки" value={byStatus.needs_review ?? 0} color="text-amber-400" />
          <StatCard label="Ошибка" value={byStatus.failed ?? 0} color="text-red-400" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* By product type */}
          <div className="bg-slate-900 border border-slate-700/50 rounded-xl p-5">
            <h3 className="text-slate-200 font-semibold mb-4">По типу продукции</h3>
            {stats?.by_product_type?.length ? (
              <div className="space-y-2">
                {stats.by_product_type.map((item: { product_type: string; count: number }) => (
                  <div key={item.product_type} className="flex items-center gap-3">
                    <div className="flex-1 text-slate-300 text-sm truncate">{item.product_type}</div>
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-amber-500 rounded-full"
                          style={{ width: `${Math.min((item.count / stats.total) * 100 * 3, 100)}%` }}
                        />
                      </div>
                      <span className="text-slate-400 text-sm w-6 text-right">{item.count}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-500 text-sm">Нет данных</p>
            )}
          </div>

          {/* By manufacturer */}
          <div className="bg-slate-900 border border-slate-700/50 rounded-xl p-5">
            <h3 className="text-slate-200 font-semibold mb-4">По производителям</h3>
            {stats?.by_manufacturer?.length ? (
              <div className="space-y-2">
                {stats.by_manufacturer.map((item: { manufacturer: string; count: number }) => (
                  <div key={item.manufacturer} className="flex items-center justify-between gap-2">
                    <div className="text-slate-300 text-sm truncate flex-1">{item.manufacturer}</div>
                    <span className="text-slate-400 text-sm flex-shrink-0">{item.count}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-500 text-sm">Нет данных</p>
            )}
          </div>
        </div>

        {/* Recent uploads */}
        <div className="bg-slate-900 border border-slate-700/50 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-slate-200 font-semibold">Последние загрузки</h3>
            <Link href="/certificates" className="text-amber-400 text-sm hover:text-amber-300">
              Все →
            </Link>
          </div>
          {stats?.recent_uploads?.length ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-slate-400 border-b border-slate-700/50">
                    <th className="text-left pb-2 font-medium">Файл</th>
                    <th className="text-left pb-2 font-medium">Товар</th>
                    <th className="text-left pb-2 font-medium">Статус</th>
                    <th className="text-left pb-2 font-medium">Дата</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.recent_uploads.map((c: { id: number; original_filename: string; product_name: string; status: CertificateStatus; created_at: string }) => (
                    <tr key={c.id} className="border-b border-slate-800 hover:bg-slate-800/50">
                      <td className="py-2 pr-4">
                        <Link href={`/certificates/${c.id}`} className="text-slate-300 hover:text-amber-400 truncate block max-w-[200px]">
                          {c.original_filename}
                        </Link>
                      </td>
                      <td className="py-2 pr-4 text-slate-300 truncate max-w-[200px]">
                        {c.product_name || "—"}
                      </td>
                      <td className="py-2 pr-4">
                        <StatusBadge status={c.status as CertificateStatus} />
                      </td>
                      <td className="py-2 text-slate-400">
                        {new Date(c.created_at).toLocaleDateString("ru-RU")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-slate-500 text-sm">Нет загруженных сертификатов</p>
          )}
        </div>
      </div>
    </div>
  );
}
