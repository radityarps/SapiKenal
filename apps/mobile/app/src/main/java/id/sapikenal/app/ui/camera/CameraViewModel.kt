package id.sapikenal.app.ui.camera

import android.Manifest
import android.content.Context
import android.net.Uri
import android.util.Log
import androidx.core.content.ContextCompat
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import id.sapikenal.app.R
import id.sapikenal.app.data.local.SettingsDataStore
import id.sapikenal.app.domain.model.ClassifyResponse
import id.sapikenal.app.domain.model.DetectionResult
import id.sapikenal.app.domain.usecase.ClassifyImageUseCase
import id.sapikenal.app.ml.preprocessing.ClientPreprocessor
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

enum class FlashMode { AUTO, ON, OFF }

data class CameraUiState(
    val isLoading: Boolean = false,
    val error: String? = null,
    val progressText: String? = null,
    val hasCameraPermission: Boolean = false,
    val permissionPermanentlyDenied: Boolean = false,
    val flashMode: FlashMode = FlashMode.AUTO,
    val showGrid: Boolean = false,
    val showConsentPanel: Boolean = false,
    val pendingImageUri: Uri? = null,
    val pendingImageIsFromCamera: Boolean = true,
)

@HiltViewModel
class CameraViewModel
    @Inject
    constructor(
        @ApplicationContext private val appContext: Context,
        private val classifyImageUseCase: ClassifyImageUseCase,
        private val settingsDataStore: SettingsDataStore,
        private val clientPreprocessor: ClientPreprocessor,
    ) : ViewModel() {
        private val _uiState = MutableStateFlow(CameraUiState())
        val uiState: StateFlow<CameraUiState> = _uiState.asStateFlow()

        // Track detection ID for retake/update scenario
        private val _updateDetectionId = MutableStateFlow<Long?>(null)
        val updateDetectionId: StateFlow<Long?> = _updateDetectionId.asStateFlow()

        fun setUpdateDetectionId(id: Long?) {
            _updateDetectionId.value = id
        }

        fun checkPermission() {
            val hasPermission =
                ContextCompat.checkSelfPermission(
                    appContext,
                    Manifest.permission.CAMERA,
                ) == android.content.pm.PackageManager.PERMISSION_GRANTED
            _uiState.value =
                _uiState.value.copy(
                    hasCameraPermission = hasPermission,
                    permissionPermanentlyDenied = if (hasPermission) false else _uiState.value.permissionPermanentlyDenied,
                )
        }

        fun onPermissionResult(
            granted: Boolean,
            permanentlyDenied: Boolean = false,
        ) {
            _uiState.value =
                _uiState.value.copy(
                    hasCameraPermission = granted,
                    permissionPermanentlyDenied = !granted && permanentlyDenied,
                )
        }

        fun classify(
            imageUri: Uri,
            updateDetectionId: Long? = null,
            isFromCamera: Boolean = true,
            onResult: (DetectionResult) -> Unit,
        ) {
            Log.d(
                "SapiKenal",
                "ViewModel: classify() called with uri=$imageUri, updateDetectionId=$updateDetectionId, isFromCamera=$isFromCamera",
            )
            viewModelScope.launch {
                _uiState.value =
                    _uiState.value.copy(
                        isLoading = true,
                        error = null,
                        progressText = appContext.getString(R.string.camera_processing),
                    )

                // Preprocessing is the trust boundary: every successfully decoded image
                // continues to inference. The product contract intentionally has no
                // blur/brightness/size rejection gate.
                val preprocessedJpegBytes =
                    try {
                        clientPreprocessor.process(imageUri)
                    } catch (e: Exception) {
                        Log.e("SapiKenal", "ViewModel: Image preprocessing failed", e)
                        _uiState.value =
                            _uiState.value.copy(
                                isLoading = false,
                                progressText = null,
                                error = appContext.getString(R.string.quality_error_load),
                            )
                        return@launch
                    }

                runCatching {
                    classifyImageUseCase.classifyPreprocessed(
                        preprocessedJpegBytes,
                        imageUri,
                        updateDetectionId,
                        isFromCamera,
                    )
                }.onSuccess { response ->
                    when (response) {
                        is ClassifyResponse.ConsentRequired -> {
                            Log.d("SapiKenal", "ViewModel: classify() consent required")
                            _uiState.value =
                                _uiState.value.copy(
                                    showConsentPanel = true,
                                    pendingImageUri = imageUri,
                                    pendingImageIsFromCamera = isFromCamera,
                                    isLoading = false,
                                    progressText = null,
                                )
                        }

                        is ClassifyResponse.Success -> {
                            val result = response.result
                            Log.d(
                                "SapiKenal",
                                "ViewModel: classify() success — label=${result.label}, confidence=${result.confidence}, mode=${result.inferenceMode}",
                            )
                            _uiState.value =
                                _uiState.value.copy(
                                    isLoading = false,
                                    progressText = null,
                                    pendingImageUri = null,
                                )
                            onResult(result)
                        }
                    }
                }.onFailure { throwable ->
                    Log.e("SapiKenal", "ViewModel: classify() failed", throwable)
                    _uiState.value =
                        _uiState.value.copy(
                            isLoading = false,
                            progressText = null,
                            error =
                                throwable.message
                                    ?: appContext.getString(R.string.camera_processing),
                        )
                }
            }
        }

        fun setFlashMode(mode: FlashMode) {
            _uiState.value = _uiState.value.copy(flashMode = mode)
        }

        fun onConsentDecision(
            allowed: Boolean,
            onResult: (DetectionResult) -> Unit,
        ) {
            viewModelScope.launch {
                settingsDataStore.setUploadConsent(allowed)
                _uiState.value = _uiState.value.copy(showConsentPanel = false)
                // Re-trigger classification with the pending image
                _uiState.value.pendingImageUri?.let { uri ->
                    classify(
                        uri,
                        updateDetectionId = _updateDetectionId.value,
                        isFromCamera = _uiState.value.pendingImageIsFromCamera,
                        onResult = onResult,
                    )
                }
            }
        }

        fun cycleFlashMode() {
            val next =
                when (_uiState.value.flashMode) {
                    FlashMode.AUTO -> FlashMode.ON
                    FlashMode.ON -> FlashMode.OFF
                    FlashMode.OFF -> FlashMode.AUTO
                }
            _uiState.value = _uiState.value.copy(flashMode = next)
        }

        fun toggleGrid() {
            _uiState.value = _uiState.value.copy(showGrid = !_uiState.value.showGrid)
        }

        fun clearError() {
            _uiState.value = _uiState.value.copy(error = null)
        }

        fun onCaptureError(message: String) {
            _uiState.value = _uiState.value.copy(error = message)
        }
    }
