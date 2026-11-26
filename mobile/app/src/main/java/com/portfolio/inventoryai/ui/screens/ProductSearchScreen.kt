package com.portfolio.inventoryai.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.portfolio.inventoryai.data.ApiClient
import com.portfolio.inventoryai.data.ApiException
import kotlinx.coroutines.launch

@Composable
fun ProductSearchScreen(
    api: ApiClient,
    onBack: () -> Unit,
) {
    var query by remember { mutableStateOf("") }
    var loading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var products by remember { mutableStateOf<List<ApiClient.Product>>(emptyList()) }
    var selected by remember { mutableStateOf<ApiClient.Product?>(null) }
    var balances by remember { mutableStateOf<List<ApiClient.StockBalance>>(emptyList()) }
    val scope = rememberCoroutineScope()

    fun search(q: String) {
        scope.launch {
            loading = true
            error = null
            selected = null
            balances = emptyList()
            try {
                products = api.searchProducts(q)
            } catch (e: ApiException) {
                error = e.message
                products = emptyList()
            } catch (e: Exception) {
                error = e.message ?: "Search failed — is the API running?"
                products = emptyList()
            } finally {
                loading = false
            }
        }
    }

    LaunchedEffect(Unit) {
        search("")
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
    ) {
        TextButton(onClick = onBack) {
            Text("← Back")
        }
        Text(
            text = "Product search",
            style = MaterialTheme.typography.headlineSmall,
            color = MaterialTheme.colorScheme.primary,
            modifier = Modifier.padding(top = 8.dp),
        )
        Text(
            text = "Same /products and /stock/balances APIs as web. Emulator uses 10.0.2.2:8000.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(top = 4.dp, bottom = 12.dp),
        )
        OutlinedTextField(
            value = query,
            onValueChange = { query = it },
            label = { Text("SKU, name, or barcode") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
        )
        Button(
            onClick = { search(query) },
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 8.dp),
            enabled = !loading,
        ) {
            Text(if (loading) "Searching…" else "Search")
        }
        if (error != null) {
            Text(
                text = error!!,
                color = MaterialTheme.colorScheme.error,
                style = MaterialTheme.typography.bodySmall,
                modifier = Modifier.padding(top = 8.dp),
            )
        }
        if (loading) {
            CircularProgressIndicator(modifier = Modifier.padding(top = 16.dp))
        }
        LazyColumn(
            verticalArrangement = Arrangement.spacedBy(4.dp),
            contentPadding = PaddingValues(top = 12.dp, bottom = 24.dp),
            modifier = Modifier.weight(1f),
        ) {
            if (!loading && products.isEmpty() && error == null) {
                item {
                    Text(
                        text = "No products match.",
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
            items(products, key = { it.id }) { product ->
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable {
                            selected = product
                            scope.launch {
                                try {
                                    balances = api.balancesForSku(product.sku)
                                } catch (e: Exception) {
                                    balances = emptyList()
                                    error = e.message
                                }
                            }
                        }
                        .padding(vertical = 8.dp),
                ) {
                    Text(text = product.sku, style = MaterialTheme.typography.labelLarge)
                    Text(text = product.name, style = MaterialTheme.typography.bodyMedium)
                    Text(
                        text = "Price ${product.sellingPrice} · ${product.unitCode ?: "unit"}",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
                HorizontalDivider()
            }
            selected?.let { product ->
                item {
                    Text(
                        text = "Stock for ${product.sku}",
                        style = MaterialTheme.typography.titleMedium,
                        modifier = Modifier.padding(top = 16.dp, bottom = 8.dp),
                    )
                    if (balances.isEmpty()) {
                        Text(
                            text = "No balances for this SKU at any location.",
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    } else {
                        balances.forEach { bal ->
                            Text(
                                text = "${bal.locationCode} — ${bal.locationName}: ${bal.quantity}",
                                style = MaterialTheme.typography.bodyMedium,
                                modifier = Modifier.padding(bottom = 4.dp),
                            )
                        }
                    }
                }
            }
        }
    }
}
