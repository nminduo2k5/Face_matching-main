import cv2
import numpy as np
import onnxruntime
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

__all__ = ["RealESRGAN"]

class RealESRGAN:
    def __init__(self, model_path: str = None, session=None, input_mean=0.5, input_std=0.5) -> None:
        """
        Initialize RealESRGAN.
        - model_path: Path to the ONNX model (if no session is provided).
        - session: Pre-created ONNX Runtime session (if available).
        - input_mean: Mean value for input normalization.
        - input_std: Standard deviation for input normalization.
        """
        if session is None:
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found: {model_path}")
            self.session = onnxruntime.InferenceSession(
                model_path,
                providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
            )
        else:
            self.session = session

        self.input_mean = input_mean
        self.input_std = input_std
        self.taskname = "super_resolution"

        # Get input configuration
        input_cfg = self.session.get_inputs()[0]
        self.input_name = input_cfg.name
        self.input_size = tuple(input_cfg.shape[2:4][::-1])  # (width, height)

        # Get output configuration
        outputs = self.session.get_outputs()
        self.output_names = [output.name for output in outputs]
        assert len(self.output_names) == 1, "Model should have exactly one output."
        self.output_shape = outputs[0].shape

        logger.info(f"Initialized RealESRGAN with input size: {self.input_size}")

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess the input image (resize, normalize, and convert to CHW format).
        """
        if len(image.shape) != 3 or image.shape[2] != 3:
            raise ValueError(f"Expected image to be of shape (height, width, 3), but got {image.shape}")

        # Resize image to model's expected input size
        image = cv2.resize(image, self.input_size)

        # Normalize image
        image = image.astype(np.float32) / 255.0
        image = (image - self.input_mean) / self.input_std

        # Add batch dimension and convert to CHW format
        image = np.expand_dims(image, axis=0)
        image = np.transpose(image, (0, 3, 1, 2))
        return image

    def get_sr_image(self, image: np.ndarray) -> np.ndarray:
        """
        Run the ONNX model to perform super-resolution.
        """
        blob = self.preprocess_image(image)
        outputs = self.session.run(self.output_names, {self.input_name: blob})[0]
        return outputs

    def __call__(self, image: np.ndarray, output_format: str = "uint8") -> np.ndarray:
        """
        Perform super-resolution on the input image.
        - image: Input image (numpy array).
        - output_format: Desired output format ("uint8" or "float").
"""
        sr_image = self.get_sr_image(image)

        # Convert from CHW to HWC
        sr_image = np.transpose(sr_image, (0, 2, 3, 1))
        sr_image = sr_image[0]  # Remove batch dimension

        # Convert to desired output format
        if output_format == "uint8":
            sr_image = np.clip(sr_image * 255.0, 0, 255).astype(np.uint8)
        elif output_format == "float":
            sr_image = np.clip(sr_image, 0, 1)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

        return sr_image