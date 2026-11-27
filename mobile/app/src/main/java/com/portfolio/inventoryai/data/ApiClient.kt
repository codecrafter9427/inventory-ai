package com.portfolio.inventoryai.data

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL

/**
 * Thin HTTP client for Inventory AI demo APIs.
 * Default base URL targets the host machine from an Android emulator.
 * Change [baseUrl] for a physical device (LAN IP of your PC).
 */
class ApiClient(
    var baseUrl: String = "http://10.0.2.2:8000/api/v1",
) {
    var token: String? = null
        private set

    data class DemoUser(
        val accessToken: String,
        val displayName: String,
        val email: String,
        val role: String,
        val organizationId: String,
    )

    data class Product(
        val id: String,
        val sku: String,
        val name: String,
        val barcode: String?,
        val sellingPrice: String,
        val unitCode: String?,
    )

    data class StockBalance(
        val productId: String? = null,
        val productSku: String?,
        val productName: String?,
        val locationId: String? = null,
        val locationCode: String?,
        val locationName: String?,
        val quantity: String,
    )

    data class PurchaseOrderSummary(
        val id: String,
        val poNumber: String,
        val status: String,
        val supplierName: String?,
        val locationId: String,
        val locationName: String?,
        val lineCount: Int,
    )

    data class PurchaseOrderLine(
        val id: String,
        val productId: String,
        val productSku: String?,
        val productName: String?,
        val quantityOrdered: String,
        val quantityReceived: String,
        val quantityRemaining: String,
        val unitCost: String,
    )

    data class PurchaseOrderDetail(
        val id: String,
        val poNumber: String,
        val status: String,
        val supplierName: String?,
        val locationId: String,
        val locationName: String?,
        val lines: List<PurchaseOrderLine>,
    )

    data class ReceiveLineResult(
        val purchaseOrderLineId: String,
        val productId: String,
        val quantityReceivedThisTime: String,
        val quantityReceivedTotal: String,
        val quantityOrdered: String,
        val balanceAfter: String,
        val movementId: String,
    )

    data class ReceiveResult(
        val purchaseOrderId: String,
        val poNumber: String,
        val status: String,
        val locationId: String,
        val discrepancyNotes: String?,
        val lines: List<ReceiveLineResult>,
    )

    data class StockMovement(
        val id: String,
        val productSku: String?,
        val productName: String?,
        val locationCode: String?,
        val locationName: String?,
        val movementType: String,
        val quantity: String,
        val balanceAfter: String,
        val referenceType: String?,
        val reason: String?,
        val createdAt: String,
    )

    suspend fun demoLogin(email: String, password: String): DemoUser = withContext(Dispatchers.IO) {
        val body = JSONObject()
            .put("email", email)
            .put("password", password)
            .toString()
        val json = request("POST", "/auth/demo-login", body, auth = false)
        val user = DemoUser(
            accessToken = json.getString("access_token"),
            displayName = json.getString("display_name"),
            email = json.getString("email"),
            role = json.getString("role"),
            organizationId = json.getString("organization_id"),
        )
        token = user.accessToken
        user
    }

    fun clearSession() {
        token = null
    }

    suspend fun searchProducts(query: String): List<Product> = withContext(Dispatchers.IO) {
        val q = java.net.URLEncoder.encode(query.trim(), Charsets.UTF_8.name())
        val path = if (query.isBlank()) {
            "/products?page=1&page_size=40"
        } else {
            "/products?page=1&page_size=40&q=$q"
        }
        val json = request("GET", path, null, auth = true)
        parseProducts(json.getJSONArray("items"))
    }

    /**
     * Resolve a scanned barcode: prefer exact barcode match, then fall back to first search hit.
     */
    suspend fun findProductByBarcode(barcode: String): Product? {
        val trimmed = barcode.trim()
        if (trimmed.isEmpty()) return null
        val results = searchProducts(trimmed)
        return results.firstOrNull { it.barcode?.equals(trimmed, ignoreCase = true) == true }
            ?: results.firstOrNull { it.sku.equals(trimmed, ignoreCase = true) }
            ?: results.firstOrNull()
    }

    suspend fun balancesForSku(sku: String, locationId: String? = null): List<StockBalance> =
        withContext(Dispatchers.IO) {
            val q = java.net.URLEncoder.encode(sku, Charsets.UTF_8.name())
            val loc = locationId?.let {
                "&location_id=${java.net.URLEncoder.encode(it, Charsets.UTF_8.name())}"
            }.orEmpty()
            val json = request("GET", "/stock/balances?page=1&page_size=40&q=$q$loc", null, auth = true)
            parseBalances(json.getJSONArray("items"))
        }

    suspend fun listPurchaseOrders(status: String? = null): List<PurchaseOrderSummary> =
        withContext(Dispatchers.IO) {
            val statusQs = status?.let {
                "&status=${java.net.URLEncoder.encode(it, Charsets.UTF_8.name())}"
            }.orEmpty()
            val json = request(
                "GET",
                "/purchase-orders?page=1&page_size=50$statusQs",
                null,
                auth = true,
            )
            val items = json.getJSONArray("items")
            buildList {
                for (i in 0 until items.length()) {
                    val p = items.getJSONObject(i)
                    add(
                        PurchaseOrderSummary(
                            id = p.getString("id"),
                            poNumber = p.getString("po_number"),
                            status = p.getString("status"),
                            supplierName = p.nullableString("supplier_name"),
                            locationId = p.getString("location_id"),
                            locationName = p.nullableString("location_name"),
                            lineCount = p.optInt("line_count", 0),
                        ),
                    )
                }
            }
        }

    suspend fun listReceivablePurchaseOrders(): List<PurchaseOrderSummary> {
        val ordered = listPurchaseOrders(status = "ordered")
        val partial = listPurchaseOrders(status = "partially_received")
        return (ordered + partial).distinctBy { it.id }.sortedByDescending { it.poNumber }
    }

    suspend fun getPurchaseOrder(id: String): PurchaseOrderDetail = withContext(Dispatchers.IO) {
        val json = request("GET", "/purchase-orders/$id", null, auth = true)
        PurchaseOrderDetail(
            id = json.getString("id"),
            poNumber = json.getString("po_number"),
            status = json.getString("status"),
            supplierName = json.nullableString("supplier_name"),
            locationId = json.getString("location_id"),
            locationName = json.nullableString("location_name"),
            lines = parsePoLines(json.optJSONArray("lines") ?: JSONArray()),
        )
    }

    suspend fun receive(
        purchaseOrderId: String,
        lines: List<Pair<String, String>>,
        discrepancyNotes: String? = null,
    ): ReceiveResult = withContext(Dispatchers.IO) {
        val lineArr = JSONArray()
        lines.forEach { (lineId, qty) ->
            lineArr.put(
                JSONObject()
                    .put("purchase_order_line_id", lineId)
                    .put("quantity", qty),
            )
        }
        val body = JSONObject()
            .put("purchase_order_id", purchaseOrderId)
            .put("lines", lineArr)
        if (!discrepancyNotes.isNullOrBlank()) {
            body.put("discrepancy_notes", discrepancyNotes.trim())
        } else {
            body.put("discrepancy_notes", JSONObject.NULL)
        }
        val json = request("POST", "/receipts", body.toString(), auth = true)
        parseReceiveResult(json)
    }

    suspend fun listMovements(
        productId: String? = null,
        locationId: String? = null,
        pageSize: Int = 20,
    ): List<StockMovement> = withContext(Dispatchers.IO) {
        val parts = mutableListOf("page=1", "page_size=$pageSize")
        if (productId != null) {
            parts += "product_id=${java.net.URLEncoder.encode(productId, Charsets.UTF_8.name())}"
        }
        if (locationId != null) {
            parts += "location_id=${java.net.URLEncoder.encode(locationId, Charsets.UTF_8.name())}"
        }
        val json = request("GET", "/stock/movements?${parts.joinToString("&")}", null, auth = true)
        parseMovements(json.getJSONArray("items"))
    }

    private fun parseProducts(items: JSONArray): List<Product> = buildList {
        for (i in 0 until items.length()) {
            val p = items.getJSONObject(i)
            add(
                Product(
                    id = p.getString("id"),
                    sku = p.getString("sku"),
                    name = p.getString("name"),
                    barcode = p.nullableString("barcode"),
                    sellingPrice = p.getString("selling_price"),
                    unitCode = p.nullableString("unit_code"),
                ),
            )
        }
    }

    private fun parsePoLines(items: JSONArray): List<PurchaseOrderLine> = buildList {
        for (i in 0 until items.length()) {
            val ln = items.getJSONObject(i)
            add(
                PurchaseOrderLine(
                    id = ln.getString("id"),
                    productId = ln.getString("product_id"),
                    productSku = ln.nullableString("product_sku"),
                    productName = ln.nullableString("product_name"),
                    quantityOrdered = ln.getString("quantity_ordered"),
                    quantityReceived = ln.getString("quantity_received"),
                    quantityRemaining = ln.optString("quantity_remaining", "0"),
                    unitCost = ln.getString("unit_cost"),
                ),
            )
        }
    }

    private fun parseReceiveResult(json: JSONObject): ReceiveResult {
        val linesJson = json.optJSONArray("lines") ?: JSONArray()
        val lines = buildList {
            for (i in 0 until linesJson.length()) {
                val ln = linesJson.getJSONObject(i)
                add(
                    ReceiveLineResult(
                        purchaseOrderLineId = ln.getString("purchase_order_line_id"),
                        productId = ln.getString("product_id"),
                        quantityReceivedThisTime = ln.getString("quantity_received_this_time"),
                        quantityReceivedTotal = ln.getString("quantity_received_total"),
                        quantityOrdered = ln.getString("quantity_ordered"),
                        balanceAfter = ln.getString("balance_after"),
                        movementId = ln.getString("movement_id"),
                    ),
                )
            }
        }
        return ReceiveResult(
            purchaseOrderId = json.getString("purchase_order_id"),
            poNumber = json.getString("po_number"),
            status = json.getString("status"),
            locationId = json.getString("location_id"),
            discrepancyNotes = json.nullableString("discrepancy_notes"),
            lines = lines,
        )
    }

    private fun parseMovements(items: JSONArray): List<StockMovement> = buildList {
        for (i in 0 until items.length()) {
            val m = items.getJSONObject(i)
            add(
                StockMovement(
                    id = m.getString("id"),
                    productSku = m.nullableString("product_sku"),
                    productName = m.nullableString("product_name"),
                    locationCode = m.nullableString("location_code"),
                    locationName = m.nullableString("location_name"),
                    movementType = m.getString("movement_type"),
                    quantity = m.getString("quantity"),
                    balanceAfter = m.getString("balance_after"),
                    referenceType = m.nullableString("reference_type"),
                    reason = m.nullableString("reason"),
                    createdAt = m.getString("created_at"),
                ),
            )
        }
    }

    private fun JSONObject.nullableString(key: String): String? =
        if (isNull(key)) null else optString(key).takeIf { it.isNotBlank() }

    private fun parseBalances(items: JSONArray): List<StockBalance> = buildList {
        for (i in 0 until items.length()) {
            val b = items.getJSONObject(i)
            add(
                StockBalance(
                    productId = b.nullableString("product_id"),
                    productSku = b.nullableString("product_sku"),
                    productName = b.nullableString("product_name"),
                    locationId = b.nullableString("location_id"),
                    locationCode = b.nullableString("location_code"),
                    locationName = b.nullableString("location_name"),
                    quantity = b.getString("quantity"),
                ),
            )
        }
    }

    private fun request(
        method: String,
        path: String,
        body: String?,
        auth: Boolean,
    ): JSONObject {
        val url = URL(baseUrl.trimEnd('/') + path)
        val conn = (url.openConnection() as HttpURLConnection).apply {
            requestMethod = method
            connectTimeout = 12_000
            readTimeout = 20_000
            setRequestProperty("Accept", "application/json")
            if (body != null) {
                doOutput = true
                setRequestProperty("Content-Type", "application/json")
            }
            if (auth) {
                val t = token ?: throw ApiException(401, "unauthorized", "Not signed in")
                setRequestProperty("Authorization", "Bearer $t")
            }
        }
        try {
            if (body != null) {
                OutputStreamWriter(conn.outputStream, Charsets.UTF_8).use { it.write(body) }
            }
            val code = conn.responseCode
            val stream = if (code in 200..299) conn.inputStream else conn.errorStream
            val text = stream?.let { BufferedReader(InputStreamReader(it, Charsets.UTF_8)).readText() }.orEmpty()
            if (code !in 200..299) {
                val err = runCatching { JSONObject(text) }.getOrNull()
                val errorObj = err?.optJSONObject("error")
                throw ApiException(
                    code,
                    errorObj?.optString("code") ?: "http_error",
                    errorObj?.optString("message") ?: "Request failed ($code)",
                )
            }
            return if (text.isBlank()) JSONObject() else JSONObject(text)
        } finally {
            conn.disconnect()
        }
    }
}

class ApiException(
    val status: Int,
    val code: String,
    override val message: String,
) : Exception(message)
