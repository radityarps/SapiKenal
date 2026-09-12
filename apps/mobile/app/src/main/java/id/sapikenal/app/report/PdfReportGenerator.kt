package id.sapikenal.app.report

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Typeface
import android.graphics.pdf.PdfDocument
import android.net.Uri
import dagger.hilt.android.qualifiers.ApplicationContext
import id.sapikenal.app.BuildConfig
import id.sapikenal.app.R
import id.sapikenal.app.domain.model.BreedContract
import id.sapikenal.app.domain.model.DetectionResult
import java.io.File
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Generates a PDF identification report from a DetectionResult.
 *
 * The text content is built by [ReportContentBuilder] (a pure, testable function).
 * This class only handles the Android-specific PDF rendering.
 *
 * Includes: image, timestamp, breed class, confidence, scores, inference mode,
 * advice, disclaimer, app version, model version, preprocessing summary,
 * and consent status.
 *
 * Excludes: IMEI, serial number, account ID, location.
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
            private const val CONTENT_WIDTH = PAGE_WIDTH - (2 * MARGIN)
            private const val LINE_HEIGHT = 18f
        }

        /**
         * Generates a PDF report and saves it to the app's cache directory.
         * Returns the file path of the generated PDF, or null on failure.
         */
        fun generate(result: DetectionResult): String? =
            runCatching {
                val labels = localizedLabels()
                val content = ReportContentBuilder.build(result, BuildConfig.VERSION_NAME, labels)
                val document = PdfDocument()
                try {
                    val writer = PageWriter(document)
                    try {
                        drawHeader(writer, content.title, content.subtitle)
                        drawImage(writer, result.imagePath)
                        drawSection(writer, labels.detectionResult, content.resultLines)
                        drawSection(writer, labels.classScores, content.scoreLines, indent = true)
                        drawSection(writer, labels.technicalInformation, content.metadataLines, smallText = true)
                        drawDeviceInfo(writer, labels.device)
                        drawDisclaimer(writer, labels.disclaimer, content.disclaimerLines)
                        writer.finish()

                        val cacheDir = File(context.cacheDir, "reports")
                        if (!cacheDir.exists()) cacheDir.mkdirs()
                        val file = File(cacheDir, "report_${result.id}_${System.currentTimeMillis()}.pdf")
                        file.outputStream().use { document.writeTo(it) }
                        file.absolutePath
                    } finally {
                        writer.close()
                    }
                } finally {
                    document.close()
                }
            }.getOrNull()

        /** Owns the current page and starts a new A4 page before content crosses its bottom margin. */
        private inner class PageWriter(
            private val document: PdfDocument,
        ) {
            private var pageNumber = 0
            private var page: PdfDocument.Page = startPage()
            private var canvas: Canvas = page.canvas
            private var pageFinished = false
            private var y = MARGIN
            private val bottom = PAGE_HEIGHT - MARGIN

            // A page-break test is kept in PdfTextLayoutTest; actual rendering remains Android-native.

            private fun startPage(): PdfDocument.Page =
                document.startPage(
                    PdfDocument.PageInfo.Builder(PAGE_WIDTH, PAGE_HEIGHT, ++pageNumber).create(),
                )

            private fun finishCurrentPage() {
                if (!pageFinished) {
                    document.finishPage(page)
                    pageFinished = true
                }
            }

            private fun newPage() {
                finishCurrentPage()
                page = startPage()
                canvas = page.canvas
                pageFinished = false
                y = MARGIN
            }

            private fun ensureLine(height: Float) {
                require(height <= bottom - MARGIN) { "PDF line is taller than the page" }
                if (!PdfTextLayout.fits(y, height, bottom)) newPage()
            }

            fun finish() {
                finishCurrentPage()
            }

            fun close() {
                finishCurrentPage()
            }

            fun addSpace(height: Float) {
                if (height <= 0f) return
                if (!PdfTextLayout.fits(y, height, bottom)) newPage()
                y += height
            }

            fun drawWrapped(
                text: String,
                paint: Paint,
                lineHeight: Float,
                firstPrefix: String = "",
                continuationPrefix: String = "",
            ) {
                PdfTextLayout
                    .wrapWithPrefixes(
                        text = text,
                        maxWidth = CONTENT_WIDTH,
                        measureText = paint::measureText,
                        firstPrefix = firstPrefix,
                        continuationPrefix = continuationPrefix,
                    ).forEach { line ->
                        val metrics = paint.fontMetrics
                        val actualHeight = maxOf(lineHeight, metrics.descent - metrics.ascent)
                        ensureLine(actualHeight)
                        canvas.drawText(line, MARGIN, y - metrics.ascent, paint)
                        y += actualHeight
                    }
            }

            fun drawImage(bitmap: Bitmap) {
                var scaled: Bitmap? = null
                try {
                    val (width, height) =
                        requireNotNull(
                            PdfTextLayout.scaleWithinBounds(
                                bitmap.width,
                                bitmap.height,
                                CONTENT_WIDTH,
                                maxHeight = 200f,
                            ),
                        ) { "Bitmap dimensions must be positive" }
                    ensureLine(height.toFloat() + LINE_HEIGHT)
                    scaled = Bitmap.createScaledBitmap(bitmap, width, height, true)
                    canvas.drawBitmap(scaled, MARGIN, y, null)
                    y += height + LINE_HEIGHT
                } finally {
                    scaled?.let {
                        if (it !== bitmap && !it.isRecycled) it.recycle()
                    }
                    if (!bitmap.isRecycled) bitmap.recycle()
                }
            }
        }

        private fun drawHeader(
            writer: PageWriter,
            title: String,
            subtitle: String,
        ) {
            val titlePaint =
                Paint().apply {
                    color = Color.parseColor("#1B4332")
                    textSize = 22f
                    typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
                }
            writer.drawWrapped(title, titlePaint, LINE_HEIGHT * 1.5f)
            writer.addSpace(LINE_HEIGHT * 0.5f)

            val subtitlePaint =
                Paint().apply {
                    color = Color.GRAY
                    textSize = 10f
                }
            writer.drawWrapped(subtitle, subtitlePaint, LINE_HEIGHT)
            writer.addSpace(LINE_HEIGHT * 0.75f)
        }

        private fun drawImage(
            writer: PageWriter,
            imagePath: String?,
        ) {
            decodeBitmap(imagePath)?.let(writer::drawImage)
        }

        private fun decodeBitmap(imagePath: String?): Bitmap? {
            if (imagePath.isNullOrBlank()) return null
            return runCatching {
                if (imagePath.startsWith("content://")) {
                    context.contentResolver.openInputStream(Uri.parse(imagePath)).use { stream ->
                        stream?.let(BitmapFactory::decodeStream)
                    }
                } else {
                    BitmapFactory.decodeFile(
                        if (imagePath.startsWith("file://")) Uri.parse(imagePath).path else imagePath,
                    )
                }
            }.getOrNull()
        }

        private fun drawSection(
            writer: PageWriter,
            title: String,
            lines: List<String>,
            indent: Boolean = false,
            smallText: Boolean = false,
        ) {
            val sectionPaint =
                Paint().apply {
                    color = Color.parseColor("#1B4332")
                    textSize = 14f
                    typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
                }
            writer.drawWrapped(title, sectionPaint, LINE_HEIGHT * 1.2f)
            writer.addSpace(LINE_HEIGHT * 0.25f)

            val bodyPaint =
                Paint().apply {
                    color = if (smallText) Color.DKGRAY else Color.BLACK
                    textSize = if (smallText) 10f else 12f
                }
            lines.forEach { line ->
                writer.drawWrapped(
                    text = line,
                    paint = bodyPaint,
                    lineHeight = if (smallText) LINE_HEIGHT * 0.85f else LINE_HEIGHT,
                    firstPrefix = if (indent) "• " else "",
                    continuationPrefix = if (indent) "  " else "",
                )
            }
            writer.addSpace(LINE_HEIGHT * 0.5f)
        }

        private fun drawDeviceInfo(
            writer: PageWriter,
            label: String,
        ) {
            val bodyPaint =
                Paint().apply {
                    color = Color.DKGRAY
                    textSize = 10f
                }
            writer.drawWrapped(
                "$label: Android ${android.os.Build.VERSION.RELEASE}, ${android.os.Build.MANUFACTURER} ${android.os.Build.MODEL}",
                bodyPaint,
                LINE_HEIGHT * 0.85f,
            )
        }

        private fun drawDisclaimer(
            writer: PageWriter,
            title: String,
            lines: List<String>,
        ) {
            val disclaimerPaint =
                Paint().apply {
                    color = Color.GRAY
                    textSize = 9f
                }
            writer.drawWrapped(title, disclaimerPaint, LINE_HEIGHT * 0.75f)
            lines.forEach { line ->
                writer.drawWrapped(line, disclaimerPaint, LINE_HEIGHT * 0.75f)
            }
        }

        private fun localizedLabels(): ReportContentBuilder.ReportLabels =
            ReportContentBuilder.ReportLabels(
                title = context.getString(R.string.report_title),
                subtitle = context.getString(R.string.report_subtitle),
                date = context.getString(R.string.report_date),
                predictedClass = context.getString(R.string.report_predicted_class),
                confidence = context.getString(R.string.report_confidence),
                inferenceMode = context.getString(R.string.report_inference_mode),
                online = context.getString(R.string.result_mode_online),
                offline = context.getString(R.string.result_mode_offline),
                offlineFallback = context.getString(R.string.result_mode_offline_fallback),
                unknown = context.getString(R.string.result_mode_unknown),
                appVersion = context.getString(R.string.report_app_version),
                modelVersion = context.getString(R.string.report_model_version),
                processingTime = context.getString(R.string.report_processing_time),
                preprocessing = context.getString(R.string.report_preprocessing),
                imageSource = context.getString(R.string.report_image_source),
                camera = context.getString(R.string.result_source_camera),
                gallery = context.getString(R.string.result_source_gallery),
                recordTitle = context.getString(R.string.report_record_title),
                recordDescription = context.getString(R.string.report_record_description),
                consentStatus = context.getString(R.string.report_consent_status),
                allowed = context.getString(R.string.report_allowed),
                denied = context.getString(R.string.report_denied),
                undecided = context.getString(R.string.report_undecided),
                detectionResult = context.getString(R.string.report_detection_result),
                classScores = context.getString(R.string.report_class_scores),
                technicalInformation = context.getString(R.string.report_technical_information),
                device = context.getString(R.string.report_device),
                disclaimer = context.getString(R.string.report_disclaimer),
                objectValidationLimitation = context.getString(R.string.report_object_validation_limitation),
                identityDocumentLimitation = context.getString(R.string.report_not_official_document),
                supportedBreedsLimitation = context.getString(R.string.report_supported_breeds_limitation),
                generatedBy = context.getString(R.string.report_generated_by),
                classLabels = BreedContract.definitions.associate { it.key to context.getString(it.displayNameResId) },
            )
    }
