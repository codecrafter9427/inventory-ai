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
        val productSku: String?,
        val productName: String?,
        val locationCode: String?,
        val locationName: String?,
        val quantity: String,
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
        val items = json.getJSONArray("items")
        buildList {
            for (i in 0 until items.length()) {
                val p = items.getJSONObject(i)
                add(
                    Product(
                        id = p.getString("id"),
                        sku = p.getString("sku"),
                        name = p.getString("name"),
                        barcode = if (p.isNull("barcode")) null else p.getString("barcode"),
                        sellingPrice = p.getString("selling_price"),
                        unitCode = if (p.isNull("unit_code")) null else p.getString("unit_code"),
                    ),
                )
            }
        }
    }

    suspend fun balancesForSku(sku: String): List<StockBalance> = withContext(Dispatchers.IO) {
        val q = java.net.URLEncoder.encode(sku, Charsets.UTF_8.name())
        val json = request("GET", "/stock/balances?page=1&page_size=40&q=$q", null, auth = true)
        val items = json.getJSONArray("items")
        parseBalances(items)
    }

    private fun JSONObject.nullableString(key: String): String? =
        if (isNull(key)) null else optString(key)

    private fun parseBalances(items: JSONArray): List<StockBalance> = buildList {
        for (i in 0 until items.length()) {
            val b = items.getJSONObject(i)
            add(
                StockBalance(
                    productSku = b.nullableString("product_sku"),
                    productName = b.nullableString("product_name"),
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
