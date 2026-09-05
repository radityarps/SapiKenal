package id.sapikenal.app.report

import android.content.Context
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Typeface
import android.graphics.pdf.PdfDocument
import dagger.hilt.android.qualifiers.ApplicationContext
import id.sapikenal.app.BuildConfig
import id.sapikenal.app.R
import id.sapikenal.app.domain.model.DetectionResult
import java.io.File
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Generates a PDF detection report from a DetectionResult.
 *
 * The text content is built by [ReportContentBuilder] (a pure, testable function).
 * This class only handles the Android-specific PDF rendering.
 *
 * Includes: image, timestamp, breed class, confidence, scores, inference mode,
 * advice, disclaimer, app version, model version, preprocessing summary,
 * consent status, and coarse location (if available).
 *
 * Excludes: IMEI, serial number, account ID, precise location.
 * Wording states breed-identification and object-validation limitations.
 */
@Singleton
class PdfReportGenerator
    @Inject
    constructor(
        @ApplicationContext private val context: Context,
    ) {
        companion object {
            private const val PAGE_WIDTH = 595 // A4 in points
            private const val PAGE_HEIGHT = 842
            private const val MARGIN = 40f
            private const val LINE_HEIGHT = 18f
        }

        /**
         * Generates a PDF report and saves it to the app's cache directory.
         * Returns the file path of the generated PDF, or null on failure.
         */
        fun generate(result: DetectionResult): String? =
            runCatching {
                // Build the textual content using the current app locale.
                val labels = localizedLabels()
                val content = ReportContentBuilder.build(result, BuildConfig.VERSION_NAME, labels)

                val document = PdfDocument()
                val pageInfo = PdfDocument.PageInfo.Builder(PAGE_WIDTH, PAGE_HEIGHT, 1).create()
                val page = document.startPage(pageInfo)
                val canvas = page.canvas

                var y = MARGIN
                y = drawHeader(canvas, y, content.title, content.subtitle)
                y = drawImage(canvas, y, result.imagePath)
                y = drawSection(canvas, y, labels.detectionResult, content.resultLines)
                y = drawSection(canvas, y, labels.classScores, content.scoreLines, indent = true)
                y = drawSection(canvas, y, labels.technicalInformation, content.metadataLines, smallText = true)
                // Append non-identifying device info to metadata visually
                y = drawDeviceInfo(canvas, y, labels.device)
                y = drawDisclaimer(canvas, y, labels.disclaimer, content.disclaimerLines)

                document.finishPage(page)

                val cacheDir = File(context.cacheDir, "reports")
                if (!cacheDir.exists()) cacheDir.mkdirs()
                val file = File(cacheDir, "report_${result.id}_${System.currentTimeMillis()}.pdf")
                file.outputStream().use { document.writeTo(it) }
                document.close()

                file.absolutePath
            }.getOrNull()

        private fun drawHeader(
            canvas: Canvas,
            startY: Float,
            title: String,
            subtitle: String,
        ): Float {
            var y = startY
            val titlePaint =
                Paint().apply {
                    color = Color.parseColor("#1B4332")
                    textSize = 22f
                    typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
                }
            canvas.drawText(title, MARGIN, y, titlePaint)
            y += LINE_HEIGHT * 1.5f

            val subtitlePaint =
                Paint().apply {
                    color = Color.GRAY
                    textSize = 10f
                }
            canvas.drawText(subtitle, MARGIN, y, subtitlePaint)
            y += LINE_HEIGHT * 1.5f
            return y
        }

        private fun drawImage(
            canvas: Canvas,
            startY: Float,
            imagePath: String?,
        ): Float {
            var y = startY
            if (imagePath != null) {
                val file = File(imagePath)
                if (file.exists()) {
                    val bitmap = BitmapFactory.decodeFile(imagePath)
                    if (bitmap != null) {
                        val maxWidth = PAGE_WIDTH - 2 * MARGIN.toInt()
                        val maxHeight = 200
                        val scale =
                            minOf(
                                maxWidth.toFloat() / bitmap.width,
                                maxHeight.toFloat() / bitmap.height,
                            )
                        val scaledWidth = (bitmap.width * scale).toInt()
                        val scaledHeight = (bitmap.height * scale).toInt()
                        val scaled = android.graphics.Bitmap.createScaledBitmap(bitmap, scaledWidth, scaledHeight, true)
                        canvas.drawBitmap(scaled, MARGIN, y, null)
                        y += scaledHeight + LINE_HEIGHT
                        bitmap.recycle()
                        scaled.recycle()
                    }
                }
            }
            return y
        }

        private fun drawSection(
            canvas: Canvas,
            startY: Float,
            title: String,
            lines: List<String>,
            indent: Boolean = false,
            smallText: Boolean = false,
        ): Float {
            var y = startY
            val sectionPaint =
                Paint().apply {
                    color = Color.parseColor("#1B4332")
                    textSize = 14f
                    typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
                }
            val bodyPaint =
                Paint().apply {
                    color = if (smallText) Color.DKGRAY else Color.BLACK
                    textSize = if (smallText) 10f else 12f
                }

            canvas.drawText(title, MARGIN, y, sectionPaint)
            y += LINE_HEIGHT * 1.3f

            val xOffset = if (indent) MARGIN + 10f else MARGIN
            val prefix = if (indent) "• " else ""
            lines.forEach { line ->
                canvas.drawText("$prefix$line", xOffset, y, bodyPaint)
                y += LINE_HEIGHT
            }
            y += LINE_HEIGHT * 0.5f

            return y
        }

        private fun drawDeviceInfo(
            canvas: Canvas,
            startY: Float,
            label: String,
        ): Float {
            var y = startY
            val bodyPaint =
                Paint().apply {
                    color = Color.DKGRAY
                    textSize = 10f
                }
            // Non-identifying device info only — no IMEI, serial, or account ID
            canvas.drawText(
                "$label: Android ${android.os.Build.VERSION.RELEASE}, ${android.os.Build.MANUFACTURER} ${android.os.Build.MODEL}",
                MARGIN,
                y,
                bodyPaint,
            )
            y += LINE_HEIGHT * 1.5f
            return y
        }

        private fun drawDisclaimer(
            canvas: Canvas,
            startY: Float,
            title: String,
            lines: List<String>,
        ): Float {
            var y = startY
            val disclaimerPaint =
                Paint().apply {
                    color = Color.GRAY
                    textSize = 9f
                }

            canvas.drawText(title, MARGIN, y, disclaimerPaint)
            y += LINE_HEIGHT * 0.8f
            lines.forEach { line ->
                canvas.drawText(line, MARGIN, y, disclaimerPaint)
                y += LINE_HEIGHT * 0.8f
            }
            return y
        }

        private fun localizedLabels(): ReportContentBuilder.ReportLabels =
            ReportContentBuilder.ReportLabels(
                title = context.getString(R.string.report_title),
                subtitle = context.getString(R.string.report_subtitle),
                date = context.getString(R.string.report_date),
                predictedClass = context.getString(R.string.report_predicted_class),
                confidence = context.getString(R.string.report_confidence),
                reliable = context.getString(R.string.report_reliable),
                yes = context.getString(R.string.report_yes),
                no = context.getString(R.string.report_no),
                inferenceMode = context.getString(R.string.report_inference_mode),
                online = context.getString(R.string.result_mode_online),
                offline = context.getString(R.string.result_mode_offline),
                appVersion = context.getString(R.string.report_app_version),
                modelVersion = context.getString(R.string.report_model_version),
                preprocessing = context.getString(R.string.report_preprocessing),
                consentStatus = context.getString(R.string.report_consent_status),
                allowed = context.getString(R.string.report_allowed),
                denied = context.getString(R.string.report_denied),
                undecided = context.getString(R.string.report_undecided),
                coarseLocation = context.getString(R.string.report_coarse_location),
                gps = context.getString(R.string.result_location_source_gps),
                manual = context.getString(R.string.result_location_source_manual),
                detectionResult = context.getString(R.string.report_detection_result),
                classScores = context.getString(R.string.report_class_scores),
                technicalInformation = context.getString(R.string.report_technical_information),
                device = context.getString(R.string.report_device),
                disclaimer = context.getString(R.string.report_disclaimer),
                objectValidationLimitation = context.getString(R.string.report_not_clinical_diagnosis),
                identityDocumentLimitation = context.getString(R.string.report_not_official_document),
                supportedBreedsLimitation = context.getString(R.string.report_consult_veterinarian),
                generatedBy = context.getString(R.string.report_generated_by),
                classLabels =
                    mapOf(
                        "bali" to context.getString(R.string.result_breed_bali),
                        "brahman" to context.getString(R.string.result_breed_brahman),
                        "brangus" to context.getString(R.string.result_breed_brangus),
                        "limusin" to context.getString(R.string.result_breed_limusin),
                    ),
            )
    }
