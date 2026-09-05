package id.sapikenal.app.data.repository

import android.content.Context
import android.net.Uri
import dagger.hilt.android.qualifiers.ApplicationContext
import id.sapikenal.app.data.local.dao.DetectionDao
import id.sapikenal.app.data.local.entity.DetectionEntity
import id.sapikenal.app.data.sync.HistorySyncScheduler
import id.sapikenal.app.domain.model.ConsentStatus
import id.sapikenal.app.domain.model.DetectionResult
import id.sapikenal.app.domain.model.ImageSource
import id.sapikenal.app.domain.model.InferenceMode
import id.sapikenal.app.domain.model.LocationSource
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import org.json.JSONObject
import java.io.File
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class DetectionRepository
    @Inject
    constructor(
        private val detectionDao: DetectionDao,
        @ApplicationContext private val context: Context,
    ) {
        suspend fun saveDetection(
            result: DetectionResult,
            imageUri: Uri,
            updateDetectionId: Long? = null,
        ): Long {
            val imagePath = copyImageToLocalHistory(imageUri)
            val detectionEntity =
                DetectionEntity(
                    id = updateDetectionId ?: 0,
                    timestamp = System.currentTimeMillis(),
                    imagePath = imagePath,
                    predictedClass = result.label,
                    displayLabel = result.displayLabel,
                    confidence = result.confidence,
                    scoresJson = scoresJson(result.allScores),
                    inferenceMode = result.inferenceMode.name,
                    isReliable = result.isReliable,
                    processingMs = result.processingMs,
                    consentStatus = result.consentStatus.name,
                    appVersion = result.appVersion,
                    modelVersion = result.modelVersion,
                    imageSource = result.imageSource?.name,
                    preprocessingSummary = result.preprocessingSummary,
                    latitude = result.latitude,
                    longitude = result.longitude,
                    locationSource = result.locationSource?.name,
                    pdfCachePath = result.pdfCachePath,
                )
            val id = detectionDao.insert(detectionEntity)
            if (result.consentStatus == ConsentStatus.ALLOWED) {
                HistorySyncScheduler.enqueue(context)
            }
            return id
        }

        suspend fun updateNote(
            id: Long,
            title: String?,
            description: String?,
        ) {
            detectionDao.updateNote(id, title, description)
        }

        suspend fun updatePdfCachePath(
            id: Long,
            path: String,
        ) {
            detectionDao.updatePdfCachePath(id, path)
        }

        fun observeDetection(id: Long): Flow<DetectionResult?> = detectionDao.observeById(id).map { it?.toDomain() }

        fun observeHistory(): Flow<List<DetectionResult>> =
            detectionDao.observeAll().map { rows ->
                rows.map { it.toDomain() }
            }

        suspend fun deleteDetection(id: Long) {
            val entity = detectionDao.findById(id)
            entity?.imagePath?.let { deleteFileIfExists(it) }
            entity?.pdfCachePath?.let { deleteFileIfExists(it) }
            detectionDao.deleteById(id)
        }

        suspend fun deleteAll() {
            detectionDao.findAllImagePaths().forEach { deleteFileIfExists(it) }
            detectionDao.findAllPdfPaths().forEach { deleteFileIfExists(it) }
            detectionDao.deleteAll()
        }

        suspend fun softDelete(id: Long) {
            detectionDao.softDelete(id, System.currentTimeMillis())
        }

        suspend fun restoreDeleted(id: Long) {
            detectionDao.restoreDeleted(id)
        }

        fun observeHistoryFiltered(
            classFilter: String?,
            modeFilter: String?,
        ): Flow<List<DetectionResult>> =
            when {
                classFilter != null && modeFilter != null -> {
                    detectionDao.observeAll().map { rows ->
                        rows
                            .filter {
                                (
                                    it.predictedClass.equals(classFilter, ignoreCase = true)
                                ) &&
                                    it.inferenceMode.equals(modeFilter, ignoreCase = true)
                            }.map { it.toDomain() }
                    }
                }

                classFilter != null -> {
                    detectionDao.observeAll().map { rows ->
                        rows
                            .filter {
                                it.predictedClass.equals(classFilter, ignoreCase = true)
                            }.map { it.toDomain() }
                    }
                }

                modeFilter != null -> {
                    detectionDao.observeByMode(modeFilter).map { rows ->
                        rows.map { it.toDomain() }
                    }
                }

                else -> {
                    observeHistory()
                }
            }

        private fun DetectionEntity.toDomain(): DetectionResult {
            val mode = runCatching { InferenceMode.valueOf(inferenceMode) }.getOrDefault(InferenceMode.OFFLINE)
            val consent = runCatching { ConsentStatus.valueOf(consentStatus) }.getOrDefault(ConsentStatus.UNDECIDED)
            val source = imageSource?.let { runCatching { ImageSource.valueOf(it) }.getOrNull() }
            val locSource = locationSource?.let { runCatching { LocationSource.valueOf(it) }.getOrNull() }
            return DetectionResult(
                id = id,
                imagePath = imagePath,
                label = predictedClass,
                displayLabel = displayLabel,
                confidence = confidence,
                isReliable = isReliable,
                allScores = parseScores(scoresJson),
                inferenceMode = mode,
                consentStatus = consent,
                timestamp = timestamp,
                processingMs = processingMs,
                title = title,
                description = description,
                appVersion = appVersion,
                modelVersion = modelVersion,
                imageSource = source,
                preprocessingSummary = preprocessingSummary,
                latitude = latitude,
                longitude = longitude,
                locationSource = locSource,
                deletedAt = deletedAt,
                pdfCachePath = pdfCachePath,
            )
        }

        private fun scoresJson(scores: Map<String, Float>): String {
            val json = JSONObject()
            SCORE_KEYS.forEach { key -> json.put(key, scores[key] ?: 0f) }
            return json.toString()
        }

        private fun parseScores(raw: String): Map<String, Float> =
            runCatching {
                val json = JSONObject(raw)
                SCORE_KEYS.associateWith { json.getDouble(it).toFloat() }
            }.getOrDefault(emptyMap())

        private companion object {
            val SCORE_KEYS = listOf("bali", "brahman", "brangus", "limusin")
        }

        private fun copyImageToLocalHistory(imageUri: Uri): String? =
            runCatching {
                val dir = File(context.filesDir, "history_images")
                if (!dir.exists()) dir.mkdirs()

                val file = File(dir, "scan_${System.currentTimeMillis()}.jpg")
                context.contentResolver.openInputStream(imageUri)?.use { input ->
                    file.outputStream().use { output ->
                        input.copyTo(output)
                    }
                }
                file.absolutePath
            }.getOrNull()

        private fun deleteFileIfExists(path: String) {
            runCatching {
                val file = File(path)
                if (file.exists()) file.delete()
            }
        }
    }
