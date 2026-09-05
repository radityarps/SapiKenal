"""Image preprocessing module - Tahap 2 (Model preprocessing)."""

import numpy as np  # pyright: ignore[reportMissingImports]
from PIL import Image

from utils.errors import PreprocessingError
from utils.logger import get_logger

logger = get_logger(__name__)


class ModelPreprocessor:
    """
    Tahap 2 Preprocessing: Convert image to model-ready numpy array.

    Steps:
    1. Resize to 224x224 (TF model input size)
    2. Convert to float32 in [0, 255] range (MobileNetV3 internal Rescaling layer)
    """

    # Constants
    INPUT_SIZE = 224

    @staticmethod
    def process(image: Image.Image | np.ndarray) -> np.ndarray:
        """
        Process image to model-ready numpy array.

        Args:
            image: PIL Image or numpy array (must be RGB)

        Returns:
            numpy array of shape (1, 224, 224, 3), dtype float32, values in [0, 255]

        Raises:
            PreprocessingError: If image processing fails
        """
        try:
            # Ensure PIL Image
            if isinstance(image, np.ndarray):
                image = Image.fromarray(np.asarray(image, dtype=np.uint8), "RGB")
            elif not isinstance(image, Image.Image):
                raise PreprocessingError(f"Unsupported image type: {type(image)}")

            # Ensure RGB
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Match TensorFlow/TFLite's explicit bilinear inference contract.
            image = image.resize(
                (ModelPreprocessor.INPUT_SIZE, ModelPreprocessor.INPUT_SIZE),
                Image.Resampling.BILINEAR,
            )

            # Convert to float32 numpy array in [0, 255] range.
            # MobileNetV3 in Keras includes an internal Rescaling layer ((x / 127.5) - 1.0),
            # so input array must not be pre-divided by 255.0.
            array = np.array(image, dtype=np.float32)

            # Add batch dimension: (224, 224, 3) -> (1, 224, 224, 3)
            array = np.expand_dims(array, axis=0)

            logger.debug(f"Preprocessed image array shape: {array.shape}")

            return array

        except Exception as e:
            raise PreprocessingError(f"Image preprocessing failed: {str(e)}") from e
