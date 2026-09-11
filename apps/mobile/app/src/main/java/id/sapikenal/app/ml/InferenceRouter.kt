package id.sapikenal.app.ml

import android.net.Uri
import android.util.Log
import id.sapikenal.app.di.OfflineClassifier
import id.sapikenal.app.di.OnlineClassifier
import id.sapikenal.app.domain.model.ClassifyFailure
import id.sapikenal.app.domain.model.ClassifyResponse
import id.sapikenal.app.domain.model.ConsentStatus
import id.sapikenal.app.domain.model.DetectionResult
import id.sapikenal.app.domain.model.InferenceMode
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class InferenceRouter
    @Inject
    constructor(
        private val clientPreprocessor: ImagePreprocessor,
        @OnlineClassifier private val onlineClient: ImageClassifier,
        @OfflineClassifier private val offlineEngine: ImageClassifier,
        private val networkChecker: NetworkChecker,
    ) {
        /**
         * Consent-aware classification that gates online inference behind user consent.
         *
         * Routing logic:
         * - Online + UNDECIDED → ConsentRequired (no preprocessing)
         * - Online + ALLOWED  → online with offline fallback on failure
         * - Offline OR DENIED → offline engine
         */
        suspend fun classify(
            imageUri: Uri,
            consentStatus: ConsentStatus,
        ): ClassifyResponse {
            Log.d("SapiKenal", "InferenceRouter: classify() started, uri=$imageUri, consent=$consentStatus")

            val online = networkChecker.isOnline()
            Log.d("SapiKenal", "InferenceRouter: isOnline=$online")

            // When online and consent is undecided, signal that consent is required
            // without performing any preprocessing or network upload.
            if (online && consentStatus == ConsentStatus.UNDECIDED) {
                Log.d("SapiKenal", "InferenceRouter: consent undecided while online, returning ConsentRequired")
                return ClassifyResponse.ConsentRequired
            }

            val imageBytes =
                withContext(Dispatchers.IO) {
                    clientPreprocessor.process(imageUri)
                }
            Log.d("SapiKenal", "InferenceRouter: preprocessed image — ${imageBytes.size} bytes")

            return classifyPreprocessed(imageBytes, consentStatus, online)
        }

        /**
         * Classifies already-preprocessed image bytes.
         * Use this when upstream code must inspect the exact inference input first
         * (for example, the image quality gate).
         */
        suspend fun classifyPreprocessed(
            imageBytes: ByteArray,
            consentStatus: ConsentStatus,
        ): ClassifyResponse {
            val online = networkChecker.isOnline()
            Log.d("SapiKenal", "InferenceRouter: classifyPreprocessed() started, consent=$consentStatus, isOnline=$online")

            if (online && consentStatus == ConsentStatus.UNDECIDED) {
                Log.d("SapiKenal", "InferenceRouter: consent undecided while online, returning ConsentRequired")
                return ClassifyResponse.ConsentRequired
            }

            return classifyPreprocessed(imageBytes, consentStatus, online)
        }

        private suspend fun classifyPreprocessed(
            imageBytes: ByteArray,
            consentStatus: ConsentStatus,
            online: Boolean,
        ): ClassifyResponse {
            val result =
                if (online && consentStatus == ConsentStatus.ALLOWED) {
                    Log.d("SapiKenal", "InferenceRouter: routing to ONLINE (consent ALLOWED)")
                    try {
                        onlineClient.classify(imageBytes)
                    } catch (e: ClassifyFailure) {
                        Log.e("SapiKenal", "InferenceRouter: online failed, falling back to offline", e)
                        offlineEngine
                            .classify(imageBytes)
                            .copy(inferenceMode = InferenceMode.OFFLINE_FALLBACK)
                    }
                } else {
                    // !isOnline() OR consentStatus == DENIED
                    Log.d("SapiKenal", "InferenceRouter: routing to OFFLINE (online=$online, consent=$consentStatus)")
                    offlineEngine.classify(imageBytes)
                }

            return ClassifyResponse.Success(result.copy(consentStatus = consentStatus))
        }

        /**
         * Compatibility overload for callers that do not need consent-aware routing.
         * Assumes consent is ALLOWED.
         */
        suspend fun classify(imageUri: Uri): DetectionResult {
            Log.d("SapiKenal", "InferenceRouter: classify() started, uri=$imageUri")
            val imageBytes =
                withContext(Dispatchers.IO) {
                    clientPreprocessor.process(imageUri)
                }
            Log.d("SapiKenal", "InferenceRouter: preprocessed image — ${imageBytes.size} bytes")

            val online = networkChecker.isOnline()
            Log.d("SapiKenal", "InferenceRouter: isOnline=$online, routing to ${if (online) "ONLINE" else "OFFLINE"}")

            return if (online) {
                try {
                    onlineClient.classify(imageBytes)
                } catch (e: Exception) {
                    Log.e("SapiKenal", "InferenceRouter: online failed, falling back to offline", e)
                    offlineEngine.classify(imageBytes).copy(inferenceMode = InferenceMode.OFFLINE_FALLBACK)
                }
            } else {
                offlineEngine.classify(imageBytes)
            }
        }
    }
