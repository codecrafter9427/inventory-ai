package com.portfolio.inventoryai.ui.screens

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.LocalLifecycleOwner
import com.google.mlkit.vision.barcode.BarcodeScanning
import com.google.mlkit.vision.common.InputImage
import com.portfolio.inventoryai.data.ApiClient
import com.portfolio.inventoryai.data.ApiException
import kotlinx.coroutines.launch
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicBoolean

@Composable
fun BarcodeScanScreen(
    api: ApiClient,
    onBack: () -> Unit,
    onProductReady: (productId: String, label: String) -> Unit,
    onManualReceive: () -> Unit,
) {
    val context = LocalContext.current
    var hasCameraPermission by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) ==
                PackageManager.PERMISSION_GRANTED,
        )
    }
    var permissionAsked by remember { mutableStateOf(false) }
    var useManual by remember { mutableStateOf(false) }
    var manualQuery by remember { mutableStateOf("") }
    var loading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()
    val handled = remember { AtomicBoolean(false) }

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission(),
    ) { granted ->
        permissionAsked = true
        hasCameraPermission = granted
        if (!granted) {
            useManual = true
            error = "Camera permission denied — enter barcode or SKU manually."
        }
    }

    LaunchedEffect(Unit) {
        if (!hasCameraPermission && !permissionAsked) {
            permissionLauncher.launch(Manifest.permission.CAMERA)
        }
    }

    fun resolveBarcode(raw: String) {
        if (raw.isBlank()) {
            error = "Enter a barcode or SKU"
            return
        }
        if (!handled.compareAndSet(false, true)) {
            return
        }
        scope.launch {
            loading = true
            error = null
            try {
                val product = api.findProductByBarcode(raw)
                if (product == null) {
                    error = "No product matched \"$raw\". Try another code or manual search."
                    handled.set(false)
                } else {
                    onProductReady(product.id, "${product.sku} — ${product.name}")
                }
            } catch (e: ApiException) {
                error = e.message
                handled.set(false)
            } catch (e: Exception) {
                error = e.message ?: "Lookup failed — is the API running?"
                handled.set(false)
            } finally {
                loading = false
            }
        }
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
            text = "Barcode scan",
            style = MaterialTheme.typography.headlineSmall,
            color = MaterialTheme.colorScheme.primary,
            modifier = Modifier.padding(top = 8.dp),
        )
        Text(
            text = "ML Kit on-device scan (free). Seeded barcodes look like 8901000…. Deny camera to use manual entry.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(top = 4.dp, bottom = 12.dp),
        )
        if (error != null) {
            Text(
                text = error!!,
                color = MaterialTheme.colorScheme.error,
                style = MaterialTheme.typography.bodySmall,
                modifier = Modifier.padding(bottom = 8.dp),
            )
        }

        if (hasCameraPermission && !useManual) {
            Box(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth(),
            ) {
                CameraBarcodePreview(
                    enabled = !loading,
                    onBarcode = { value ->
                        if (!loading) resolveBarcode(value)
                    },
                )
                if (loading) {
                    CircularProgressIndicator(modifier = Modifier.align(Alignment.Center))
                }
            }
            OutlinedButton(
                onClick = {
                    useManual = true
                    handled.set(false)
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 12.dp),
            ) {
                Text("Enter barcode manually")
            }
        } else {
            Column(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                if (!hasCameraPermission) {
                    Text(
                        text = "Camera unavailable. Manual search uses the same /products API.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    OutlinedButton(
                        onClick = {
                            permissionAsked = false
                            permissionLauncher.launch(Manifest.permission.CAMERA)
                        },
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Text("Retry camera permission")
                    }
                }
                OutlinedTextField(
                    value = manualQuery,
                    onValueChange = { manualQuery = it },
                    label = { Text("Barcode, SKU, or name") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
                Button(
                    onClick = { resolveBarcode(manualQuery.trim()) },
                    enabled = !loading,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text(if (loading) "Looking up…" else "Find product")
                }
                if (hasCameraPermission) {
                    OutlinedButton(
                        onClick = {
                            useManual = false
                            handled.set(false)
                            error = null
                        },
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Text("Back to camera")
                    }
                }
            }
        }

        OutlinedButton(
            onClick = onManualReceive,
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 8.dp),
        ) {
            Text("Skip to Receive (pick PO)")
        }
    }
}

@Composable
private fun CameraBarcodePreview(
    enabled: Boolean,
    onBarcode: (String) -> Unit,
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val analysisExecutor = remember { Executors.newSingleThreadExecutor() }
    val scanner = remember { BarcodeScanning.getClient() }
    val fired = remember { AtomicBoolean(false) }
    val enabledFlag = remember { AtomicBoolean(enabled) }
    val latestOnBarcode by rememberUpdatedState(onBarcode)
    val previewView = remember {
        PreviewView(context).apply {
            scaleType = PreviewView.ScaleType.FILL_CENTER
            implementationMode = PreviewView.ImplementationMode.COMPATIBLE
        }
    }

    LaunchedEffect(enabled) {
        enabledFlag.set(enabled)
        if (enabled) fired.set(false)
    }

    DisposableEffect(lifecycleOwner) {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(context)
        val mainExecutor = ContextCompat.getMainExecutor(context)
        var unbound = false

        val listener = Runnable {
            if (unbound) return@Runnable
            try {
                val cameraProvider = cameraProviderFuture.get()
                val preview = Preview.Builder().build().also {
                    it.surfaceProvider = previewView.surfaceProvider
                }
                @Suppress("DEPRECATION")
                val analysis = ImageAnalysis.Builder()
                    .setTargetResolution(android.util.Size(1280, 720))
                    .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                    .build()
                analysis.setAnalyzer(analysisExecutor) { imageProxy ->
                    if (!enabledFlag.get() || fired.get()) {
                        imageProxy.close()
                        return@setAnalyzer
                    }
                    val mediaImage = imageProxy.image
                    if (mediaImage == null) {
                        imageProxy.close()
                        return@setAnalyzer
                    }
                    val image = InputImage.fromMediaImage(
                        mediaImage,
                        imageProxy.imageInfo.rotationDegrees,
                    )
                    scanner.process(image)
                        .addOnSuccessListener { barcodes ->
                            val value = barcodes
                                .asSequence()
                                .mapNotNull { it.rawValue }
                                .firstOrNull { it.isNotBlank() }
                            if (value != null && fired.compareAndSet(false, true)) {
                                latestOnBarcode(value)
                            }
                        }
                        .addOnCompleteListener {
                            imageProxy.close()
                        }
                }
                cameraProvider.unbindAll()
                cameraProvider.bindToLifecycle(
                    lifecycleOwner,
                    CameraSelector.DEFAULT_BACK_CAMERA,
                    preview,
                    analysis,
                )
            } catch (_: Exception) {
                // Preview bind can fail on some emulators; manual fallback covers this.
            }
        }
        cameraProviderFuture.addListener(listener, mainExecutor)

        onDispose {
            unbound = true
            runCatching {
                ProcessCameraProvider.getInstance(context).get().unbindAll()
            }
            analysisExecutor.shutdown()
            scanner.close()
        }
    }

    AndroidView(
        factory = { previewView },
        modifier = Modifier.fillMaxSize(),
    )
}
