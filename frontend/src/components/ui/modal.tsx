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
  sm: "max-w-[420px]", // Звузили для ідеального вигляду форми
  md: "max-w-2xl",
  lg: "max-w-4xl"
};

const variantClasses: Record<NonNullable<ModalProps["variant"]>, string> = {
  default: "border-t-blue-500",
  success: "border-t-emerald-500",
  danger: "border-t-rose-500"
};

const Modal = ({ isOpen, title, onClose, children, footer, size = "sm", variant = "success" }: ModalProps) => {
  useEffect(() => {
    if (!isOpen) return undefined;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4 backdrop-blur-[2px]">
      <button
        type="button"
        aria-label="Close modal"
        className="absolute inset-0 bg-black/60 transition-opacity animate-in fade-in duration-200"
        onClick={onClose}
      />
      <div
        className={cn(
          "relative w-full overflow-hidden rounded-2xl border border-white/10 bg-[#11151f] shadow-[0_20px_60px_rgba(0,0,0,0.7)] border-t-[4px] animate-in fade-in zoom-in-95 duration-200",
          sizeClasses[size],
          variantClasses[variant]
        )}
      >
        {title && (
          <div className="flex items-center justify-between px-6 pt-5 pb-2">
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
        <div className="px-6 py-4">{children}</div>
        {footer && <div className="bg-black/20 px-6 py-4">{footer}</div>}
      </div>
    </div>,
    document.body
  );
};

export default Modal;