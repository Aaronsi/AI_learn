import { blake3 } from '@noble/hashes/blake3.js';
import { bytesToHex } from '@noble/hashes/utils.js';

/**
 * Compute Blake3 hash of content (first 16 hex characters)
 * Used to generate unique identifiers for slide content
 */
export function computeBlake3Hash(content: string): string {
  const hash = blake3(new TextEncoder().encode(content));
  return bytesToHex(hash).slice(0, 16);
}
