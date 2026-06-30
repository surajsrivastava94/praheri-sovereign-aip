"use client";

import { createContext, useContext, useEffect, useState } from "react";

export type Role = "analyst" | "mlro";

const RoleContext = createContext<{ role: Role; setRole: (r: Role) => void }>({
  role: "analyst",
  setRole: () => {},
});

// Demo control (not auth): who is acting. Persisted to localStorage so it
// survives navigation. The role is sent with each governed action/approve.
export function RoleProvider({ children }: { children: React.ReactNode }) {
  const [role, setRoleState] = useState<Role>("analyst");

  useEffect(() => {
    const saved = localStorage.getItem("praheri.role");
    if (saved === "analyst" || saved === "mlro") setRoleState(saved);
  }, []);

  const setRole = (r: Role) => {
    setRoleState(r);
    localStorage.setItem("praheri.role", r);
  };

  return <RoleContext.Provider value={{ role, setRole }}>{children}</RoleContext.Provider>;
}

export function useRole() {
  return useContext(RoleContext);
}
