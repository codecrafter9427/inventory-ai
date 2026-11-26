"use client";

import { AuthGate } from "@/components/AuthGate";
import { ComingSoon } from "@/components/ComingSoon";

export default function TransfersPage() {
  return (
    <AuthGate>
      <ComingSoon
        title="Stock transfers"
        description="Move stock between locations with initiated / in-transit / received states. Coming Soon."
      />
    </AuthGate>
  );
}
