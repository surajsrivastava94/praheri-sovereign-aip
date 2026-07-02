// Enumerates the sector keys so the static export can prerender each /sectors/*
// route. The page itself is a client component (reads params via use()); a layout
// is the right place for generateStaticParams. Keys mirror the engine registry.
export function generateStaticParams() {
  return [
    { key: "insurance_siu" },
    { key: "lending_ews" },
    { key: "wealth" },
    { key: "corporate" },
    { key: "procurement" },
  ];
}

export default function SectorLayout({ children }: { children: React.ReactNode }) {
  return children;
}
