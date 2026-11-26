"use client";

import { AuthGate } from "@/components/AuthGate";
import { ComingSoon } from "@/components/ComingSoon";

export default function SuppliersPage() {
  return (
    <AuthGate>
      <ComingSoon
        title="Suppliers"
        description="Supplier directory for purchasing and lead-time inputs to Stockout Radar. Coming Soon."
      />
    </AuthGate>
  );
}
