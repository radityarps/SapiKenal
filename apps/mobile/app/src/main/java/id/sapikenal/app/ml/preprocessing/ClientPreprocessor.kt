package id.sapikenal.app.ml.preprocessing

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import android.net.Uri
import androidx.exifinterface.media.ExifInterface
import dagger.hilt.android.qualifiers.ApplicationContext
import id.sapikenal.app.ml.ImagePreprocessor
import java.io.ByteArrayOutputStream
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
open class ClientPreprocessor
    @Inject
    constructor(
        @ApplicationContext private val context: Context,
    ) : ImagePreprocessor {
        open override fun process(imageUri: Uri): ByteArray {
            val bitmap = decodeBitmap(imageUri)
            val corrected = correctOrientation(bitmap, imageUri)
            val resized = resize(corrected, maxDimension = 800)

            val output = ByteArrayOutputStream()
            resized.compress(Bitmap.CompressFormat.JPEG, 85, output)
            return output.toByteArray()
        }

        private fun decodeBitmap(uri: Uri): Bitmap =
            context.contentResolver.openInputStream(uri)?.use {
                BitmapFactory.decodeStream(it)
            } ?: throw IllegalArgumentException("Unable to read image")

        private fun correctOrientation(
            bitmap: Bitmap,
            uri: Uri,
        ): Bitmap {
            val exif = context.contentResolver.openInputStream(uri)?.use { ExifInterface(it) } ?: return bitmap
            val orientation =
                exif.getAttributeInt(
                    ExifInterface.TAG_ORIENTATION,
                    ExifInterface.ORIENTATION_NORMAL,
                )
            val matrix =
                Matrix().apply {
                    when (orientation) {
                        ExifInterface.ORIENTATION_FLIP_HORIZONTAL -> {
                            postScale(-1f, 1f)
                        }

                        ExifInterface.ORIENTATION_ROTATE_180 -> {
                            postRotate(180f)
                        }

                        ExifInterface.ORIENTATION_FLIP_VERTICAL -> {
                            postScale(1f, -1f)
                        }

                        ExifInterface.ORIENTATION_TRANSPOSE -> {
                            postRotate(90f)
                            postScale(-1f, 1f)
                        }

                        ExifInterface.ORIENTATION_ROTATE_90 -> {
                            postRotate(90f)
                        }

                        ExifInterface.ORIENTATION_TRANSVERSE -> {
                            postRotate(270f)
                            postScale(-1f, 1f)
                        }

                        ExifInterface.ORIENTATION_ROTATE_270 -> {
                            postRotate(270f)
                        }

                        else -> {
                            return bitmap
                        }
                    }
                }
            return Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true)
        }

        private fun resize(
            bitmap: Bitmap,
            maxDimension: Int,
        ): Bitmap {
            val width = bitmap.width
            val height = bitmap.height
            if (width <= maxDimension && height <= maxDimension) return bitmap

            val ratio = minOf(maxDimension.toFloat() / width, maxDimension.toFloat() / height)
            return Bitmap.createScaledBitmap(bitmap, (width * ratio).toInt(), (height * ratio).toInt(), true)
        }
    }
