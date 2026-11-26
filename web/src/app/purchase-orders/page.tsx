"use client";

import { AuthGate } from "@/components/AuthGate";
import { ComingSoon } from "@/components/ComingSoon";

export default function PurchaseOrdersPage() {
  return (
    <AuthGate>
      <ComingSoon
        title="Purchase orders"
        description="Draft → ordered → partially received → received / cancelled, plus receiving with discrepancy notes. Coming Soon."
      />
    </AuthGate>
  );
}
