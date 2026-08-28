package id.sapikenal.app.ml.preprocessing

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import id.sapikenal.app.BuildConfig
import java.nio.ByteBuffer
import java.nio.ByteOrder
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ModelPreprocessor
    @Inject
    constructor() {
        companion object {
            val INPUT_SIZE = BuildConfig.MODEL_INPUT_SIZE
        }

        fun process(jpegBytes: ByteArray): ByteBuffer {
            val bitmap =
                BitmapFactory.decodeByteArray(jpegBytes, 0, jpegBytes.size)
                    ?: throw IllegalArgumentException("Unable to decode image bytes")
            val resized = Bitmap.createScaledBitmap(bitmap, INPUT_SIZE, INPUT_SIZE, true)

            val input = ByteBuffer.allocateDirect(4 * INPUT_SIZE * INPUT_SIZE * 3)
            input.order(ByteOrder.nativeOrder())

            val pixels = IntArray(INPUT_SIZE * INPUT_SIZE)
            resized.getPixels(pixels, 0, INPUT_SIZE, 0, 0, INPUT_SIZE, INPUT_SIZE)

            // Raw float32 in [0, 255] range — matches backend model_preprocessor.py
            // MobileNetV3 model includes internal Rescaling layer ((x / 127.5) - 1.0)
            for (pixel in pixels) {
                input.putFloat((pixel shr 16 and 0xFF).toFloat())
                input.putFloat((pixel shr 8 and 0xFF).toFloat())
                input.putFloat((pixel and 0xFF).toFloat())
            }

            input.rewind()
            return input
        }
    }
