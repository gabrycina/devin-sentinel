import * as React from "react";
import { cn } from "@/lib/utils";

export function Badge({
  className,
  color,
  children,
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & { color?: string }) {
  const style = color
    ? {
        color,
        backgroundColor: `color-mix(in srgb, ${color} 10%, transparent)`,
        borderColor: `color-mix(in srgb, ${color} 22%, transparent)`,
      }
    : undefined;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 whitespace-nowrap rounded-full border px-2 py-0.5 text-xs font-medium",
        !color && "border-border bg-muted text-muted-foreground",
        className
      )}
      style={style}
      {...props}
    >
      {children}
    </span>
  );
}
