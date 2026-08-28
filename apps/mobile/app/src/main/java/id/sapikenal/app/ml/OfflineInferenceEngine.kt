package id.sapikenal.app.ml

import android.content.Context
import dagger.hilt.android.qualifiers.ApplicationContext
import id.sapikenal.app.BuildConfig
import id.sapikenal.app.domain.model.DetectionResult
import id.sapikenal.app.domain.model.InferenceMode
import id.sapikenal.app.ml.preprocessing.ModelPreprocessor
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.tensorflow.lite.DataType
import org.tensorflow.lite.Interpreter
import java.nio.ByteBuffer
import java.nio.ByteOrder
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.math.abs

@Singleton
open class OfflineInferenceEngine
    @Inject
    constructor(
        @ApplicationContext private val context: Context,
        private val modelPreprocessor: ModelPreprocessor,
    ) : ImageClassifier {
        companion object {
            private val MODEL_FILE = BuildConfig.MODEL_FILE_NAME

            /** Offline model version identifier. Configured via BuildConfig / local.properties. */
            val MODEL_VERSION = BuildConfig.MODEL_VERSION
            private val EXPECTED_INPUT_SHAPE = intArrayOf(1, 224, 224, 3)
            private val EXPECTED_OUTPUT_SHAPE = intArrayOf(1, 4)

            // Canonical labels matching backend class_names.json: {"0": "FMD", "1": "Healthy", "2": "LSD", "3": "non_cattle"}
            private val LABELS = listOf("FMD", "healthy", "LSD", "non_cattle")
            private val LABEL_DISPLAY =
                mapOf(
                    "FMD" to "Penyakit Mulut dan Kuku (FMD)",
                    "LSD" to "Penyakit Lumpy Skin (LSD)",
                    "healthy" to "Sapi Sehat",
                    "Healthy" to "Sapi Sehat",
                    "non_cattle" to "Objek bukan sapi",
                )
        }

        private val interpreter: Interpreter by lazy {
            val bytes = context.assets.open(MODEL_FILE).use { it.readBytes() }
            val modelBuffer =
                ByteBuffer.allocateDirect(bytes.size).apply {
                    order(ByteOrder.nativeOrder())
                    put(bytes)
                }
            modelBuffer.rewind()
            Interpreter(modelBuffer, Interpreter.Options().apply { numThreads = 4 }).also { interp ->
                validateTensorContract(interp)
            }
        }

        private fun validateTensorContract(interpreter: Interpreter) {
            if (interpreter.inputTensorCount != 1 || interpreter.outputTensorCount != 1) {
                throw IllegalStateException(
                    "TFLite tensor count mismatch: expected one input and one output, " +
                        "got ${interpreter.inputTensorCount} input(s) and ${interpreter.outputTensorCount} output(s)",
                )
            }

            val inputTensor = interpreter.getInputTensor(0)
            if (!inputTensor.shape().contentEquals(EXPECTED_INPUT_SHAPE)) {
                throw IllegalStateException(
                    "TFLite input shape mismatch: expected [${EXPECTED_INPUT_SHAPE.joinToString()}], " +
                        "got [${inputTensor.shape().joinToString()}]",
                )
            }
            if (inputTensor.dataType() != DataType.FLOAT32) {
                throw IllegalStateException(
                    "TFLite input dtype mismatch: expected FLOAT32, got ${inputTensor.dataType()}",
                )
            }

            val outputTensor = interpreter.getOutputTensor(0)
            if (!outputTensor.shape().contentEquals(EXPECTED_OUTPUT_SHAPE)) {
                throw IllegalStateException(
                    "TFLite output shape mismatch: expected [${EXPECTED_OUTPUT_SHAPE.joinToString()}], " +
                        "got [${outputTensor.shape().joinToString()}]",
                )
            }
            if (outputTensor.dataType() != DataType.FLOAT32) {
                throw IllegalStateException(
                    "TFLite output dtype mismatch: expected FLOAT32, got ${outputTensor.dataType()}",
                )
            }
        }

        private fun validateScores(scores: FloatArray) {
            if (scores.size != LABELS.size || scores.any { !it.isFinite() || it < 0f || it > 1f }) {
                throw IllegalStateException("TFLite output must contain four finite probabilities in [0, 1]")
            }
            if (abs(scores.sum() - 1f) > 0.01f) {
                throw IllegalStateException("TFLite output probabilities must sum to 1")
            }
        }

        open override suspend fun classify(jpegBytes: ByteArray): DetectionResult =
            withContext(Dispatchers.Default) {
                val inputBuffer = modelPreprocessor.process(jpegBytes)
                val output = Array(1) { FloatArray(4) }
                interpreter.run(inputBuffer, output)

                val scores = output[0]
                validateScores(scores)
                val maxIdx = scores.indices.maxByOrNull { scores[it] } ?: 0
                val label = LABELS.getOrElse(maxIdx) { "unknown" }
                val isRejected = label == "non_cattle"

                DetectionResult(
                    label = label,
                    displayLabel = LABEL_DISPLAY[label] ?: label,
                    confidence = scores[maxIdx],
                    isReliable = if (isRejected) false else scores[maxIdx] >= BuildConfig.CONFIDENCE_THRESHOLD,
                    allScores =
                        mapOf(
                            "FMD" to scores[0],
                            "healthy" to scores[1],
                            "LSD" to scores[2],
                            "non_cattle" to scores[3],
                        ),
                    inferenceMode = InferenceMode.OFFLINE,
                    modelVersion = MODEL_VERSION,
                    outcome = if (isRejected) "REJECTED" else "ACCEPTED",
                    rejectionReason = if (isRejected) "non_cattle" else null,
                )
            }
    }
