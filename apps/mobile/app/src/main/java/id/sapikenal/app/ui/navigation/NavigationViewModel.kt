package id.sapikenal.app.ui.navigation

import androidx.lifecycle.ViewModel
import dagger.hilt.android.lifecycle.HiltViewModel
import id.sapikenal.app.domain.model.DetectionResult
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import javax.inject.Inject

@HiltViewModel
class NavigationViewModel
    @Inject
    constructor() : ViewModel() {
        // Tracks the detection ID to update on retake
        private val _updateDetectionId = MutableStateFlow<Long?>(null)
        val updateDetectionId: StateFlow<Long?> = _updateDetectionId.asStateFlow()

        // A single bounded payload bridges the camera and result destinations. The persisted
        // record remains the process-recreation fallback.
        private var pendingResult: Pair<String, DetectionResult>? = null

        // Flag to trigger navigation to camera on retake
        private val _shouldNavigateToCamera = MutableStateFlow(false)
        val shouldNavigateToCamera: StateFlow<Boolean> = _shouldNavigateToCamera.asStateFlow()

        fun setUpdateDetectionId(id: Long?) {
            _updateDetectionId.value = id
        }

        fun clearUpdateDetectionId() {
            _updateDetectionId.value = null
        }

        fun triggerNavigateToCamera() {
            _shouldNavigateToCamera.value = true
        }

        fun clearNavigateToCamera() {
            _shouldNavigateToCamera.value = false
        }

        fun setPendingResult(
            key: String,
            result: DetectionResult,
        ) {
            pendingResult = key to result
        }

        fun takePendingResult(key: String): DetectionResult? {
            val pending = pendingResult ?: return null
            pendingResult = null
            return pending.takeIf { it.first == key }?.second
        }
    }
