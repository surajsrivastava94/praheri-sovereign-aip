"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { DEMO_STEPS } from "@/lib/demoSteps";

type DemoState = {
  active: boolean;
  index: number; // 0-based into DEMO_STEPS
  start: () => void;
  stop: () => void;
  next: () => void;
  prev: () => void;
  restart: () => void;
};

const DemoContext = createContext<DemoState>({
  active: false,
  index: 0,
  start: () => {},
  stop: () => {},
  next: () => {},
  prev: () => {},
  restart: () => {},
});

// Guided-demo state, persisted to localStorage so it survives navigation between
// the routes each step points to.
export function DemoProvider({ children }: { children: React.ReactNode }) {
  const [active, setActive] = useState(false);
  const [index, setIndex] = useState(0);

  useEffect(() => {
    setActive(localStorage.getItem("praheri.demo.active") === "1");
    const i = parseInt(localStorage.getItem("praheri.demo.index") ?? "0", 10);
    if (!Number.isNaN(i)) setIndex(Math.min(Math.max(i, 0), DEMO_STEPS.length - 1));
  }, []);

  const persist = (a: boolean, i: number) => {
    localStorage.setItem("praheri.demo.active", a ? "1" : "0");
    localStorage.setItem("praheri.demo.index", String(i));
  };

  const start = () => { setActive(true); setIndex(0); persist(true, 0); };
  const stop = () => { setActive(false); persist(false, index); };
  const restart = () => { setIndex(0); persist(active, 0); };
  const next = () => setIndex((i) => { const n = Math.min(i + 1, DEMO_STEPS.length - 1); persist(active, n); return n; });
  const prev = () => setIndex((i) => { const n = Math.max(i - 1, 0); persist(active, n); return n; });

  return (
    <DemoContext.Provider value={{ active, index, start, stop, next, prev, restart }}>
      {children}
    </DemoContext.Provider>
  );
}

export function useDemo() {
  return useContext(DemoContext);
}
