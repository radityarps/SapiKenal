package id.sapikenal.app.ui.settings

import android.app.Activity
import android.content.Context
import android.content.ContextWrapper
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsetsSides
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.only
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.core.graphics.ColorUtils
import androidx.core.view.WindowCompat
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import id.sapikenal.app.BuildConfig
import id.sapikenal.app.R
import id.sapikenal.app.data.local.SettingsDataStore
import id.sapikenal.app.data.repository.DetectionRepository
import id.sapikenal.app.ui.theme.SapiKenalColors
import id.sapikenal.app.utils.LocaleManager
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

// ════════════════════════════════════════════════════════════════════════════
// ViewModel
// ════════════════════════════════════════════════════════════════════════════

@HiltViewModel
class SettingsViewModel
    @Inject
    constructor(
        private val settingsDataStore: SettingsDataStore,
        private val detectionRepository: DetectionRepository,
        private val purgeManager: id.sapikenal.app.data.repository.PurgeManager,
    ) : ViewModel() {
        val language: StateFlow<String> =
            settingsDataStore.language
                .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), "system")

        val textSize: StateFlow<String> =
            settingsDataStore.textSize
                .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), "system")

        val uploadConsent: StateFlow<Boolean?> =
            settingsDataStore.uploadConsent
                .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), null)

        private val _snackbarMessageRes = MutableStateFlow<Int?>(null)
        val snackbarMessageRes: StateFlow<Int?> = _snackbarMessageRes.asStateFlow()

        fun setLanguage(value: String) {
            viewModelScope.launch { settingsDataStore.setLanguage(value) }
        }

        fun setTextSize(value: String) {
            viewModelScope.launch { settingsDataStore.setTextSize(value) }
        }

        fun setUploadConsent(value: Boolean) {
            viewModelScope.launch { settingsDataStore.setUploadConsent(value) }
        }

        fun purgeDeletedRecords() {
            viewModelScope.launch {
                runCatching { purgeManager.purgeExpired() }
                _snackbarMessageRes.value = R.string.settings_purge_done
            }
        }

        fun clearAllHistory() {
            // Policy: This is an immediate, permanent purge of ALL detection records
            // and their associated image files. Unlike soft-delete (which retains records
            // for 30 days), this action is irreversible and cannot be undone.
            viewModelScope.launch {
                detectionRepository.deleteAll()
                _snackbarMessageRes.value = R.string.settings_history_cleared
            }
        }

        fun resetOnboarding(context: Context) {
            context
                .getSharedPreferences(
                    context.packageName + "_preferences",
                    Context.MODE_PRIVATE,
                ).edit()
                .putBoolean("has_completed_onboarding", false)
                .apply()
            _snackbarMessageRes.value = R.string.settings_onboarding_reset
        }

        fun clearSnackbar() {
            _snackbarMessageRes.value = null
        }
    }

// ════════════════════════════════════════════════════════════════════════════
// UI
// ════════════════════════════════════════════════════════════════════════════

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsRoute(
    onBack: (() -> Unit)? = null,
    viewModel: SettingsViewModel = hiltViewModel(),
) {
    val context = LocalContext.current
    val language by viewModel.language.collectAsStateWithLifecycle()
    val textSize by viewModel.textSize.collectAsStateWithLifecycle()
    val uploadConsent by viewModel.uploadConsent.collectAsStateWithLifecycle()
    val snackbarMessageRes by viewModel.snackbarMessageRes.collectAsStateWithLifecycle()

    var showLanguageDialog by remember { mutableStateOf(false) }
    var showTextSizeDialog by remember { mutableStateOf(false) }
    var showClearHistoryDialog by remember { mutableStateOf(false) }
    var showResetOnboardingDialog by remember { mutableStateOf(false) }
    var showPurgeDialog by remember { mutableStateOf(false) }

    val snackbarHostState = remember { SnackbarHostState() }

    snackbarMessageRes?.let { messageRes ->
        val snackbarText = stringResource(messageRes)
        LaunchedEffect(messageRes) {
            snackbarHostState.showSnackbar(snackbarText)
            viewModel.clearSnackbar()
        }
    }

    val view = LocalView.current
    val statusBarColorArgb = MaterialTheme.colorScheme.surface.toArgb()
    val isLightStatusBar = ColorUtils.calculateLuminance(statusBarColorArgb) > 0.5

    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as? Activity)?.window ?: return@SideEffect
            window.statusBarColor = statusBarColorArgb
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = isLightStatusBar
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = stringResource(R.string.settings_title),
                        style = MaterialTheme.typography.headlineMedium,
                        fontWeight = FontWeight.Bold,
                        color = SapiKenalColors.TextPrimary,
                    )
                },
                navigationIcon = {
                    if (onBack != null) {
                        IconButton(onClick = onBack) {
                            Icon(
                                Icons.AutoMirrored.Filled.ArrowBack,
                                contentDescription = stringResource(R.string.nav_back),
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
        snackbarHost = { SnackbarHost(snackbarHostState) },
    ) { innerPadding ->
        Column(
            modifier =
                Modifier
                    .fillMaxSize()
                    .padding(innerPadding)
                    .verticalScroll(rememberScrollState())
                    .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            // Language
            PreferenceRow(
                title = stringResource(R.string.settings_language),
                value = languageDisplayName(language),
                onClick = { showLanguageDialog = true },
            )

            // Text size
            PreferenceRow(
                title = stringResource(R.string.settings_text_size),
                value = textSizeDisplayName(textSize),
                onClick = { showTextSizeDialog = true },
            )

            // Upload consent toggle
            UploadConsentRow(
                checked = uploadConsent == true,
                onCheckedChange = { viewModel.setUploadConsent(it) },
            )

            Spacer(Modifier.height(12.dp))
            HorizontalDivider()
            Spacer(Modifier.height(12.dp))

            // Clear all history
            PreferenceRow(
                title = stringResource(R.string.settings_clear_history),
                onClick = { showClearHistoryDialog = true },
                titleColor = SapiKenalColors.Error,
            )

            // Purge deleted records
            PreferenceRow(
                title = stringResource(R.string.settings_purge_deleted),
                value = stringResource(R.string.settings_purge_deleted_description),
                onClick = { showPurgeDialog = true },
                titleColor = SapiKenalColors.Error,
            )

            // Reset onboarding
            PreferenceRow(
                title = stringResource(R.string.settings_reset_onboarding),
                onClick = { showResetOnboardingDialog = true },
            )

            Spacer(Modifier.height(12.dp))
            HorizontalDivider()
            Spacer(Modifier.height(12.dp))

            // App version (read-only)
            PreferenceRow(
                title = stringResource(R.string.settings_app_version),
                value = BuildConfig.VERSION_NAME,
                enabled = false,
            )

            // Model version (read-only)
            PreferenceRow(
                title = stringResource(R.string.settings_model_version),
                value = id.sapikenal.app.ml.OfflineInferenceEngine.MODEL_VERSION,
                enabled = false,
            )

            Spacer(Modifier.height(12.dp))
            HorizontalDivider()
            Spacer(Modifier.height(12.dp))

            // Privacy section
            Text(
                text = stringResource(R.string.settings_privacy_title),
                style = MaterialTheme.typography.titleMedium,
                color = SapiKenalColors.TextPrimary,
            )
            Spacer(Modifier.height(8.dp))
            listOf(
                R.string.settings_privacy_exif,
                R.string.settings_privacy_no_retention,
                R.string.settings_privacy_local_history,
                R.string.settings_privacy_offline,
            ).forEach { resId ->
                Text(
                    text = "• ${stringResource(resId)}",
                    style = MaterialTheme.typography.bodyMedium,
                    color = SapiKenalColors.TextSecondary,
                    modifier = Modifier.padding(vertical = 2.dp),
                )
            }
        }
    }

    // ── Dialogs ──────────────────────────────────────────────────────

    if (showLanguageDialog) {
        SelectionDialog(
            title = stringResource(R.string.settings_language),
            options =
                listOf(
                    "system" to stringResource(R.string.settings_language_system),
                    "id" to stringResource(R.string.settings_language_id),
                    "en" to stringResource(R.string.settings_language_en),
                ),
            selected = language,
            onSelect = {
                val shouldApplyLanguage = it != LocaleManager.currentLanguageSetting()
                viewModel.setLanguage(it)
                if (shouldApplyLanguage) {
                    LocaleManager.applyLanguage(it)
                    context.findActivity()?.recreate()
                }
                showLanguageDialog = false
            },
            onDismiss = { showLanguageDialog = false },
        )
    }

    if (showTextSizeDialog) {
        SelectionDialog(
            title = stringResource(R.string.settings_text_size),
            options =
                listOf(
                    "system" to stringResource(R.string.settings_text_size_system),
                    "small" to stringResource(R.string.settings_text_size_small),
                    "medium" to stringResource(R.string.settings_text_size_medium),
                    "large" to stringResource(R.string.settings_text_size_large),
                ),
            selected = textSize,
            onSelect = {
                viewModel.setTextSize(it)
                showTextSizeDialog = false
            },
            onDismiss = { showTextSizeDialog = false },
        )
    }

    if (showClearHistoryDialog) {
        AlertDialog(
            onDismissRequest = { showClearHistoryDialog = false },
            title = { Text(stringResource(R.string.settings_clear_history)) },
            text = { Text(stringResource(R.string.settings_clear_history_message)) },
            confirmButton = {
                TextButton(onClick = {
                    viewModel.clearAllHistory()
                    showClearHistoryDialog = false
                }) {
                    Text(stringResource(R.string.btn_delete))
                }
            },
            dismissButton = {
                TextButton(onClick = { showClearHistoryDialog = false }) {
                    Text(stringResource(R.string.btn_cancel))
                }
            },
        )
    }

    if (showPurgeDialog) {
        AlertDialog(
            onDismissRequest = { showPurgeDialog = false },
            title = { Text(stringResource(R.string.settings_purge_deleted)) },
            text = { Text(stringResource(R.string.settings_purge_deleted_message)) },
            confirmButton = {
                TextButton(onClick = {
                    viewModel.purgeDeletedRecords()
                    showPurgeDialog = false
                }) {
                    Text(stringResource(R.string.btn_ok))
                }
            },
            dismissButton = {
                TextButton(onClick = { showPurgeDialog = false }) {
                    Text(stringResource(R.string.btn_cancel))
                }
            },
        )
    }

    if (showResetOnboardingDialog) {
        AlertDialog(
            onDismissRequest = { showResetOnboardingDialog = false },
            title = { Text(stringResource(R.string.settings_reset_onboarding)) },
            text = { Text(stringResource(R.string.settings_reset_onboarding_message)) },
            confirmButton = {
                TextButton(onClick = {
                    viewModel.resetOnboarding(context)
                    showResetOnboardingDialog = false
                }) {
                    Text(stringResource(R.string.btn_ok))
                }
            },
            dismissButton = {
                TextButton(onClick = { showResetOnboardingDialog = false }) {
                    Text(stringResource(R.string.btn_cancel))
                }
            },
        )
    }
}

private fun Context.findActivity(): Activity? {
    var current: Context? = this
    while (current is ContextWrapper) {
        if (current is Activity) return current
        current = current.baseContext
    }
    return null
}

// ════════════════════════════════════════════════════════════════════════════
// Sub-composables
// ════════════════════════════════════════════════════════════════════════════

@Composable
private fun PreferenceRow(
    title: String,
    value: String? = null,
    enabled: Boolean = true,
    titleColor: Color? = null,
    onClick: () -> Unit = {},
) {
    val finalColor = titleColor ?: MaterialTheme.colorScheme.onSurface
    Surface(
        modifier =
            Modifier
                .fillMaxWidth()
                .clickable(enabled = enabled, onClick = onClick),
        color = Color.Transparent,
    ) {
        Row(
            modifier = Modifier.padding(vertical = 12.dp, horizontal = 4.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = title,
                    style = MaterialTheme.typography.bodyLarge,
                    color = if (enabled) finalColor else finalColor.copy(alpha = 0.5f),
                )
                if (value != null) {
                    Text(
                        text = value,
                        style = MaterialTheme.typography.bodyMedium,
                        color = SapiKenalColors.TextSecondary,
                    )
                }
            }
            if (enabled) {
                Text(
                    "›",
                    color = SapiKenalColors.TextSecondary,
                    style = MaterialTheme.typography.titleMedium,
                )
            }
        }
    }
}

@Composable
private fun SelectionDialog(
    title: String,
    options: List<Pair<String, String>>,
    selected: String,
    onSelect: (String) -> Unit,
    onDismiss: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(title) },
        text = {
            Column {
                options.forEach { (key, label) ->
                    Row(
                        modifier =
                            Modifier
                                .fillMaxWidth()
                                .clickable { onSelect(key) }
                                .padding(vertical = 12.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        RadioButton(selected = selected == key, onClick = { onSelect(key) })
                        Spacer(Modifier.width(12.dp))
                        Text(label, style = MaterialTheme.typography.bodyLarge)
                    }
                }
            }
        },
        confirmButton = {},
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text(stringResource(R.string.btn_cancel))
            }
        },
    )
}

@Composable
private fun UploadConsentRow(
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        color = Color.Transparent,
    ) {
        Row(
            modifier = Modifier.padding(vertical = 12.dp, horizontal = 4.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = stringResource(R.string.settings_upload_consent),
                    style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurface,
                )
                Text(
                    text = stringResource(R.string.settings_upload_consent_description),
                    style = MaterialTheme.typography.bodyMedium,
                    color = SapiKenalColors.TextSecondary,
                )
            }
            Spacer(Modifier.width(12.dp))
            Switch(
                checked = checked,
                onCheckedChange = onCheckedChange,
            )
        }
    }
}

@Composable
private fun languageDisplayName(code: String): String =
    when (code) {
        "id" -> stringResource(R.string.settings_language_id)
        "en" -> stringResource(R.string.settings_language_en)
        else -> stringResource(R.string.settings_language_system)
    }

@Composable
private fun textSizeDisplayName(code: String): String =
    when (code) {
        "small" -> stringResource(R.string.settings_text_size_small)
        "medium" -> stringResource(R.string.settings_text_size_medium)
        "large" -> stringResource(R.string.settings_text_size_large)
        else -> stringResource(R.string.settings_text_size_system)
    }
