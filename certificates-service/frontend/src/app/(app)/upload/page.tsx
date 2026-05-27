"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import api, { getErrorMessage } from "@/lib/api";
import Header from "@/components/layout/Header";
import { DropZone } from "@/components/upload/DropZone";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { CertificateStatus, UploadedFile } from "@/types";

export default function UploadPage() {
  const router = useRouter();
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [uploading, setUploading] = useState(false);

  const onFiles = useCallback((newFiles: File[]) => {
    const items: UploadedFile[] = newFiles.map((f) => ({
      id: `${f.name}-${Date.now()}-${Math.random()}`,
      file: f,
      status: "pending",
      progress: 0,
    }));
    setFiles((prev) => [...prev, ...items]);
  }, []);

  const uploadFile = async (item: UploadedFile) => {
    const formData = new FormData();
    formData.append("file", item.file);

    try {
      setFiles((prev) =>
        prev.map((f) => (f.id === item.id ? { ...f, status: "uploading", progress: 10 } : f))
      );

      const res = await api.post("/certificates/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (e) => {
          const pct = e.total ? Math.round((e.loaded / e.total) * 80) + 10 : 50;
          setFiles((prev) =>
            prev.map((f) => (f.id === item.id ? { ...f, progress: pct } : f))
          );
        },
      });

      setFiles((prev) =>
        prev.map((f) =>
          f.id === item.id
            ? { ...f, status: "processing", progress: 100, certificateId: res.data.id }
            : f
        )
      );

      // Poll status
      pollStatus(item.id, res.data.id);
    } catch (err) {
      setFiles((prev) =>
        prev.map((f) =>
          f.id === item.id ? { ...f, status: "error", error: getErrorMessage(err) } : f
        )
      );
    }
  };

  const pollStatus = (fileId: string, certId: number) => {
    let attempts = 0;
    const timer = setInterval(async () => {
      attempts++;
      try {
        const res = await api.get(`/certificates/${certId}`);
        const status = res.data.status as CertificateStatus;
        if (
          status === CertificateStatus.PARSED ||
          status === CertificateStatus.NEEDS_REVIEW ||
          status === CertificateStatus.FAILED
        ) {
          clearInterval(timer);
          setFiles((prev) =>
            prev.map((f) => (f.id === fileId ? { ...f, status: "done" } : f))
          );
        }
      } catch {
        // ignore polling errors
      }
      if (attempts > 30) {
        clearInterval(timer);
        setFiles((prev) =>
          prev.map((f) => (f.id === fileId ? { ...f, status: "done" } : f))
        );
      }
    }, 3000);
  };

  const handleUploadAll = async () => {
    setUploading(true);
    const pending = files.filter((f) => f.status === "pending");
    await Promise.allSettled(pending.map(uploadFile));
    setUploading(false);
  };

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const pendingCount = files.filter((f) => f.status === "pending").length;

  return (
    <div className="flex-1 overflow-auto">
      <Header title="Загрузка сертификатов" />
      <div className="p-6 max-w-3xl mx-auto space-y-6">
        <DropZone onFiles={onFiles} disabled={uploading} />

        {files.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-slate-200 font-medium">
                Файлы ({files.length})
              </h3>
              <div className="flex gap-2">
                {pendingCount > 0 && (
                  <button
                    onClick={handleUploadAll}
                    disabled={uploading}
                    className="px-4 py-2 bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-950 font-semibold rounded-lg text-sm transition-colors"
                  >
                    {uploading ? "Загрузка..." : `Загрузить (${pendingCount})`}
                  </button>
                )}
                <button
                  onClick={() => setFiles([])}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm transition-colors"
                >
                  Очистить
                </button>
              </div>
            </div>

            {files.map((item) => (
              <div
                key={item.id}
                className="bg-slate-900 border border-slate-700/50 rounded-lg p-4 flex items-center gap-4"
              >
                {/* Icon */}
                <div className="w-10 h-10 bg-slate-800 rounded-lg flex items-center justify-center flex-shrink-0">
                  <svg className="w-5 h-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="text-slate-200 text-sm font-medium truncate">{item.file.name}</div>
                  <div className="text-slate-500 text-xs">
                    {(item.file.size / 1024 / 1024).toFixed(2)} МБ
                  </div>
                  {(item.status === "uploading" || item.status === "processing") && (
                    <div className="mt-1.5 h-1 bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-amber-500 rounded-full transition-all"
                        style={{ width: `${item.progress}%` }}
                      />
                    </div>
                  )}
                  {item.status === "error" && (
                    <div className="text-red-400 text-xs mt-1">{item.error}</div>
                  )}
                </div>

                {/* Status */}
                <div className="flex items-center gap-2 flex-shrink-0">
                  {item.status === "done" && item.certificateId ? (
                    <Link
                      href={`/certificates/${item.certificateId}`}
                      className="text-amber-400 text-xs hover:text-amber-300"
                    >
                      Открыть →
                    </Link>
                  ) : item.status === "processing" ? (
                    <span className="text-blue-400 text-xs">Обрабатывается...</span>
                  ) : item.status === "uploading" ? (
                    <span className="text-slate-400 text-xs">{item.progress}%</span>
                  ) : item.status === "error" ? (
                    <span className="text-red-400 text-xs">Ошибка</span>
                  ) : null}

                  {item.status === "pending" && (
                    <button
                      onClick={() => removeFile(item.id)}
                      className="text-slate-500 hover:text-slate-300"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
