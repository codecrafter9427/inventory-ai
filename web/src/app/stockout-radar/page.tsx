"use client";

import { AuthGate } from "@/components/AuthGate";
import { ComingSoon } from "@/components/ComingSoon";

export default function StockoutRadarPage() {
  return (
    <AuthGate>
      <ComingSoon
        title="Stockout Radar"
        description="Transparent risk score from on-hand, average daily movement, lead time, and safety stock. Formula UI Coming Soon; demo API stub exists at POST /api/v1/ai/stockout-radar."
      />
    </AuthGate>
  );
}
