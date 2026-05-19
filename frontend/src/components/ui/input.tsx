import * as React from "react";
import { cn } from "../../lib/utils";

type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

export const Input = ({ className, ...props }: InputProps) => {
  return (
    <input
      className={cn(
        "w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-100",
        "placeholder:text-slate-400 focus:border-blue-400/60 focus:outline-none focus:ring-2 focus:ring-blue-500/20",
        className
      )}
      {...props}
    />
  );
};
