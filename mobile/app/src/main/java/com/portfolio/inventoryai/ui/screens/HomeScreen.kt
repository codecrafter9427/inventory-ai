package com.portfolio.inventoryai.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

private data class Shortcut(val route: String, val label: String, val enabled: Boolean)

private val shortcuts = listOf(
    Shortcut("products", "Product search", enabled = true),
    Shortcut("scan", "Scan barcode", enabled = false),
    Shortcut("receive", "Receive PO", enabled = false),
    Shortcut("count", "Stock count", enabled = false),
    Shortcut("transfer", "Transfer", enabled = false),
    Shortcut("adjust", "Quick adjustment", enabled = false),
)

@Composable
fun HomeScreen(
    displayName: String,
    onOpenShortcut: (String) -> Unit,
    onSignOut: () -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
    ) {
        Text(
            text = "Inventory AI",
            style = MaterialTheme.typography.headlineSmall,
            color = MaterialTheme.colorScheme.primary,
        )
        Text(
            text = "Hello, $displayName",
            style = MaterialTheme.typography.bodyLarge,
            modifier = Modifier.padding(top = 4.dp),
        )
        Text(
            text = "Product search calls the same backend as web. Other workflows stay Coming Soon (disabled).",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(top = 8.dp, bottom = 16.dp),
        )
        LazyColumn(
            verticalArrangement = Arrangement.spacedBy(10.dp),
            contentPadding = PaddingValues(bottom = 24.dp),
            modifier = Modifier.weight(1f),
        ) {
            items(shortcuts) { item ->
                if (item.enabled) {
                    Button(
                        onClick = { onOpenShortcut(item.route) },
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Text(item.label)
                    }
                } else {
                    OutlinedButton(
                        onClick = { },
                        enabled = false,
                        modifier = Modifier.fillMaxWidth(),
                        colors = ButtonDefaults.outlinedButtonColors(
                            disabledContentColor = MaterialTheme.colorScheme.onSurfaceVariant,
                        ),
                    ) {
                        Text("${item.label} — Coming Soon")
                    }
                }
            }
        }
        TextButton(onClick = onSignOut) {
            Text("Sign out")
        }
    }
}
