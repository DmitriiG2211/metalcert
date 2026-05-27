"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import api, { getErrorMessage } from "@/lib/api";
import Header from "@/components/layout/Header";
import { useAuth } from "@/hooks/useAuth";

export default function SettingsPage() {
  const { user } = useAuth();
  const [pwSuccess, setPwSuccess] = useState(false);
  const [pwError, setPwError] = useState("");

  const { register, handleSubmit, reset, formState: { isSubmitting } } = useForm<{
    current_password: string;
    new_password: string;
    confirm_password: string;
  }>();

  const changePassword = async (data: { current_password: string; new_password: string; confirm_password: string }) => {
    setPwError("");
    setPwSuccess(false);
    if (data.new_password !== data.confirm_password) {
      setPwError("Пароли не совпадают");
      return;
    }
    try {
      await api.post("/auth/change-password", {
        current_password: data.current_password,
        new_password: data.new_password,
      });
      setPwSuccess(true);
      reset();
    } catch (err) {
      setPwError(getErrorMessage(err));
    }
  };

  const roleLabel: Record<string, string> = {
    admin: "Администратор",
    manager: "Менеджер",
    viewer: "Наблюдатель",
  };

  return (
    <div className="flex-1 overflow-auto">
      <Header title="Настройки" />
      <div className="p-6 max-w-xl mx-auto space-y-6">
        {/* Profile */}
        <div className="bg-slate-900 border border-slate-700/50 rounded-xl p-6">
          <h2 className="text-slate-200 font-semibold mb-4">Профиль</h2>
          <div className="flex items-center gap-4 mb-4">
            <div className="w-14 h-14 bg-amber-500 rounded-full flex items-center justify-center text-slate-950 text-xl font-bold">
              {user?.email?.[0]?.toUpperCase() ?? "?"}
            </div>
            <div>
              <div className="text-slate-100 font-medium">{user?.email}</div>
              <div className="text-slate-400 text-sm">{roleLabel[user?.role ?? ""] ?? user?.role}</div>
            </div>
          </div>
          <div className="text-xs text-slate-500">
            Для смены email обратитесь к администратору
          </div>
        </div>

        {/* Change password */}
        <div className="bg-slate-900 border border-slate-700/50 rounded-xl p-6">
          <h2 className="text-slate-200 font-semibold mb-4">Смена пароля</h2>

          {pwSuccess && (
            <div className="mb-4 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm">
              Пароль успешно изменён
            </div>
          )}
          {pwError && (
            <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
              {pwError}
            </div>
          )}

          <form onSubmit={handleSubmit(changePassword)} className="space-y-3">
            <div>
              <label className="text-xs text-slate-400 block mb-1">Текущий пароль</label>
              <input
                {...register("current_password", { required: true })}
                type="password"
                className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-200 text-sm focus:outline-none focus:border-amber-500"
              />
            </div>
            <div>
              <label className="text-xs text-slate-400 block mb-1">Новый пароль</label>
              <input
                {...register("new_password", { required: true, minLength: 6 })}
                type="password"
                className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-200 text-sm focus:outline-none focus:border-amber-500"
              />
            </div>
            <div>
              <label className="text-xs text-slate-400 block mb-1">Подтвердите пароль</label>
              <input
                {...register("confirm_password", { required: true })}
                type="password"
                className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-200 text-sm focus:outline-none focus:border-amber-500"
              />
            </div>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-5 py-2 bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-950 font-semibold rounded-lg text-sm mt-2 transition-colors"
            >
              {isSubmitting ? "Сохранение..." : "Изменить пароль"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
