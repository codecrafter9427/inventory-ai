"use client";

import { AuthGate } from "@/components/AuthGate";
import { ComingSoon } from "@/components/ComingSoon";

export default function ReportsPage() {
  return (
    <AuthGate>
      <ComingSoon
        title="Inventory reports"
        description="Stock-on-hand, low-stock, movement, valuation, and CSV export. Coming Soon."
      />
    </AuthGate>
  );
}
