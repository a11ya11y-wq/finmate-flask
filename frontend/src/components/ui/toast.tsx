import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import { cn } from "../../lib/utils";

type ToastVariant = "info" | "success" | "warning" | "error";

type ToastOptions = {
  message: string;
  title?: string;
  variant?: ToastVariant;
  duration?: number;
};

type ToastItem = ToastOptions & {
  id: string;
  variant: ToastVariant;
};

type ToastContextValue = {
  toast: (options: ToastOptions) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

const variantStyles: Record<ToastVariant, { wrapper: string; icon: string; iconColor: string }> = {
  info: {
    wrapper: "bg-[#0f172a]/80 border-blue-500/20 text-slate-100",
    icon: "bi-info-circle-fill",
    iconColor: "text-blue-400"
  },
  success: {
    wrapper: "bg-[#0f172a]/80 border-emerald-500/20 text-slate-100",
    icon: "bi-check-circle-fill",
    iconColor: "text-emerald-400"
  },
  warning: {
    wrapper: "bg-[#0f172a]/80 border-amber-500/20 text-slate-100",
    icon: "bi-exclamation-triangle-fill",
    iconColor: "text-amber-400"
  },
  error: {
    wrapper: "bg-[#0f172a]/80 border-rose-500/20 text-slate-100",
    icon: "bi-x-circle-fill",
    iconColor: "text-rose-400"
  }
};

const createToastId = () => `${Date.now()}-${Math.random().toString(16).slice(2)}`;

export const ToastProvider = ({ children }: { children: React.ReactNode }) => {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const toast = useCallback(
    (options: ToastOptions) => {
      const id = createToastId();
      const entry: ToastItem = {
        id,
        variant: options.variant ?? "info",
        ...options
      };
      setToasts((prev) => [...prev, entry]);
      const duration = options.duration ?? 4000;
      window.setTimeout(() => removeToast(id), duration);
    },
    [removeToast]
  );

  useEffect(() => {
    const handler = (event: Event) => {
      const detail = (event as CustomEvent<{ message?: string }>).detail;
      if (!detail?.message) {
        return;
      }
      toast({ variant: "warning", message: detail.message });
    };

    window.addEventListener("auth:logout", handler);
    return () => window.removeEventListener("auth:logout", handler);
  }, [toast]);

  const value = useMemo(() => ({ toast }), [toast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      {createPortal(
        <div className="fixed left-1/2 top-4 z-[100] flex w-fit min-w-[280px] max-w-[calc(100vw-2rem)] -translate-x-1/2 flex-col gap-2 sm:left-auto sm:right-6 sm:top-24 sm:w-[320px] sm:translate-x-0">
          {toasts.map((item) => {
            const config = variantStyles[item.variant];
            const messageLines = item.message
              .split("\n")
              .map((line) => line.trim())
              .filter(Boolean);
            return (
              <div
                key={item.id}
                data-testid="toast-item"
                data-variant={item.variant}
                onClick={() => removeToast(item.id)}
                className={cn(
                  "group relative cursor-pointer overflow-hidden rounded-[24px] border px-4 py-3 shadow-[0_8px_30px_rgb(0,0,0,0.24)] backdrop-blur-xl transition-all active:scale-95 sm:px-5 sm:py-3.5",
                  config.wrapper
                )}
              >
                <div className="flex items-center gap-3">
                  <span data-testid="toast-icon" className={cn("text-xl", config.iconColor)}>
                    <i className={`bi ${config.icon}`} />
                  </span>
                  <div className="flex-1">
                    {item.title && <p className="text-sm font-bold">{item.title}</p>}
                    {messageLines.length > 1 ? (
                      <div className="space-y-0.5 text-sm font-medium opacity-90">
                        {messageLines.map((line, index) => (
                          <p key={`${item.id}-${index}`}>{line}</p>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm font-medium opacity-90">{item.message}</p>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>,
        document.body
      )}
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return context;
};

