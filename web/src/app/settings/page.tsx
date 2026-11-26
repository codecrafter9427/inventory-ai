"use client";

import { AuthGate } from "@/components/AuthGate";
import { ComingSoon } from "@/components/ComingSoon";

export default function SettingsPage() {
  return (
    <AuthGate>
      <ComingSoon
        title="Settings"
        description="Organization, roles, units, and reorder defaults. Coming Soon."
      />
    </AuthGate>
  );
}
