package com.portfolio.inventoryai.ui

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.portfolio.inventoryai.ui.screens.ComingSoonScreen
import com.portfolio.inventoryai.ui.screens.HomeScreen
import com.portfolio.inventoryai.ui.screens.LoginScreen

@Composable
fun InventoryApp() {
    val navController = rememberNavController()
    var loggedIn by rememberSaveable { mutableStateOf(false) }
    var displayName by rememberSaveable { mutableStateOf("Demo User") }

    NavHost(
        navController = navController,
        startDestination = if (loggedIn) "home" else "login",
    ) {
        composable("login") {
            LoginScreen(
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
                    loggedIn = false
                    navController.navigate("login") {
                        popUpTo("home") { inclusive = true }
                    }
                },
            )
        }
        composable("products") {
            ComingSoonScreen(
                title = "Product search",
                detail = "Search and stock-by-location detail. Coming Soon.",
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
                detail = "Receiving workflow is not implemented in this scaffold.",
                onBack = { navController.popBackStack() },
            )
        }
        composable("count") {
            ComingSoonScreen(
                title = "Stock count",
                detail = "Offline draft counts and sync. Coming Soon.",
                onBack = { navController.popBackStack() },
            )
        }
        composable("transfer") {
            ComingSoonScreen(
                title = "Transfer",
                detail = "Source/destination transfer workflow. Coming Soon.",
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
