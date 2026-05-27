"use client";

import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { useEffect, useState } from "react";
import api, { getErrorMessage } from "@/lib/api";
import Header from "@/components/layout/Header";
import { Certificate } from "@/types";

function Field({ label, name, register, type = "text" }: { label: string; name: string; register: ReturnType<typeof useForm>["register"]; type?: string }) {
  return (
    <div>
      <label className="block text-xs text-slate-400 mb-1">{label}</label>
      <input
        {...register(name as keyof Certificate)}
        type={type}
        className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-200 text-sm focus:outline-none focus:border-amber-500 transition-colors"
      />
    </div>
  );
}

export default function EditCertificatePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const qc = useQueryClient();
  const [error, setError] = useState("");

  const { data: cert, isLoading } = useQuery<Certificate>({
    queryKey: ["certificate", id],
    queryFn: () => api.get(`/certificates/${id}`).then((r) => r.data),
  });

  const { register, handleSubmit, reset } = useForm();

  useEffect(() => {
    if (cert) {
      reset({
        certificate_number: cert.certificate_number ?? "",
        certificate_date: cert.certificate_date ?? "",
        manufacturer: cert.manufacturer ?? "",
        supplier: cert.supplier ?? "",
        product_name: cert.product_name ?? "",
        product_type: cert.product_type ?? "",
        material: cert.material ?? "",
        gost: cert.gost ?? "",
        dimensions: cert.dimensions ?? "",
        batch_number: cert.batch_number ?? "",
        heat_number: cert.heat_number ?? "",
      });
    }
  }, [cert, reset]);

  const update = useMutation({
    mutationFn: (data: Record<string, string>) => api.patch(`/certificates/${id}`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["certificate", id] });
      router.push(`/certificates/${id}`);
    },
    onError: (err) => setError(getErrorMessage(err)),
  });

  if (isLoading) return (
    <div className="flex-1 overflow-auto">
      <Header title="Редактирование" />
      <div className="p-6 text-slate-400">Загрузка...</div>
    </div>
  );

  return (
    <div className="flex-1 overflow-auto">
      <Header title="Редактирование сертификата" />
      <div className="p-6 max-w-2xl mx-auto">
        <div className="flex items-center gap-2 text-sm mb-6">
          <Link href="/certificates" className="text-slate-400 hover:text-slate-200">Сертификаты</Link>
          <span className="text-slate-600">/</span>
          <Link href={`/certificates/${id}`} className="text-slate-400 hover:text-slate-200">#{id}</Link>
          <span className="text-slate-600">/</span>
          <span className="text-slate-200">Редактирование</span>
        </div>

        <div className="bg-slate-900 border border-slate-700/50 rounded-xl p-6">
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit((data) => update.mutate(data as Record<string, string>))} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Field label="Номер сертификата" name="certificate_number" register={register} />
              <Field label="Дата сертификата" name="certificate_date" register={register} type="date" />
              <Field label="Тип продукции" name="product_type" register={register} />
              <Field label="Размер" name="dimensions" register={register} />
              <Field label="Марка стали" name="material" register={register} />
              <Field label="ГОСТ / ТУ" name="gost" register={register} />
              <Field label="Производитель" name="manufacturer" register={register} />
              <Field label="Поставщик" name="supplier" register={register} />
              <Field label="Номер партии" name="batch_number" register={register} />
              <Field label="Номер плавки" name="heat_number" register={register} />
            </div>

            <div className="pt-4 flex gap-3">
              <button
                type="submit"
                disabled={update.isPending}
                className="px-6 py-2.5 bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-950 font-semibold rounded-lg text-sm transition-colors"
              >
                {update.isPending ? "Сохранение..." : "Сохранить"}
              </button>
              <Link
                href={`/certificates/${id}`}
                className="px-6 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm transition-colors"
              >
                Отмена
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
