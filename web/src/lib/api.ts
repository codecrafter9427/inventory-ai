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

export type Location = {
  id: string;
  code: string;
  name: string;
  address: string | null;
  bin_shelf_notes: string | null;
};

export type DashboardSummary = {
  generated_at: string;
  stock_value: string;
  low_stock_items: number;
  out_of_stock_items: number;
  pending_purchase_orders: number;
  recent_movement_count: number;
  product_count: number;
  location_count: number;
};

export type InventoryReport = {
  generated_at: string;
  stock_value: string;
  balance_rows: number;
  low_stock_items: number;
  out_of_stock_items: number;
  pending_purchase_orders: number;
  recent_movement_count: number;
  stock_on_hand: {
    sku: string;
    name: string;
    location_code: string;
    location_name: string;
    quantity: string;
    unit_cost: string;
    extended_value: string;
    reorder_point: string;
    is_low_stock: boolean;
  }[];
  recent_movements: {
    id: string;
    created_at: string;
    movement_type: string;
    sku: string | null;
    product_name: string | null;
    location_code: string | null;
    quantity: string;
    balance_after: string;
  }[];
};

export type TransferSummary = {
  id: string;
  status: string;
  source_location_code: string | null;
  source_location_name: string | null;
  destination_location_code: string | null;
  destination_location_name: string | null;
  line_count: number;
  notes: string | null;
  created_at: string;
};

export type TransferDetail = TransferSummary & {
  source_location_id: string;
  destination_location_id: string;
  lines: {
    id: string;
    product_id: string;
    product_sku: string | null;
    product_name: string | null;
    quantity: string;
  }[];
};

export type CountSummary = {
  id: string;
  status: string;
  location_code: string | null;
  location_name: string | null;
  line_count: number;
  notes: string | null;
  created_at: string;
  approved_at: string | null;
};

export type CountDetail = CountSummary & {
  location_id: string;
  lines: {
    id: string;
    product_id: string;
    product_sku: string | null;
    product_name: string | null;
    expected_quantity: string;
    counted_quantity: string;
    variance: string;
    variance_reason: string | null;
  }[];
};

/** Download a CSV report using the current session token. */
export async function downloadCsv(path: string, filename: string): Promise<void> {
  const token = getToken();
  const headers = new Headers();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const res = await fetch(`${API_BASE}${path}`, { headers });
  if (res.status === 401) {
    clearSession();
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new ApiRequestError(401, "unauthorized", "Session expired");
  }
  if (!res.ok) {
    throw new ApiRequestError(res.status, "http_error", `CSV export failed (${res.status})`);
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
