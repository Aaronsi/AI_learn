/**
 * Audio Visualizer Component
 *
 * Phase 2: Real-time audio level visualization
 */

import React, { useEffect, useRef } from 'react';

interface AudioVisualizerProps {
  level: number; // 0.0 - 1.0
  isActive: boolean;
}

export const AudioVisualizer: React.FC<AudioVisualizerProps> = ({
  level,
  isActive,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();
  const historyRef = useRef<number[]>([]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const draw = () => {
      const width = canvas.width;
      const height = canvas.height;

      // Clear canvas
      ctx.clearRect(0, 0, width, height);

      if (!isActive) {
        // Draw inactive state
        ctx.fillStyle = '#e5e7eb';
        ctx.fillRect(0, height / 2 - 1, width, 2);
        return;
      }

      // Add current level to history
      historyRef.current.push(level);
      if (historyRef.current.length > 50) {
        historyRef.current.shift();
      }

      // Draw waveform
      const barWidth = width / historyRef.current.length;

      historyRef.current.forEach((value, index) => {
        const barHeight = value * height * 0.8;
        const x = index * barWidth;
        const y = (height - barHeight) / 2;

        // Gradient color based on level
        const hue = 120 - value * 60; // Green to yellow to red
        ctx.fillStyle = `hsl(${hue}, 70%, 50%)`;
        ctx.fillRect(x, y, barWidth - 1, barHeight);
      });

      animationRef.current = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [level, isActive]);

  return (
    <canvas
      ref={canvasRef}
      width={300}
      height={60}
      className="w-full h-full"
      style={{ imageRendering: 'pixelated' }}
    />
  );
};
