import * as SeparatorPrimitive from "@radix-ui/react-separator"
import { cn } from "@/lib/utils"
import * as React from "react"

const Separator = React.forwardRef<
  React.ElementRef<typeof SeparatorPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof SeparatorPrimitive.Root>
>(({ className, orientation = "horizontal", decorative = true, ...props }, ref) => (
  <SeparatorPrimitive.Root
    ref={ref}
    decorative={decorative}
    orientation={orientation}
    className={cn(orientation === "horizontal" ? "h-px w-full bg-white/10" : "h-full w-px bg-white/10", className)}
    {...props}
  />
))
Separator.displayName = SeparatorPrimitive.Root.displayName

export { Separator }
