"use client";

import { AuthGate } from "@/components/AuthGate";
import { ComingSoon } from "@/components/ComingSoon";

export default function StockPage() {
  return (
    <AuthGate>
      <ComingSoon
        title="Stock ledger"
        description="Immutable movements (opening, receive, dispatch, transfer, adjustment, return) and balances. Coming Soon."
      />
    </AuthGate>
  );
}
