package id.sapikenal.app.domain.usecase

import android.net.Uri
import id.sapikenal.app.BuildConfig
import id.sapikenal.app.data.local.SettingsDataStore
import id.sapikenal.app.data.repository.DetectionRepository
import id.sapikenal.app.domain.model.ClassifyResponse
import id.sapikenal.app.domain.model.ConsentStatus
import id.sapikenal.app.domain.model.ImageSource
import id.sapikenal.app.location.LocationProvider
import id.sapikenal.app.location.LocationResolver
import id.sapikenal.app.ml.InferenceRouter
import kotlinx.coroutines.flow.first
import javax.inject.Inject

class ClassifyImageUseCase
    @Inject
    constructor(
        private val inferenceRouter: InferenceRouter,
        private val detectionRepository: DetectionRepository,
        private val settingsDataStore: SettingsDataStore,
        private val locationProvider: LocationProvider,
    ) {
        suspend operator fun invoke(
            imageUri: Uri,
            updateDetectionId: Long? = null,
            isFromCamera: Boolean = true,
        ): ClassifyResponse {
            val consentValue = settingsDataStore.uploadConsent.first()
            val consentStatus = ConsentStatus.fromBoolean(consentValue)

            val response = inferenceRouter.classify(imageUri, consentStatus)
            return saveSuccessfulResponse(response, imageUri, updateDetectionId, isFromCamera)
        }

        suspend fun classifyPreprocessed(
            jpegBytes: ByteArray,
            sourceImageUri: Uri,
            updateDetectionId: Long? = null,
            isFromCamera: Boolean = true,
        ): ClassifyResponse {
            val consentValue = settingsDataStore.uploadConsent.first()
            val consentStatus = ConsentStatus.fromBoolean(consentValue)

            val response = inferenceRouter.classifyPreprocessed(jpegBytes, consentStatus)
            return saveSuccessfulResponse(response, sourceImageUri, updateDetectionId, isFromCamera)
        }

        private suspend fun saveSuccessfulResponse(
            response: ClassifyResponse,
            imageUri: Uri,
            updateDetectionId: Long?,
            isFromCamera: Boolean,
        ): ClassifyResponse {
            val targetResult =
                when (response) {
                    is ClassifyResponse.Success -> response.result
                    is ClassifyResponse.Rejected -> response.result
                    is ClassifyResponse.ConsentRequired -> return response
                }

            // Resolve location: GPS assist (if enabled) → manual fallback → none
            val gpsAssistEnabled = settingsDataStore.locationEnabled.first()
            val gpsLocation = if (gpsAssistEnabled) locationProvider.getCoarseLocation() else null
            val manualLat = settingsDataStore.manualLatitude.first()?.toDoubleOrNull()
            val manualLng = settingsDataStore.manualLongitude.first()?.toDoubleOrNull()

            val location =
                LocationResolver.resolve(
                    gpsAssistEnabled = gpsAssistEnabled,
                    gpsLocation = gpsLocation,
                    manualLatitude = manualLat,
                    manualLongitude = manualLng,
                )

            val resultWithMetadata =
                targetResult.copy(
                    appVersion = BuildConfig.VERSION_NAME,
                    imageSource = ImageSource.fromBoolean(isFromCamera),
                    preprocessingSummary = PREPROCESSING_SUMMARY,
                    latitude = location.latitude,
                    longitude = location.longitude,
                    locationSource = location.source,
                )
            val savedId =
                detectionRepository.saveDetection(
                    resultWithMetadata,
                    imageUri,
                    updateDetectionId,
                )
            val savedResult = resultWithMetadata.copy(id = savedId)

            return if (response is ClassifyResponse.Rejected) {
                ClassifyResponse.Rejected(savedResult)
            } else {
                ClassifyResponse.Success(savedResult)
            }
        }

        companion object {
            /** Stable description of the current preprocessing pipeline. */
            const val PREPROCESSING_SUMMARY = "EXIF correct, resize max 800px, JPEG 85%, then 224×224 float32 raw [0..255]"
        }
    }
