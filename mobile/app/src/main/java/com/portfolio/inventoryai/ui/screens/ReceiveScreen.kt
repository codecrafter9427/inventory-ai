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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
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
import java.math.BigDecimal

private enum class ReceiveStep {
    ListPos,
    PickLine,
    Confirm,
    Success,
}

private data class ReceivableLine(
    val po: ApiClient.PurchaseOrderDetail,
    val line: ApiClient.PurchaseOrderLine,
)

@Composable
fun ReceiveScreen(
    api: ApiClient,
    productIdFilter: String? = null,
    productLabel: String? = null,
    onBack: () -> Unit,
    onOpenScan: (() -> Unit)? = null,
) {
    var step by remember { mutableStateOf(ReceiveStep.ListPos) }
    var loading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var receivablePos by remember { mutableStateOf<List<ApiClient.PurchaseOrderSummary>>(emptyList()) }
    var selectedPo by remember { mutableStateOf<ApiClient.PurchaseOrderDetail?>(null) }
    var filteredLines by remember { mutableStateOf<List<ReceivableLine>>(emptyList()) }
    var selectedLine by remember { mutableStateOf<ReceivableLine?>(null) }
    var qtyText by remember { mutableStateOf("") }
    var notes by remember { mutableStateOf("") }
    var submitting by remember { mutableStateOf(false) }
    var receiveResult by remember { mutableStateOf<ApiClient.ReceiveResult?>(null) }
    var movements by remember { mutableStateOf<List<ApiClient.StockMovement>>(emptyList()) }
    var balances by remember { mutableStateOf<List<ApiClient.StockBalance>>(emptyList()) }
    val scope = rememberCoroutineScope()

    fun remainingOf(line: ApiClient.PurchaseOrderLine): BigDecimal =
        runCatching { BigDecimal(line.quantityRemaining) }.getOrDefault(BigDecimal.ZERO)

    fun loadReceivablePos() {
        scope.launch {
            loading = true
            error = null
            try {
                if (productIdFilter != null) {
                    val summaries = api.listReceivablePurchaseOrders()
                    val matches = mutableListOf<ReceivableLine>()
                    for (summary in summaries) {
                        val detail = api.getPurchaseOrder(summary.id)
                        detail.lines
                            .filter { it.productId == productIdFilter && remainingOf(it) > BigDecimal.ZERO }
                            .forEach { matches += ReceivableLine(detail, it) }
                    }
                    filteredLines = matches
                    receivablePos = emptyList()
                    step = if (matches.isEmpty()) ReceiveStep.ListPos else ReceiveStep.PickLine
                } else {
                    receivablePos = api.listReceivablePurchaseOrders()
                    filteredLines = emptyList()
                    step = ReceiveStep.ListPos
                }
            } catch (e: ApiException) {
                error = e.message
                receivablePos = emptyList()
                filteredLines = emptyList()
            } catch (e: Exception) {
                error = e.message ?: "Failed to load purchase orders — is the API running?"
                receivablePos = emptyList()
                filteredLines = emptyList()
            } finally {
                loading = false
            }
        }
    }

    fun openPo(id: String) {
        scope.launch {
            loading = true
            error = null
            try {
                val detail = api.getPurchaseOrder(id)
                selectedPo = detail
                filteredLines = detail.lines
                    .filter { remainingOf(it) > BigDecimal.ZERO }
                    .map { ReceivableLine(detail, it) }
                step = ReceiveStep.PickLine
            } catch (e: Exception) {
                error = e.message ?: "Failed to load PO"
            } finally {
                loading = false
            }
        }
    }

    fun submitReceive() {
        val target = selectedLine ?: return
        val qty = runCatching { BigDecimal(qtyText.trim()) }.getOrNull()
        if (qty == null || qty <= BigDecimal.ZERO) {
            error = "Enter a quantity greater than zero"
            return
        }
        val remaining = remainingOf(target.line)
        if (qty > remaining) {
            error = "Quantity exceeds remaining ($remaining)"
            return
        }
        scope.launch {
            submitting = true
            error = null
            try {
                val result = api.receive(
                    purchaseOrderId = target.po.id,
                    lines = listOf(target.line.id to qty.stripTrailingZeros().toPlainString()),
                    discrepancyNotes = notes.trim().ifBlank { null },
                )
                receiveResult = result
                val productId = result.lines.firstOrNull()?.productId ?: target.line.productId
                movements = api.listMovements(
                    productId = productId,
                    locationId = result.locationId,
                    pageSize = 5,
                )
                val sku = target.line.productSku
                balances = if (sku != null) {
                    api.balancesForSku(sku, locationId = result.locationId)
                } else {
                    emptyList()
                }
                step = ReceiveStep.Success
            } catch (e: ApiException) {
                error = e.message
            } catch (e: Exception) {
                error = e.message ?: "Receive failed"
            } finally {
                submitting = false
            }
        }
    }

    LaunchedEffect(productIdFilter) {
        loadReceivablePos()
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
    ) {
        TextButton(onClick = {
            when (step) {
                ReceiveStep.ListPos, ReceiveStep.Success -> onBack()
                ReceiveStep.PickLine -> {
                    if (productIdFilter != null) onBack()
                    else {
                        selectedPo = null
                        selectedLine = null
                        step = ReceiveStep.ListPos
                    }
                }
                ReceiveStep.Confirm -> {
                    selectedLine = null
                    step = ReceiveStep.PickLine
                }
            }
        }) {
            Text("← Back")
        }
        Text(
            text = "Receive against PO",
            style = MaterialTheme.typography.headlineSmall,
            color = MaterialTheme.colorScheme.primary,
            modifier = Modifier.padding(top = 8.dp),
        )
        Text(
            text = when {
                productLabel != null -> "Filtered to $productLabel. Location comes from the PO."
                productIdFilter != null -> "Filtered to scanned product. Location comes from the PO."
                else -> "Select an ordered/partial PO, confirm qty and destination location, then post a receipt."
            },
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(top = 4.dp, bottom = 8.dp),
        )
        if (onOpenScan != null && step == ReceiveStep.ListPos && productIdFilter == null) {
            OutlinedButton(
                onClick = onOpenScan,
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 8.dp),
            ) {
                Text("Scan barcode instead")
            }
        }
        if (error != null) {
            Text(
                text = error!!,
                color = MaterialTheme.colorScheme.error,
                style = MaterialTheme.typography.bodySmall,
                modifier = Modifier.padding(bottom = 8.dp),
            )
        }
        if (loading) {
            CircularProgressIndicator(modifier = Modifier.padding(top = 16.dp))
        }

        when (step) {
            ReceiveStep.ListPos -> {
                if (!loading && productIdFilter != null && filteredLines.isEmpty()) {
                    Text(
                        text = "No receivable PO lines for this product. Try another barcode or pick a PO from Home → Receive.",
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                } else if (!loading && receivablePos.isEmpty() && productIdFilter == null) {
                    Text(
                        text = "No ordered or partially received purchase orders.",
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                } else if (productIdFilter == null) {
                    LazyColumn(
                        verticalArrangement = Arrangement.spacedBy(4.dp),
                        contentPadding = PaddingValues(bottom = 24.dp),
                        modifier = Modifier.weight(1f),
                    ) {
                        items(receivablePos, key = { it.id }) { po ->
                            Column(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .clickable { openPo(po.id) }
                                    .padding(vertical = 10.dp),
                            ) {
                                Text(po.poNumber, style = MaterialTheme.typography.labelLarge)
                                Text(
                                    "${po.status} · ${po.supplierName ?: "Supplier"} · ${po.locationName ?: po.locationId}",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                )
                                Text(
                                    "${po.lineCount} line(s)",
                                    style = MaterialTheme.typography.bodySmall,
                                )
                            }
                            HorizontalDivider()
                        }
                    }
                }
            }

            ReceiveStep.PickLine -> {
                LazyColumn(
                    verticalArrangement = Arrangement.spacedBy(4.dp),
                    contentPadding = PaddingValues(bottom = 24.dp),
                    modifier = Modifier.weight(1f),
                ) {
                    if (!loading && filteredLines.isEmpty()) {
                        item {
                            Text(
                                text = "No remaining quantity on this PO.",
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                    }
                    items(filteredLines, key = { "${it.po.id}-${it.line.id}" }) { item ->
                        Column(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable {
                                    selectedLine = item
                                    val rem = remainingOf(item.line)
                                    qtyText = rem.stripTrailingZeros().toPlainString()
                                    notes = ""
                                    error = null
                                    step = ReceiveStep.Confirm
                                }
                                .padding(vertical = 10.dp),
                        ) {
                            Text(
                                "${item.po.poNumber} · ${item.line.productSku ?: item.line.productId}",
                                style = MaterialTheme.typography.labelLarge,
                            )
                            Text(
                                item.line.productName ?: "Product",
                                style = MaterialTheme.typography.bodyMedium,
                            )
                            Text(
                                "Remaining ${item.line.quantityRemaining} of ${item.line.quantityOrdered} @ ${item.po.locationName ?: item.po.locationId}",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                        HorizontalDivider()
                    }
                }
            }

            ReceiveStep.Confirm -> {
                val item = selectedLine
                if (item == null) {
                    Text("No line selected.")
                } else {
                    Column(
                        modifier = Modifier
                            .weight(1f)
                            .verticalScroll(rememberScrollState()),
                        verticalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        Text("PO ${item.po.poNumber}", style = MaterialTheme.typography.titleMedium)
                        Text(
                            "${item.line.productSku} — ${item.line.productName}",
                            style = MaterialTheme.typography.bodyLarge,
                        )
                        Text(
                            "Destination location (from PO): ${item.po.locationName ?: item.po.locationId}",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.primary,
                        )
                        Text(
                            "Ordered ${item.line.quantityOrdered} · already received ${item.line.quantityReceived} · remaining ${item.line.quantityRemaining}",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                        OutlinedTextField(
                            value = qtyText,
                            onValueChange = { qtyText = it },
                            label = { Text("Quantity to receive") },
                            singleLine = true,
                            modifier = Modifier.fillMaxWidth(),
                        )
                        OutlinedTextField(
                            value = notes,
                            onValueChange = { notes = it },
                            label = { Text("Discrepancy notes (optional)") },
                            modifier = Modifier.fillMaxWidth(),
                        )
                        Button(
                            onClick = { submitReceive() },
                            enabled = !submitting,
                            modifier = Modifier.fillMaxWidth(),
                        ) {
                            Text(if (submitting) "Posting receipt…" else "Confirm receive")
                        }
                    }
                }
            }

            ReceiveStep.Success -> {
                val result = receiveResult
                Column(
                    modifier = Modifier
                        .weight(1f)
                        .verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    Text(
                        "Received against ${result?.poNumber ?: "PO"}",
                        style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.primary,
                    )
                    Text("PO status: ${result?.status}")
                    result?.lines?.forEach { line ->
                        Text(
                            "Qty ${line.quantityReceivedThisTime} · balance after ${line.balanceAfter}",
                            style = MaterialTheme.typography.bodyLarge,
                        )
                        Text(
                            "Movement id ${line.movementId}",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                    if (balances.isNotEmpty()) {
                        Text("Updated balance", style = MaterialTheme.typography.titleSmall)
                        balances.forEach { bal ->
                            Text(
                                "${bal.locationCode ?: bal.locationName}: ${bal.quantity}",
                                style = MaterialTheme.typography.bodyMedium,
                            )
                        }
                    }
                    if (movements.isNotEmpty()) {
                        Text("Recent movements", style = MaterialTheme.typography.titleSmall)
                        movements.forEach { m ->
                            Text(
                                "${m.movementType} ${m.quantity} → bal ${m.balanceAfter} (${m.locationCode ?: m.locationName})",
                                style = MaterialTheme.typography.bodySmall,
                            )
                            if (m.reason != null) {
                                Text(
                                    m.reason,
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                )
                            }
                        }
                    }
                    Button(
                        onClick = {
                            receiveResult = null
                            selectedLine = null
                            selectedPo = null
                            loadReceivablePos()
                        },
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Text("Receive another")
                    }
                    OutlinedButton(onClick = onBack, modifier = Modifier.fillMaxWidth()) {
                        Text("Done")
                    }
                }
            }
        }
    }
}
