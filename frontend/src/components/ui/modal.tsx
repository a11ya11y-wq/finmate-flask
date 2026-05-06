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
};

const sizeClasses: Record<NonNullable<ModalProps["size"]>, string> = {
  sm: "max-w-md",
  md: "max-w-2xl",
  lg: "max-w-4xl"
};

const Modal = ({ isOpen, title, onClose, children, footer, size = "md" }: ModalProps) => {
  useEffect(() => {
    if (!isOpen) {
      return undefined;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) {
    return null;
  }

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
      <button
        type="button"
        aria-label="Close modal"
        className="absolute inset-0 bg-black/60"
        onClick={onClose}
      />
      <div
        className={cn(
          "relative w-full overflow-hidden rounded-2xl border border-white/10 bg-[#0b0f17] shadow-[0_20px_60px_rgba(0,0,0,0.5)]",
          sizeClasses[size]
        )}
      >
        {title && (
          <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
            <h3 className="text-lg font-semibold text-slate-100">{title}</h3>
            <button
              type="button"
              className="rounded-lg border border-white/10 bg-white/5 px-2 py-1 text-slate-300 hover:bg-white/10"
              onClick={onClose}
            >
              ✕
            </button>
          </div>
        )}
        <div className="px-6 py-5">{children}</div>
        {footer && <div className="border-t border-white/10 px-6 py-4">{footer}</div>}
      </div>
    </div>,
    document.body
  );
};

export default Modal;

