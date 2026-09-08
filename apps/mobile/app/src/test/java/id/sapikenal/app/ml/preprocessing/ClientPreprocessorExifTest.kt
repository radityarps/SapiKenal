package id.sapikenal.app.ml.preprocessing

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import androidx.exifinterface.media.ExifInterface
import androidx.test.core.app.ApplicationProvider
import id.sapikenal.app.ml.ImagePreprocessor
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import java.io.File
import java.io.FileOutputStream

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [33], manifest = Config.NONE)
class ClientPreprocessorExifTest {
    private lateinit var context: Context
    private lateinit var preprocessor: ImagePreprocessor
    private lateinit var imageFile: File

    @Before
    fun setUp() {
        context = ApplicationProvider.getApplicationContext()
        preprocessor = ClientPreprocessor(context)
        imageFile = File.createTempFile("exif-orientation", ".jpg", context.cacheDir)
    }

    @After
    fun tearDown() {
        imageFile.delete()
    }

    @Test
    fun `process applies every supported EXIF orientation before model-size PNG output`() {
        val orientations =
            listOf(
                ExifInterface.ORIENTATION_FLIP_HORIZONTAL,
                ExifInterface.ORIENTATION_ROTATE_180,
                ExifInterface.ORIENTATION_FLIP_VERTICAL,
                ExifInterface.ORIENTATION_TRANSPOSE,
                ExifInterface.ORIENTATION_ROTATE_90,
                ExifInterface.ORIENTATION_TRANSVERSE,
                ExifInterface.ORIENTATION_ROTATE_270,
            )

        orientations.forEach { orientation ->
            writeAsymmetricImage(orientation)

            val bytes = preprocessor.process(Uri.fromFile(imageFile))
            val result = decode(bytes)

            assertEquals("orientation=$orientation width", 224, result.width)
            assertEquals("orientation=$orientation height", 224, result.height)
            assertEquals(
                "orientation=$orientation PNG signature",
                listOf(0x89, 0x50, 0x4E, 0x47),
                bytes.take(4).map(Byte::toInt).map { it and 0xFF },
            )
        }
    }

    private fun writeAsymmetricImage(orientation: Int) {
        val bitmap =
            Bitmap
                .createBitmap(
                    30,
                    20,
                    Bitmap.Config.ARGB_8888,
                ).apply {
                    for (y in 0 until height) {
                        for (x in 0 until width) {
                            val color =
                                when {
                                    y < height / 2 && x < width / 2 -> 0xFFFF0000.toInt()
                                    y < height / 2 -> 0xFF0000FF.toInt()
                                    x < width / 2 -> 0xFFFFFF00.toInt()
                                    else -> 0xFFFF00FF.toInt()
                                }
                            setPixel(x, y, color)
                        }
                    }
                }
        FileOutputStream(imageFile).use { bitmap.compress(Bitmap.CompressFormat.JPEG, 100, it) }
        ExifInterface(imageFile).apply {
            setAttribute(ExifInterface.TAG_ORIENTATION, orientation.toString())
            saveAttributes()
        }
    }

    private fun decode(bytes: ByteArray): Bitmap = requireNotNull(BitmapFactory.decodeByteArray(bytes, 0, bytes.size))
}
