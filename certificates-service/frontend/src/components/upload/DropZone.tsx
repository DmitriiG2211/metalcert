"use client";

import { useCallback } from "react";
import { useDropzone } from "react-dropzone";

interface DropZoneProps {
  onFiles: (files: File[]) => void;
  disabled?: boolean;
}

const ACCEPTED_TYPES = {
  "application/pdf": [".pdf"],
  "image/jpeg": [".jpg", ".jpeg"],
  "image/png": [".png"],
  "image/webp": [".webp"],
  "image/tiff": [".tiff", ".tif"],
};

export function DropZone({ onFiles, disabled }: DropZoneProps) {
  const onDrop = useCallback(
    (accepted: File[]) => {
      if (accepted.length > 0) onFiles(accepted);
    },
    [onFiles]
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    disabled,
    maxSize: 50 * 1024 * 1024,
  });

  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all ${
        isDragActive && !isDragReject
          ? "border-amber-500 bg-amber-500/5"
          : isDragReject
          ? "border-red-500 bg-red-500/5"
          : "border-slate-600 hover:border-slate-500 hover:bg-slate-800/30"
      } ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
    >
      <input {...getInputProps()} />
      <div className="flex flex-col items-center gap-4">
        <div
          className={`w-16 h-16 rounded-2xl flex items-center justify-center ${
            isDragActive ? "bg-amber-500/20" : "bg-slate-800"
          }`}
        >
          {isDragActive ? (
            <svg className="w-8 h-8 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          ) : (
            <svg className="w-8 h-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4v16m8-8H4" />
            </svg>
          )}
        </div>
        <div>
          <p className="text-slate-200 font-medium">
            {isDragActive
              ? isDragReject
                ? "Неподдерживаемый формат"
                : "Отпустите файлы"
              : "Перетащите файлы или нажмите для выбора"}
          </p>
          <p className="text-slate-500 text-sm mt-1">
            PDF, JPG, PNG, WEBP, TIFF — до 50 МБ каждый
          </p>
        </div>
      </div>
    </div>
  );
}
