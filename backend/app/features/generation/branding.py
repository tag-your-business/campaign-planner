"""Overlays company branding (logo, colors) onto a generated image."""

import logging
from pathlib import Path

from PIL import Image

logger = logging.getLogger(__name__)


class BrandingService:
    """Applies company branding (logo overlay) to generated images using Pillow."""

    def apply(
        self, image_path: Path, logo_path: Path | None, output_path: Path
    ) -> Path:
        """
        Overlay company logo on the bottom-right corner of an image.

        Args:
            image_path: Path to the base image
            logo_path: Path to the logo image (optional)
            output_path: Path where branded image will be saved

        Returns:
            Path to the output image

        The logo is resized to 10% of the image width and placed in the
        bottom-right corner with 20px padding. If no logo is provided,
        the image is copied as-is.
        """
        try:
            # Open the base image
            base_image = Image.open(image_path).convert("RGBA")

            # If no logo provided, save the base image and return
            if logo_path is None or not logo_path.exists():
                if logo_path is not None:
                    logger.warning(
                        f"Logo not found at {logo_path}, continuing without branding"
                    )
                # Convert back to RGB for PNG save
                rgb_image = base_image.convert("RGB")
                rgb_image.save(output_path, "PNG")
                return output_path

            # Open and process logo
            logo = Image.open(logo_path).convert("RGBA")

            # Calculate logo size (10% of image width)
            base_width = base_image.width
            logo_width = int(base_width * 0.1)

            # Resize logo maintaining aspect ratio
            aspect_ratio = logo.height / logo.width
            logo_height = int(logo_width * aspect_ratio)
            logo_resized = logo.resize(
                (logo_width, logo_height), Image.Resampling.LANCZOS
            )

            # Calculate position (bottom-right with 20px padding)
            padding = 20
            position = (
                base_width - logo_width - padding,
                base_image.height - logo_height - padding,
            )

            # Create a copy of base image and paste logo
            branded_image = base_image.copy()
            branded_image.paste(logo_resized, position, logo_resized)

            # Convert to RGB and save
            rgb_image = branded_image.convert("RGB")
            rgb_image.save(output_path, "PNG")

            logger.info(f"Applied branding to image: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"Failed to apply branding: {e}")
            # Fallback: copy original image
            try:
                base_image = Image.open(image_path).convert("RGB")
                base_image.save(output_path, "PNG")
                logger.warning("Saved image without branding due to error")
            except Exception as fallback_error:
                logger.error(f"Failed to save fallback image: {fallback_error}")
                raise

            return output_path
