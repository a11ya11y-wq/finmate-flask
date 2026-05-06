import * as React from "react";
import { cn } from "../../lib/utils";

type CardProps = React.HTMLAttributes<HTMLDivElement>;

type CardHeaderProps = React.HTMLAttributes<HTMLDivElement>;

type CardTitleProps = React.HTMLAttributes<HTMLHeadingElement>;

type CardContentProps = React.HTMLAttributes<HTMLDivElement>;

type CardFooterProps = React.HTMLAttributes<HTMLDivElement>;

export const Card = ({ className, ...props }: CardProps) => {
  return (
    <div
      className={cn(
        "rounded-2xl border border-white/10 bg-white/5 shadow-[0_20px_60px_rgba(0,0,0,0.35)]",
        className
      )}
      {...props}
    />
  );
};

export const CardHeader = ({ className, ...props }: CardHeaderProps) => {
  return <div className={cn("border-b border-white/5 px-6 py-4", className)} {...props} />;
};

export const CardTitle = ({ className, ...props }: CardTitleProps) => {
  return <h3 className={cn("text-base font-semibold text-slate-100", className)} {...props} />;
};

export const CardContent = ({ className, ...props }: CardContentProps) => {
  return <div className={cn("px-6 py-4", className)} {...props} />;
};

export const CardFooter = ({ className, ...props }: CardFooterProps) => {
  return <div className={cn("border-t border-white/5 px-6 py-4", className)} {...props} />;
};

