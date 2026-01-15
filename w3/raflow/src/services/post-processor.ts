/**
 * Text Post-Processor
 *
 * Handles text correction including term mapping and course correction
 */

// ============================================================================
// Post-Processor Class
// ============================================================================

export class TextPostProcessor {
  private termMapping: Map<string, string>;

  constructor(customTerms: Record<string, string> = {}) {
    // Default technical terms
    this.termMapping = new Map([
      // Technology names
      ['view cell', 'Vercel'],
      ['super base', 'Supabase'],
      ['react js', 'React.js'],
      ['react j s', 'React.js'],
      ['type script', 'TypeScript'],
      ['java script', 'JavaScript'],
      ['next js', 'Next.js'],
      ['tail wind', 'Tailwind'],
      ['docker', 'Docker'],
      ['kubernetes', 'Kubernetes'],

      // Programming concepts
      ['camel case', 'camelCase'],
      ['snake case', 'snake_case'],
      ['kebab case', 'kebab-case'],
      ['pascal case', 'PascalCase'],

      // Rust specific
      ['rust', 'Rust'],
      ['cargo', 'Cargo'],
      ['crate', 'crate'],

      // Add custom terms
      ...Object.entries(customTerms),
    ]);
  }

  /**
   * Process text with all corrections
   */
  process(text: string, enableTermCorrection = true, enableCourseCorrection = true): string {
    let result = text;

    if (enableCourseCorrection) {
      const corrected = this.detectCourseCorrection(result);
      if (corrected.corrected) {
        result = corrected.text;
      }
    }

    if (enableTermCorrection) {
      result = this.applyTermCorrection(result);
    }

    return result.trim();
  }

  /**
   * Apply term mapping corrections
   */
  private applyTermCorrection(text: string): string {
    let result = text;

    this.termMapping.forEach((correct, wrong) => {
      // Case-insensitive replacement
      const regex = new RegExp(wrong, 'gi');
      result = result.replace(regex, correct);
    });

    return result;
  }

  /**
   * Detect and apply course correction
   * Handles patterns like "tomorrow, no, day after tomorrow"
   */
  private detectCourseCorrection(text: string): { text: string; corrected: boolean } {
    const patterns = [
      // Chinese patterns
      /(.+?)[，,]\s*不[，,]\s*(.+)/,           // "明天，不，后天"
      /(.+?)[，,]\s*我是说\s*(.+)/,            // "三点，我是说四点"
      /(.+?)[，,]\s*应该是\s*(.+)/,            // "周一，应该是周二"
      /(.+?)[，,]\s*不对[，,]\s*(.+)/,         // "星期一，不对，星期二"

      // English patterns
      /(.+?),\s*no,\s*(.+)/i,                  // "tomorrow, no, next week"
      /(.+?),\s*I mean\s*(.+)/i,               // "three, I mean four"
      /(.+?),\s*actually\s*(.+)/i,             // "Monday, actually Tuesday"
      /(.+?),\s*wait,\s*(.+)/i,                // "five, wait, six"
    ];

    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match && match[2]) {
        return {
          text: match[2].trim(),
          corrected: true,
        };
      }
    }

    return {
      text,
      corrected: false,
    };
  }

  /**
   * Add custom term mapping
   */
  addTermMapping(wrong: string, correct: string): void {
    this.termMapping.set(wrong, correct);
  }

  /**
   * Remove term mapping
   */
  removeTermMapping(wrong: string): void {
    this.termMapping.delete(wrong);
  }

  /**
   * Get all term mappings
   */
  getTermMappings(): Map<string, string> {
    return new Map(this.termMapping);
  }

  /**
   * Update custom terms
   */
  updateCustomTerms(customTerms: Record<string, string>): void {
    Object.entries(customTerms).forEach(([wrong, correct]) => {
      this.termMapping.set(wrong, correct);
    });
  }
}

// ============================================================================
// Export singleton instance
// ============================================================================

export const textPostProcessor = new TextPostProcessor();
