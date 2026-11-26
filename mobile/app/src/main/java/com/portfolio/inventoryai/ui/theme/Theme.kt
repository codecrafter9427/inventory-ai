package com.portfolio.inventoryai.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val Green = Color(0xFF3DBA7A)
private val Ink = Color(0xFFE8F2EC)
private val Bg = Color(0xFF0F1C17)
private val SurfaceBg = Color(0xFF1C3229)
private val Muted = Color(0xFF9BB5A8)

private val ColorScheme = darkColorScheme(
    primary = Green,
    onPrimary = Color.White,
    background = Bg,
    onBackground = Ink,
    surface = SurfaceBg,
    onSurface = Ink,
    onSurfaceVariant = Muted,
)

@Composable
fun InventoryAITheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = ColorScheme,
        content = content,
    )
}
