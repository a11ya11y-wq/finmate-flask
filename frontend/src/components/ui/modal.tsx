import { useEffect } from "react";
import { createPortal } from "react-dom";
import type { ReactNode } from "react";
import { cn } from "../../lib/utils";

type ModalProps = {
  isOpen: boolean;
  title?: string;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
  size?: "sm" | "md" | "lg";
  variant?: "default" | "success" | "danger";
};

const sizeClasses: Record<NonNullable<ModalProps["size"]>, string> = {
  sm: "sm:max-w-[420px]", // На мобільному без обмежень, на десктопі вузька
  md: "sm:max-w-2xl",
  lg: "sm:max-w-4xl"
};

const variantClasses: Record<NonNullable<ModalProps["variant"]>, string> = {
  default: "border-t-blue-500",
  success: "border-t-emerald-500",
  danger: "border-t-rose-500"
};

const Modal = ({ isOpen, title, onClose, children, footer, size = "sm", variant = "success" }: ModalProps) => {
  useEffect(() => {
    if (!isOpen) return undefined;

    // Вимірюємо ширину скролбара щоб компенсувати зсув при overflow:hidden
    const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;
    document.body.style.overflow = "hidden";
    document.body.style.paddingRight = `${scrollbarWidth}px`;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
      document.body.style.paddingRight = "";
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return createPortal(
    <div className="fixed inset-0 z-[100] flex items-center justify-center px-4 backdrop-blur-[2px]">
      <button
        type="button"
        aria-label="Close modal"
        className="absolute inset-0 bg-black/60 transition-opacity animate-in fade-in duration-200"
        onClick={onClose}
      />
      <div
        className={cn(
          "relative w-full overflow-hidden rounded-2xl border border-white/10 bg-[#11151f] border-t-[4px] flex flex-col",
          "shadow-[0_20px_60px_rgba(0,0,0,0.7)] animate-in fade-in zoom-in-95 duration-200",
          "max-h-[90vh]",
          sizeClasses[size],
          variantClasses[variant]
        )}
      >
        {title && (
          <div className="flex shrink-0 items-center justify-between px-6 pt-5 pb-2">
            <h3 className="text-lg font-bold text-slate-100">{title}</h3>
            <button
              type="button"
              className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-white/10 hover:text-white"
              onClick={onClose}
            >
              <i className="bi bi-x-lg" />
            </button>
          </div>
        )}
        <div className="flex-1 overflow-y-auto px-6 py-4">{children}</div>
        {footer && <div className="shrink-0 bg-black/20 px-6 py-4">{footer}</div>}
      </div>
    </div>,
    document.body
  );
};

export default Modal;