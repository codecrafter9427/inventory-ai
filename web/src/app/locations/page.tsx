"use client";

import { AuthGate } from "@/components/AuthGate";
import { ComingSoon } from "@/components/ComingSoon";

export default function LocationsPage() {
  return (
    <AuthGate>
      <ComingSoon
        title="Warehouses & locations"
        description="Warehouses, bins/shelves, and location-scoped balances. Coming Soon."
      />
    </AuthGate>
  );
}
