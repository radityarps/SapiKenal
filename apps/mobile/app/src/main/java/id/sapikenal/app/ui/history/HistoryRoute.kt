package id.sapikenal.app.ui.history

import android.app.Activity
import androidx.annotation.StringRes
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsetsSides
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.only
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.graphics.ColorUtils
import androidx.core.view.WindowCompat
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import coil.compose.AsyncImage
import id.sapikenal.app.R
import id.sapikenal.app.ui.theme.SapiKenalColors
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

// ── Disease display helpers ──────────────────────────────────────────────

private val diseaseMap =
    mapOf(
        "SEHAT" to ("🟢" to SapiKenalColors.Healthy),
        "sehat" to ("🟢" to SapiKenalColors.Healthy),
        "healthy" to ("🟢" to SapiKenalColors.Healthy),
        "PMK" to ("🔴" to SapiKenalColors.DangerPMK),
        "FMD" to ("🔴" to SapiKenalColors.DangerPMK),
        "pmk" to ("🔴" to SapiKenalColors.DangerPMK),
        "fmd" to ("🔴" to SapiKenalColors.DangerPMK),
        "LSD" to ("🟠" to SapiKenalColors.WarningLSD),
        "LATO_LATO" to ("🟠" to SapiKenalColors.WarningLSD),
        "lsd" to ("🟠" to SapiKenalColors.WarningLSD),
        "lato_lato" to ("🟠" to SapiKenalColors.WarningLSD),
        "non_cattle" to ("🚫" to SapiKenalColors.TextSecondary),
        "NON_CATTLE" to ("🚫" to SapiKenalColors.TextSecondary),
    )

private val diseaseDisplayNames =
    mapOf(
        "SEHAT" to R.string.result_disease_sehat,
        "healthy" to R.string.result_disease_sehat,
        "PMK" to R.string.result_disease_fmd,
        "FMD" to R.string.result_disease_fmd,
        "LSD" to R.string.result_disease_lsd,
        "LATO_LATO" to R.string.result_disease_lsd,
        "non_cattle" to R.string.result_disease_non_cattle,
        "NON_CATTLE" to R.string.result_disease_non_cattle,
    )

private fun diseaseEmoji(label: String): String = diseaseMap[label]?.first ?: "📸"

private fun diseaseColor(label: String): Color = diseaseMap[label]?.second ?: SapiKenalColors.TextSecondary

@StringRes
private fun diseaseDisplayNameRes(label: String): Int? = diseaseDisplayNames[label]

private fun formatTimestamp(
    millis: Long,
    locale: Locale,
): String {
    val sdf = SimpleDateFormat("dd MMM yyyy, HH:mm", locale)
    return sdf.format(Date(millis))
}

// ── Screen ───────────────────────────────────────────────────────────────

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HistoryRoute(
    onOpenDetail: (
        label: String,
        confidence: Float,
        mode: String,
        scoresJson: String,
        imageRef: String,
        timestamp: Long,
        detectionId: Long,
    ) -> Unit,
    viewModel: HistoryViewModel = hiltViewModel(),
) {
    val rows by viewModel.filteredRows.collectAsStateWithLifecycle()
    val filterClass by viewModel.classFilter.collectAsStateWithLifecycle()
    val filterMode by viewModel.modeFilter.collectAsStateWithLifecycle()
    val lastDeletedId by viewModel.lastDeletedId.collectAsStateWithLifecycle()

    var showDeleteAllDialog by remember { mutableStateOf(false) }
    var deleteTargetId by remember { mutableStateOf<Long?>(null) }
    val snackbarHostState = remember { androidx.compose.material3.SnackbarHostState() }
    val deletedMessage = stringResource(R.string.history_deleted)
    val undoLabel = stringResource(R.string.history_undo)

    // Show undo snackbar when an item is soft-deleted
    androidx.compose.runtime.LaunchedEffect(lastDeletedId) {
        if (lastDeletedId != null) {
            val result =
                snackbarHostState.showSnackbar(
                    message = deletedMessage,
                    actionLabel = undoLabel,
                    duration = androidx.compose.material3.SnackbarDuration.Short,
                )
            if (result == androidx.compose.material3.SnackbarResult.ActionPerformed) {
                viewModel.undoDelete()
            } else {
                viewModel.clearLastDeleted()
            }
        }
    }
    val view = LocalView.current
    val statusBarColorArgb = MaterialTheme.colorScheme.surface.toArgb()
    val isLightStatusBar = ColorUtils.calculateLuminance(statusBarColorArgb) > 0.5

    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = statusBarColorArgb
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = isLightStatusBar
        }
    }

    Scaffold(
        snackbarHost = { androidx.compose.material3.SnackbarHost(snackbarHostState) },
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = stringResource(R.string.history_title),
                        style = MaterialTheme.typography.headlineMedium,
                        fontWeight = FontWeight.Bold,
                        color = SapiKenalColors.TextPrimary,
                    )
                },
                actions = {
                    if (rows.isNotEmpty()) {
                        IconButton(onClick = { showDeleteAllDialog = true }) {
                            Icon(
                                Icons.Filled.Delete,
                                contentDescription = stringResource(R.string.history_delete_all_title),
                                tint = SapiKenalColors.TextSecondary,
                            )
                        }
                    }
                },
                colors =
                    TopAppBarDefaults.topAppBarColors(
                        containerColor = MaterialTheme.colorScheme.surface,
                    ),
                windowInsets = TopAppBarDefaults.windowInsets.only(WindowInsetsSides.Horizontal),
            )
        },
    ) { innerPadding ->
        Column(
            modifier =
                Modifier
                    .fillMaxSize()
                    .padding(innerPadding),
        ) {
            // ── Filter chips ──────────────────────────────────────
            FilterChipRow(
                selectedClass = filterClass,
                selectedMode = filterMode,
                onSelectClass = { viewModel.setClassFilter(it) },
                onSelectMode = { viewModel.setModeFilter(it) },
            )

            // ── Content ───────────────────────────────────────────
            if (rows.isEmpty() && filterClass == null && filterMode == null) {
                // Empty state
                Box(
                    modifier =
                        Modifier
                            .weight(1f)
                            .fillMaxWidth(),
                    contentAlignment = Alignment.Center,
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text("🐄", fontSize = 64.sp)
                        Spacer(Modifier.height(16.dp))
                        Text(
                            text = stringResource(R.string.history_empty),
                            style = MaterialTheme.typography.bodyLarge,
                            color = SapiKenalColors.TextSecondary,
                        )
                    }
                }
            } else if (rows.isEmpty()) {
                // Filter empty state
                Box(
                    modifier =
                        Modifier
                            .weight(1f)
                            .fillMaxWidth(),
                    contentAlignment = Alignment.Center,
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(
                            text = stringResource(R.string.history_empty_filter),
                            style = MaterialTheme.typography.bodyLarge,
                        )
                        Spacer(Modifier.height(8.dp))
                        TextButton(onClick = {
                            viewModel.setClassFilter(null)
                            viewModel.setModeFilter(null)
                        }) {
                            Text(stringResource(R.string.history_clear_filter))
                        }
                    }
                }
            } else {
                LazyColumn(
                    modifier = Modifier.weight(1f),
                    contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    items(rows, key = { it.id }) { item ->
                        HistoryCard(
                            item = item,
                            onTap = {
                                onOpenDetail(
                                    item.label,
                                    item.confidence,
                                    item.mode,
                                    item.allScoresJson,
                                    item.imagePath.orEmpty(),
                                    item.timestamp,
                                    item.id,
                                )
                            },
                            onDelete = { deleteTargetId = item.id },
                        )
                    }
                }
            }
        }
    }

    // ── Delete single item dialog ────────────────────────────────────
    if (deleteTargetId != null) {
        AlertDialog(
            onDismissRequest = { deleteTargetId = null },
            title = { Text(stringResource(R.string.history_delete_title)) },
            text = { Text(stringResource(R.string.history_delete_message)) },
            confirmButton = {
                TextButton(onClick = {
                    deleteTargetId?.let { viewModel.deleteItem(it) }
                    deleteTargetId = null
                }) {
                    Text(stringResource(R.string.btn_delete))
                }
            },
            dismissButton = {
                TextButton(onClick = { deleteTargetId = null }) {
                    Text(stringResource(R.string.btn_cancel))
                }
            },
        )
    }

    // ── Delete all dialog ────────────────────────────────────────────
    if (showDeleteAllDialog) {
        AlertDialog(
            onDismissRequest = { showDeleteAllDialog = false },
            title = { Text(stringResource(R.string.history_delete_all_title)) },
            text = { Text(stringResource(R.string.history_delete_all_message)) },
            confirmButton = {
                TextButton(onClick = {
                    viewModel.deleteAll()
                    showDeleteAllDialog = false
                }) {
                    Text(stringResource(R.string.btn_delete))
                }
            },
            dismissButton = {
                TextButton(onClick = { showDeleteAllDialog = false }) {
                    Text(stringResource(R.string.btn_cancel))
                }
            },
        )
    }
}

// ── Sub-composables ──────────────────────────────────────────────────────

@Composable
private fun FilterChipRow(
    selectedClass: String?,
    selectedMode: String?,
    onSelectClass: (String?) -> Unit,
    onSelectMode: (String?) -> Unit,
) {
    Row(
        modifier =
            Modifier
                .fillMaxWidth()
                .horizontalScroll(rememberScrollState())
                .padding(horizontal = 16.dp, vertical = 8.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        // "Semua" chip
        val allSelected = selectedClass == null && selectedMode == null
        FilterChip(
            selected = allSelected,
            onClick = {
                onSelectClass(null)
                onSelectMode(null)
            },
            label = { Text(stringResource(R.string.history_filter_all)) },
        )

        // Class chips
        listOf(
            "healthy" to R.string.history_filter_sehat,
            "FMD" to R.string.history_filter_fmd,
            "LSD" to R.string.history_filter_lsd,
            "non_cattle" to R.string.history_filter_non_cattle,
        ).forEach { (value, labelRes) ->
            FilterChip(
                selected = selectedClass == value && selectedMode == null,
                onClick = {
                    onSelectClass(value)
                    onSelectMode(null)
                },
                label = { Text(stringResource(labelRes)) },
            )
        }

        // Mode chips
        listOf(
            "ONLINE" to R.string.history_filter_online,
            "OFFLINE" to R.string.history_filter_offline,
        ).forEach { (value, labelRes) ->
            FilterChip(
                selected = selectedMode == value && selectedClass == null,
                onClick = {
                    onSelectMode(value)
                    onSelectClass(null)
                },
                label = { Text(stringResource(labelRes)) },
            )
        }
    }
}

@Composable
private fun HistoryCard(
    item: HistoryItemUi,
    onTap: () -> Unit,
    onDelete: () -> Unit,
) {
    val isRejected = item.outcome.equals("REJECTED", ignoreCase = true) || item.label.equals("non_cattle", ignoreCase = true)
    val emoji = diseaseEmoji(item.label)
    val color = diseaseColor(item.label)
    val displayNameRes = diseaseDisplayNameRes(item.label)
    val displayName = displayNameRes?.let { stringResource(it) } ?: item.displayLabel
    val noteTitle = item.title?.takeIf { it.isNotBlank() }
    val noteDescription = item.description?.takeIf { it.isNotBlank() }
    val locale = LocalConfiguration.current.locales[0]
    val isOnline = item.mode.equals("ONLINE", ignoreCase = true)
    val modeLabel =
        if (isOnline) {
            stringResource(R.string.result_mode_online)
        } else {
            stringResource(R.string.result_mode_offline)
        }

    Card(
        modifier =
            Modifier
                .fillMaxWidth()
                .clickable(onClick = onTap),
        shape = RoundedCornerShape(12.dp),
    ) {
        Row(
            modifier =
                Modifier
                    .fillMaxWidth()
                    .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            // Thumbnail placeholder
            Surface(
                modifier = Modifier.size(56.dp),
                shape = RoundedCornerShape(8.dp),
                color = MaterialTheme.colorScheme.surfaceVariant,
            ) {
                val imagePath = item.imagePath
                if (!imagePath.isNullOrBlank() && File(imagePath).exists()) {
                    AsyncImage(
                        model = File(imagePath),
                        contentDescription = displayName,
                        modifier = Modifier.fillMaxSize(),
                    )
                } else {
                    Box(contentAlignment = Alignment.Center) {
                        Text(emoji, fontSize = 24.sp)
                    }
                }
            }

            Spacer(Modifier.width(12.dp))

            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = noteTitle ?: displayName,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                    color = SapiKenalColors.TextPrimary,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )

                if (noteDescription != null) {
                    Spacer(Modifier.height(2.dp))
                    Text(
                        text = noteDescription,
                        style = MaterialTheme.typography.bodySmall,
                        color = SapiKenalColors.TextSecondary,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis,
                    )
                }

                Spacer(Modifier.height(6.dp))

                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    Surface(
                        shape = RoundedCornerShape(999.dp),
                        color = color.copy(alpha = 0.14f),
                    ) {
                        Text(
                            text = if (isRejected) stringResource(R.string.rejection_status_badge) else displayName,
                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp),
                            style = MaterialTheme.typography.labelSmall,
                            color = color,
                            fontWeight = FontWeight.SemiBold,
                        )
                    }
                    Text(
                        text =
                            if (isRejected) {
                                stringResource(R.string.history_item_rejected, modeLabel)
                            } else {
                                stringResource(R.string.history_confidence_percent, (item.confidence * 100).toInt())
                            },
                        style = MaterialTheme.typography.bodySmall,
                        color = SapiKenalColors.TextSecondary,
                    )
                }

                Spacer(Modifier.height(4.dp))

                Row(verticalAlignment = Alignment.CenterVertically) {
                    if (!isRejected) {
                        val modeColor =
                            if (isOnline) {
                                SapiKenalColors.Healthy
                            } else {
                                SapiKenalColors.WarningLSD
                            }
                        Surface(
                            shape = RoundedCornerShape(4.dp),
                            color = modeColor.copy(alpha = 0.15f),
                        ) {
                            Text(
                                text = modeLabel,
                                modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                                fontSize = 10.sp,
                                color = modeColor,
                            )
                        }

                        Spacer(Modifier.width(8.dp))
                    }

                    Text(
                        text = formatTimestamp(item.timestamp, locale),
                        style = MaterialTheme.typography.bodySmall,
                        color = SapiKenalColors.TextSecondary,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                }
            }

            // Delete button
            IconButton(onClick = onDelete) {
                Icon(
                    Icons.Filled.Delete,
                    contentDescription = stringResource(R.string.btn_delete),
                    tint = SapiKenalColors.DangerPMK.copy(alpha = 0.7f),
                )
            }
        }
    }
}
