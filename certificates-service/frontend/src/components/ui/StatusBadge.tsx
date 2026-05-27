import { CertificateStatus } from "@/types";

const STATUS_CONFIG: Record<CertificateStatus, { label: string; className: string }> = {
  [CertificateStatus.UPLOADED]: {
    label: "Загружен",
    className: "bg-slate-500/20 text-slate-400 border-slate-500/30",
  },
  [CertificateStatus.PROCESSING]: {
    label: "Обработка",
    className: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  },
  [CertificateStatus.PARSED]: {
    label: "Распознан",
    className: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  },
  [CertificateStatus.NEEDS_REVIEW]: {
    label: "Требует проверки",
    className: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  },
  [CertificateStatus.FAILED]: {
    label: "Ошибка",
    className: "bg-red-500/20 text-red-400 border-red-500/30",
  },
};

export function StatusBadge({ status }: { status: CertificateStatus }) {
  const config = STATUS_CONFIG[status] ?? STATUS_CONFIG[CertificateStatus.UPLOADED];
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${config.className}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current mr-1.5 opacity-70" />
      {config.label}
    </span>
  );
}
