package com.portfolio.inventoryai

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import com.portfolio.inventoryai.ui.InventoryApp
import com.portfolio.inventoryai.ui.theme.InventoryAITheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            InventoryAITheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    InventoryApp()
                }
            }
        }
    }
}
