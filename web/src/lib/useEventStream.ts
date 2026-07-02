"use client";

import { useCallback, useRef, useState } from "react";
import { DEMO, demoStream } from "@/lib/demoResolver";

// Minimal SSE consumer for the token stream. Native EventSource (GET only),
// served same-origin via the Next proxy. Handles named events: token, done, error.
// In DEMO mode there's no server, so we replay the cached narrative token-by-token
// on a timer — the typing animation is identical to the real Llama stream.
export function useTokenStream() {
  const [text, setText] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  const start = useCallback((url: string) => {
    esRef.current?.close();
    setText("");
    setError(null);
    setStreaming(true);

    if (DEMO) {
      demoStream(
        url,
        (t) => setText((prev) => prev + t),
        () => setStreaming(false),
      ).catch(() => {
        setError("demo stream error");
        setStreaming(false);
      });
      return;
    }

    const es = new EventSource(url);
    esRef.current = es;

    es.addEventListener("token", (e) => {
      const { t } = JSON.parse((e as MessageEvent).data);
      setText((prev) => prev + t);
    });
    es.addEventListener("done", () => {
      setStreaming(false);
      es.close();
    });
    es.addEventListener("error", (e) => {
      // Either a server "error" event or a transport drop.
      const data = (e as MessageEvent).data;
      if (data) {
        try {
          setError(JSON.parse(data).message);
        } catch {
          setError("stream error");
        }
      } else {
        setError("connection lost");
      }
      setStreaming(false);
      es.close();
    });
  }, []);

  return { text, streaming, error, start };
}
