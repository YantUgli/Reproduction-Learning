import type { HTMLAttributes } from "react";

/** Kontainer surface standar: putih, border token, radius, shadow halus. */
export default function Card({
  className = "",
  ...rest
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`rounded-md border border-border bg-surface shadow-sm ${className}`}
      {...rest}
    />
  );
}
