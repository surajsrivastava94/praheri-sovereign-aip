"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { RoleProvider } from "@/lib/role";
import { DemoProvider } from "@/lib/demo";

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(() => new QueryClient());
  return (
    <QueryClientProvider client={client}>
      <RoleProvider>
        <DemoProvider>{children}</DemoProvider>
      </RoleProvider>
    </QueryClientProvider>
  );
}
