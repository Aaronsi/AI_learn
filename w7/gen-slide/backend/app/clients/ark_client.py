"""Volcano Ark API client for image generation.

This module provides an async HTTP client for interacting with the Volcano Ark
Seedream image generation model API for text-to-image generation.
"""

import httpx
import logging
import base64
from typing import Tuple, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class ArkClientError(Exception):
    """Base exception for Ark API client errors."""
    pass


class ArkClient:
    """Async HTTP client for Volcano Ark API.

    This client handles authentication, request formatting, and response parsing
    for the Seedream image generation model.

    Attributes:
        api_key: Volcano Ark API authentication key
        endpoint: Base URL for API requests
        model_id: Model identifier for image generation
        timeout: Request timeout in seconds
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        model_id: Optional[str] = None,
        timeout: float = 120.0
    ):
        """Initialize the Ark API client.

        Args:
            api_key: API key (defaults to settings.ARK_API_KEY)
            endpoint: API endpoint (defaults to settings.ARK_API_ENDPOINT)
            model_id: Model ID (defaults to settings.ARK_MODEL_ID)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or settings.ARK_API_KEY
        self.endpoint = endpoint or settings.ARK_API_ENDPOINT
        self.model_id = model_id or settings.ARK_MODEL_ID
        self.timeout = timeout

    async def generate_text_to_image(
        self,
        prompt: str,
        width: int = 1920,
        height: int = 1920
    ) -> Tuple[bytes, float]:
        """Generate an image from a text prompt using Seedream model.

        Args:
            prompt: Text description of the desired image
            width: Image width in pixels (min 1920 for seedream-4.5-pro)
            height: Image height in pixels (min 1920 for seedream-4.5-pro)

        Returns:
            Tuple of (image_bytes, cost)

        Raises:
            ArkClientError: If the API request fails
        """
        url = f"{self.endpoint}/images/generations"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model_id,
            "prompt": prompt,
            "n": 1,
            "size": f"{width}x{height}",
            "response_format": "b64_json"
        }

        logger.info(f"Calling images/generations: model={self.model_id}, prompt length={len(prompt)}, size={width}x{height}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)

                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"API returned status {response.status_code}: {error_text}")
                    raise ArkClientError(f"API request failed with status {response.status_code}: {error_text}")

                data = response.json()
                logger.info(f"API response: {str(data)[:500]}")

                if "error" in data:
                    error_msg = data["error"]
                    error_message = error_msg.get("message", str(error_msg)) if isinstance(error_msg, dict) else str(error_msg)
                    logger.error(f"API error: {error_message}")
                    raise ArkClientError(f"API error: {error_message}")

                if "data" not in data or not isinstance(data["data"], list) or len(data["data"]) == 0:
                    logger.error(f"Unexpected response format: {str(data)[:500]}")
                    raise ArkClientError("Invalid API response: missing image data")

                image_data = data["data"][0]

                if "b64_json" in image_data:
                    image_bytes = base64.b64decode(image_data["b64_json"])
                    cost = 0.01
                    logger.info(f"Generated image: {len(image_bytes)} bytes")
                    return image_bytes, cost
                elif "url" in image_data:
                    image_url = image_data["url"]
                    if image_url.startswith("data:image/"):
                        base64_data = image_url.split(",", 1)[1]
                        image_bytes = base64.b64decode(base64_data)
                        cost = 0.01
                        logger.info(f"Generated image from data URL: {len(image_bytes)} bytes")
                        return image_bytes, cost
                    else:
                        # Download image from HTTP URL
                        img_response = await client.get(image_url)
                        if img_response.status_code == 200:
                            image_bytes = img_response.content
                            cost = 0.01
                            logger.info(f"Downloaded image from URL: {len(image_bytes)} bytes")
                            return image_bytes, cost
                        else:
                            raise ArkClientError(f"Failed to download image from URL: {image_url}")
                else:
                    raise ArkClientError("No image data in API response")

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise ArkClientError(f"API request failed: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            raise ArkClientError(f"Network error: {str(e)}") from e
        except ArkClientError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise ArkClientError(f"Unexpected error: {str(e)}") from e

    async def generate_image_to_image(
        self,
        prompt: str,
        reference_image: str,
        width: int = 1920,
        height: int = 1920
    ) -> Tuple[bytes, float]:
        """Generate an image from a text prompt with reference image.

        Seedream 4.5 supports reference image input for style-consistent generation.

        Args:
            prompt: Text description of the desired image
            reference_image: Base64-encoded reference image
            width: Image width in pixels (min 1920 for seedream-4.5-pro)
            height: Image height in pixels (min 1920 for seedream-4.5-pro)

        Returns:
            Tuple of (image_bytes, cost)

        Raises:
            ArkClientError: If the API request fails
        """
        url = f"{self.endpoint}/images/generations"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Format reference image as data URL
        image_data_url = f"data:image/jpeg;base64,{reference_image}"

        payload = {
            "model": self.model_id,
            "prompt": prompt,
            "image": image_data_url,
            "n": 1,
            "size": f"{width}x{height}",
            "response_format": "b64_json"
        }

        logger.info(f"Calling images/generations with reference image: model={self.model_id}, prompt length={len(prompt)}, size={width}x{height}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)

                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"API returned status {response.status_code}: {error_text}")
                    raise ArkClientError(f"API request failed with status {response.status_code}: {error_text}")

                data = response.json()
                logger.info(f"API response: {str(data)[:500]}")

                if "error" in data:
                    error_msg = data["error"]
                    error_message = error_msg.get("message", str(error_msg)) if isinstance(error_msg, dict) else str(error_msg)
                    logger.error(f"API error: {error_message}")
                    raise ArkClientError(f"API error: {error_message}")

                if "data" not in data or not isinstance(data["data"], list) or len(data["data"]) == 0:
                    logger.error(f"Unexpected response format: {str(data)[:500]}")
                    raise ArkClientError("Invalid API response: missing image data")

                image_data = data["data"][0]

                if "b64_json" in image_data:
                    image_bytes = base64.b64decode(image_data["b64_json"])
                    cost = 0.01
                    logger.info(f"Generated image with reference: {len(image_bytes)} bytes")
                    return image_bytes, cost
                elif "url" in image_data:
                    image_url = image_data["url"]
                    if image_url.startswith("data:image/"):
                        base64_data = image_url.split(",", 1)[1]
                        image_bytes = base64.b64decode(base64_data)
                        cost = 0.01
                        logger.info(f"Generated image from data URL: {len(image_bytes)} bytes")
                        return image_bytes, cost
                    else:
                        # Download image from HTTP URL
                        img_response = await client.get(image_url)
                        if img_response.status_code == 200:
                            image_bytes = img_response.content
                            cost = 0.01
                            logger.info(f"Downloaded image from URL: {len(image_bytes)} bytes")
                            return image_bytes, cost
                        else:
                            raise ArkClientError(f"Failed to download image from URL: {image_url}")
                else:
                    raise ArkClientError("No image data in API response")

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise ArkClientError(f"API request failed: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            raise ArkClientError(f"Network error: {str(e)}") from e
        except ArkClientError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise ArkClientError(f"Unexpected error: {str(e)}") from e
