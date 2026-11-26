import { API_BASE, clearSession, getToken } from "@/lib/auth";

export type ApiError = {
  error: { code: string; message: string; details?: unknown };
};

export class ApiRequestError extends Error {
  status: number;
  code: string;
  details?: unknown;

  constructor(status: number, code: string, message: string, details?: unknown) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (res.status === 401) {
    clearSession();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
    throw new ApiRequestError(401, "unauthorized", "Session expired");
  }

  if (res.status === 204) {
    return undefined as T;
  }

  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const err = data as ApiError | null;
    throw new ApiRequestError(
      res.status,
      err?.error?.code ?? "http_error",
      err?.error?.message ?? `Request failed (${res.status})`,
      err?.error?.details,
    );
  }
  return data as T;
}

export type Page<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export type Product = {
  id: string;
  sku: string;
  name: string;
  description: string | null;
  barcode: string | null;
  category_id: string | null;
  unit_id: string;
  cost: string;
  selling_price: string;
  reorder_point: string;
  is_active: boolean;
  category_name: string | null;
  unit_code: string | null;
};

export type Unit = { id: string; code: string; name: string };
export type Category = { id: string; name: string; description: string | null };

export type PurchaseOrderSummary = {
  id: string;
  po_number: string;
  status: string;
  supplier_name: string | null;
  location_name: string | null;
  ordered_at: string | null;
  line_count: number;
};

export type PurchaseOrderLine = {
  id: string;
  product_id: string;
  product_sku: string | null;
  product_name: string | null;
  quantity_ordered: string;
  quantity_received: string;
  quantity_remaining: string;
  unit_cost: string;
};

export type PurchaseOrderDetail = {
  id: string;
  po_number: string;
  status: string;
  supplier_name: string | null;
  location_id: string;
  location_name: string | null;
  notes: string | null;
  lines: PurchaseOrderLine[];
};

export type StockBalance = {
  id: string;
  product_sku: string | null;
  product_name: string | null;
  location_code: string | null;
  location_name: string | null;
  quantity: string;
  updated_at: string;
};

export type StockMovement = {
  id: string;
  product_sku: string | null;
  product_name: string | null;
  location_code: string | null;
  location_name: string | null;
  movement_type: string;
  quantity: string;
  balance_after: string;
  reason: string | null;
  created_at: string;
};
