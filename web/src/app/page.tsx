"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

// Client-side redirect to the AML hero. A server redirect() can't be statically
// exported, so we bounce on mount — works in both dev and the static demo build.
export default function Home() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/aml");
  }, [router]);
  return <div className="p-8 text-muted text-sm">Loading console…</div>;
}
