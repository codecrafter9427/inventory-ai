"use client";

import { AuthGate } from "@/components/AuthGate";
import { ComingSoon } from "@/components/ComingSoon";

export default function CountsPage() {
  return (
    <AuthGate>
      <ComingSoon
        title="Stock counts"
        description="Count sessions with expected vs counted quantity, variance review, and approval. Coming Soon."
      />
    </AuthGate>
  );
}
