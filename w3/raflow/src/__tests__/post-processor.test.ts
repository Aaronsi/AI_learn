/**
 * Text Post-Processor Tests
 *
 * Phase 5: Unit tests for text post-processing
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { TextPostProcessor } from '../services/post-processor';

describe('TextPostProcessor', () => {
  let processor: TextPostProcessor;

  beforeEach(() => {
    processor = new TextPostProcessor();
  });

  describe('Term Mapping', () => {
    it('should replace technical terms correctly', () => {
      const input = 'I use view cell for deployment';
      const output = processor.process(input);
      expect(output).toBe('I use Vercel for deployment');
    });

    it('should handle multiple term replacements', () => {
      const input = 'react js and type script with next js';
      const output = processor.process(input);
      expect(output).toContain('React.js');
      expect(output).toContain('TypeScript');
      expect(output).toContain('Next.js');
    });

    it('should be case-insensitive', () => {
      const input = 'Using VIEW CELL and Super Base';
      const output = processor.process(input);
      expect(output).toContain('Vercel');
      expect(output).toContain('Supabase');
    });

    it('should handle programming case terms', () => {
      const input = 'use camel case and snake case';
      const output = processor.process(input);
      expect(output).toContain('camelCase');
      expect(output).toContain('snake_case');
    });

    it('should handle empty input', () => {
      const output = processor.process('');
      expect(output).toBe('');
    });

    it('should handle text without replaceable terms', () => {
      const input = 'This is a normal sentence';
      const output = processor.process(input);
      expect(output).toBe('This is a normal sentence');
    });
  });

  describe('Course Correction', () => {
    it('should detect Chinese correction pattern - 不', () => {
      const input = '明天，不，后天';
      const output = processor.process(input);
      expect(output).toBe('后天');
    });

    it('should detect Chinese correction pattern - 应该是', () => {
      const input = '三点，应该是四点';
      const output = processor.process(input);
      expect(output).toBe('四点');
    });

    it('should detect Chinese correction pattern - 我是说', () => {
      const input = '星期一，我是说星期二';
      const output = processor.process(input);
      expect(output).toBe('星期二');
    });

    it('should detect English correction pattern - no', () => {
      const input = 'tomorrow, no, next week';
      const output = processor.process(input);
      expect(output).toBe('next week');
    });

    it('should detect English correction pattern - I mean', () => {
      const input = 'three, I mean four';
      const output = processor.process(input);
      expect(output).toBe('four');
    });

    it('should detect English correction pattern - actually', () => {
      const input = 'Monday, actually Tuesday';
      const output = processor.process(input);
      expect(output).toBe('Tuesday');
    });

    it('should not apply correction to normal text', () => {
      const input = 'This is a normal sentence without correction';
      const output = processor.process(input);
      expect(output).toBe('This is a normal sentence without correction');
    });
  });

  describe('Custom Terms', () => {
    it('should add custom term mapping', () => {
      processor.addTermMapping('my term', 'MyTerm');
      const output = processor.process('I use my term here');
      expect(output).toContain('MyTerm');
    });

    it('should remove term mapping', () => {
      processor.addTermMapping('test term', 'TestTerm');
      processor.removeTermMapping('test term');
      const output = processor.process('test term');
      expect(output).toBe('test term');
    });

    it('should update multiple custom terms at once', () => {
      processor.updateCustomTerms({
        'custom one': 'CustomOne',
        'custom two': 'CustomTwo',
      });
      const output = processor.process('custom one and custom two');
      expect(output).toContain('CustomOne');
      expect(output).toContain('CustomTwo');
    });

    it('should get all term mappings', () => {
      const mappings = processor.getTermMappings();
      expect(mappings).toBeInstanceOf(Map);
      expect(mappings.size).toBeGreaterThan(0);
    });
  });

  describe('Combined Processing', () => {
    it('should apply both term mapping and course correction', () => {
      const input = 'using view cell, no, super base';
      const output = processor.process(input);
      // Course correction should extract "super base"
      // Then term mapping should replace it with "Supabase"
      expect(output).toContain('Supabase');
    });

    it('should handle complex sentences', () => {
      const input = 'Deploy with view cell and use type script, wait, react js';
      const output = processor.process(input);
      expect(output).toContain('React.js');
    });
  });

  describe('Control Flags', () => {
    it('should skip term correction when disabled', () => {
      const input = 'view cell';
      const output = processor.process(input, false, true);
      expect(output).toBe('view cell');
    });

    it('should skip course correction when disabled', () => {
      const input = 'tomorrow, no, next week';
      const output = processor.process(input, true, false);
      // Should still be original but with term mapping applied
      expect(output).toContain('tomorrow');
    });

    it('should skip all processing when both disabled', () => {
      const input = 'view cell, no, next week';
      const output = processor.process(input, false, false);
      expect(output).toBe('view cell, no, next week');
    });
  });
});
