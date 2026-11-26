"use client";

import { AuthGate } from "@/components/AuthGate";
import { ComingSoon } from "@/components/ComingSoon";

export default function ProductsPage() {
  return (
    <AuthGate>
      <ComingSoon
        title="Product catalog"
        description="SKU, barcode, category, unit, cost, selling price, reorder point, and active state. Create/search is not wired in this scaffold."
      />
    </AuthGate>
  );
}
