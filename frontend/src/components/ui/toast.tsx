import { createContext, useCallback, useContext, useMemo, useState } from "react";
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
    wrapper: "border-blue-500/30 bg-[#0b0f17]/95",
    icon: "bi-info-circle",
    iconColor: "text-blue-300"
  },
  success: {
    wrapper: "border-emerald-500/30 bg-[#0b0f17]/95",
    icon: "bi-check-circle",
    iconColor: "text-emerald-300"
  },
  warning: {
    wrapper: "border-amber-500/30 bg-[#0b0f17]/95",
    icon: "bi-exclamation-triangle",
    iconColor: "text-amber-300"
  },
  error: {
    wrapper: "border-rose-500/30 bg-[#0b0f17]/95",
    icon: "bi-x-circle",
    iconColor: "text-rose-300"
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

  const value = useMemo(() => ({ toast }), [toast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      {createPortal(
        <div className="fixed right-6 top-36 z-[100] flex w-[320px] max-w-[calc(100vw-3rem)] flex-col gap-3">
          {toasts.map((item) => {
            const config = variantStyles[item.variant];
            return (
              <div
                key={item.id}
                data-testid="toast-item"
                data-variant={item.variant}
                className={cn(
                  "relative rounded-2xl border px-4 py-3 text-slate-100 shadow-[0_20px_40px_rgba(0,0,0,0.45)] backdrop-blur",
                  config.wrapper
                )}
              >
                <div className="flex items-start gap-3">
                  <span data-testid="toast-icon" className={cn("text-lg", config.iconColor)}>
                    <i className={`bi ${config.icon}`} />
                  </span>
                  <div className="flex-1">
                    {item.title && <p className="text-sm font-semibold text-slate-100">{item.title}</p>}
                    <p className="text-sm text-slate-200">{item.message}</p>
                  </div>
                  <button
                    type="button"
                    className="text-slate-500 transition hover:text-slate-200"
                    onClick={() => removeToast(item.id)}
                    aria-label="Close notification"
                  >
                    <i className="bi bi-x-lg" />
                  </button>
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

