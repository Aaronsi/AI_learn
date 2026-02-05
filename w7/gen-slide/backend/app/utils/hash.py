"""Blake3 hashing utility for content-based image identification.

This module provides fast, cryptographic hashing using the Blake3 algorithm
to generate unique identifiers for slide content.
"""

import blake3


def compute_blake3_hash(content: str) -> str:
    """Compute a Blake3 hash of the given content.

    Args:
        content: The string content to hash

    Returns:
        A 16-character hexadecimal hash string (first 16 chars of full hash)

    Example:
        >>> compute_blake3_hash("Hello, World!")
        'a2764d133a16816b'
    """
    hasher = blake3.blake3(content.encode('utf-8'))
    return hasher.hexdigest()[:16]
