import * as React from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

/** Right-side slide-over. Portaled to <body> so it escapes the frosted window's
 *  backdrop-filter containing block (otherwise `fixed` clips inside it). */
export function Sheet({
  open,
  onClose,
  children,
  className,
}: {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
  className?: string;
}) {
  React.useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    if (open) window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  return createPortal(
    <div className={cn("fixed inset-0 z-[100]", open ? "pointer-events-auto" : "pointer-events-none")}>
      <div
        onClick={onClose}
        className={cn(
          "absolute inset-0 bg-black/25 backdrop-blur-[1px] transition-opacity duration-300",
          open ? "opacity-100" : "opacity-0"
        )}
      />
      <div
        className={cn(
          "absolute right-0 top-0 h-full w-full max-w-[520px] border-l border-border bg-card shadow-pop transition-transform duration-300 ease-out",
          open ? "translate-x-0" : "translate-x-full",
          className
        )}
      >
        <button
          onClick={onClose}
          className="absolute right-4 top-4 z-10 rounded-md p-1.5 text-muted-foreground hover:bg-muted"
          aria-label="Close"
        >
          <X className="size-4" />
        </button>
        <div className="h-full overflow-y-auto">{open ? children : null}</div>
      </div>
    </div>,
    document.body
  );
}
