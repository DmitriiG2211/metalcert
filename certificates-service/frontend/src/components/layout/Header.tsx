"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { removeToken } from "@/lib/auth";
import { useAuth } from "@/hooks/useAuth";

export default function Header({ title }: { title?: string }) {
  const { user } = useAuth();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const roleLabel: Record<string, string> = {
    admin: "Администратор",
    manager: "Менеджер",
    viewer: "Наблюдатель",
  };

  return (
    <header className="h-14 bg-slate-900/80 backdrop-blur border-b border-slate-700/50 flex items-center px-6 gap-4">
      {title && (
        <h1 className="text-slate-100 font-semibold text-base">{title}</h1>
      )}
      <div className="ml-auto flex items-center gap-3" ref={ref}>
        <div className="relative">
          <button
            onClick={() => setOpen(!open)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-600 transition-colors"
          >
            <div className="w-6 h-6 rounded-full bg-amber-500 flex items-center justify-center text-slate-950 text-xs font-bold">
              {user?.email?.[0]?.toUpperCase() ?? "?"}
            </div>
            <div className="text-left hidden sm:block">
              <div className="text-slate-200 text-xs font-medium leading-none">{user?.email}</div>
              <div className="text-slate-400 text-xs leading-none mt-0.5">
                {roleLabel[user?.role ?? ""] ?? user?.role}
              </div>
            </div>
            <svg className="w-3 h-3 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {open && (
            <div className="absolute right-0 top-full mt-1 w-44 bg-slate-800 border border-slate-600 rounded-lg shadow-xl py-1 z-50">
              <button
                onClick={() => { router.push("/settings"); setOpen(false); }}
                className="w-full text-left px-4 py-2 text-sm text-slate-300 hover:text-slate-100 hover:bg-slate-700 transition-colors"
              >
                Профиль
              </button>
              <hr className="border-slate-700 my-1" />
              <button
                onClick={() => { removeToken(); router.push("/login"); }}
                className="w-full text-left px-4 py-2 text-sm text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-colors"
              >
                Выйти
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
