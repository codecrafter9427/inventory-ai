package com.portfolio.inventoryai.ui

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.portfolio.inventoryai.data.ApiClient
import com.portfolio.inventoryai.ui.screens.ComingSoonScreen
import com.portfolio.inventoryai.ui.screens.HomeScreen
import com.portfolio.inventoryai.ui.screens.LoginScreen
import com.portfolio.inventoryai.ui.screens.ProductSearchScreen

@Composable
fun InventoryApp() {
    val navController = rememberNavController()
    val api = remember { ApiClient() }
    var loggedIn by rememberSaveable { mutableStateOf(false) }
    var displayName by rememberSaveable { mutableStateOf("Demo User") }

    NavHost(
        navController = navController,
        startDestination = if (loggedIn) "home" else "login",
    ) {
        composable("login") {
            LoginScreen(
                api = api,
                onDemoLogin = { name ->
                    displayName = name
                    loggedIn = true
                    navController.navigate("home") {
                        popUpTo("login") { inclusive = true }
                    }
                },
            )
        }
        composable("home") {
            HomeScreen(
                displayName = displayName,
                onOpenShortcut = { route -> navController.navigate(route) },
                onSignOut = {
                    api.clearSession()
                    loggedIn = false
                    navController.navigate("login") {
                        popUpTo("home") { inclusive = true }
                    }
                },
            )
        }
        composable("products") {
            ProductSearchScreen(
                api = api,
                onBack = { navController.popBackStack() },
            )
        }
        composable("scan") {
            ComingSoonScreen(
                title = "Barcode scan",
                detail = "ML Kit barcode scanning with manual search fallback. Coming Soon.",
                onBack = { navController.popBackStack() },
            )
        }
        composable("receive") {
            ComingSoonScreen(
                title = "Receive against PO",
                detail = "Use the web Purchase orders screen for receiving in this milestone.",
                onBack = { navController.popBackStack() },
            )
        }
        composable("count") {
            ComingSoonScreen(
                title = "Stock count",
                detail = "Offline draft counts and sync. Coming Soon. Web has a thin approval slice.",
                onBack = { navController.popBackStack() },
            )
        }
        composable("transfer") {
            ComingSoonScreen(
                title = "Transfer",
                detail = "Mobile transfer UI Coming Soon. Web transfers slice is available.",
                onBack = { navController.popBackStack() },
            )
        }
        composable("adjust") {
            ComingSoonScreen(
                title = "Quick adjustment",
                detail = "Adjustment with mandatory reason. Coming Soon.",
                onBack = { navController.popBackStack() },
            )
        }
    }
}
