package id.sapikenal.app.data.sync

import android.util.Log
import id.sapikenal.app.data.local.DeviceIdProvider
import id.sapikenal.app.data.local.SettingsDataStore
import id.sapikenal.app.data.local.dao.DetectionDao
import id.sapikenal.app.data.local.entity.DetectionEntity
import id.sapikenal.app.data.remote.api.InferenceApiService
import id.sapikenal.app.data.remote.dto.HistorySyncRequestDto
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.first
import org.json.JSONObject
import javax.inject.Inject
import javax.inject.Singleton

enum class HistorySyncAttempt {
    SUCCESS,
    RETRY,
}

@Singleton
class HistorySyncRunner
    @Inject
    constructor(
        private val detectionDao: DetectionDao,
        private val settingsDataStore: SettingsDataStore,
        private val api: InferenceApiService,
        private val deviceIdProvider: DeviceIdProvider,
    ) {
        suspend fun run(): HistorySyncAttempt = runWithConsent(settingsDataStore.uploadConsent.first() == true)

        internal suspend fun runWithConsent(consentAllowed: Boolean): HistorySyncAttempt {
            if (!consentAllowed) return HistorySyncAttempt.SUCCESS

            return try {
                detectionDao.findPendingSync().forEach { entity ->
                    val response = api.upsertHistory(entity.toRequest(deviceIdProvider.value))
                    if (!response.isSuccessful) {
                        response.errorBody()?.close()
                        return HistorySyncAttempt.RETRY
                    }
                    response.body()?.close()
                    detectionDao.markSynced(entity.id)
                }
                HistorySyncAttempt.SUCCESS
            } catch (cancellation: CancellationException) {
                throw cancellation
            } catch (error: Exception) {
                Log.w("SapiKenal", "History metadata synchronization failed", error)
                HistorySyncAttempt.RETRY
            }
        }

        private fun DetectionEntity.toRequest(deviceId: String): HistorySyncRequestDto =
            HistorySyncRequestDto(
                deviceId = deviceId,
                localId = id,
                timestamp = timestamp,
                predictedClass = predictedClass,
                displayLabel = displayLabel,
                confidence = confidence,
                scores =
                    run {
                        val json = JSONObject(scoresJson)
                        SCORE_KEYS.associateWith { key -> json.getDouble(key).toFloat() }
                    },
                inferenceMode = inferenceMode.lowercase(),
                isReliable = isReliable,
                processingMs = processingMs,
                title = title,
                description = description,
                consentStatus = consentStatus.lowercase(),
                appVersion = appVersion,
                modelVersion = modelVersion,
                imageSource = imageSource?.lowercase(),
                preprocessingSummary = preprocessingSummary,
                latitude = latitude,
                longitude = longitude,
                locationSource = locationSource?.lowercase(),
            )

        private companion object {
            val SCORE_KEYS = listOf("bali", "brahman", "brangus", "limusin")
        }
    }
