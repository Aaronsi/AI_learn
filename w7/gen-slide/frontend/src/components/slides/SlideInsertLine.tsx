import { useState, useRef, useEffect } from 'react';

interface SlideInsertLineProps {
  isActive: boolean;
  onClick: () => void;
  onConfirm: (content: string) => void;
  onCancel: () => void;
}

export function SlideInsertLine({
  isActive,
  onClick,
  onConfirm,
  onCancel,
}: SlideInsertLineProps) {
  const [content, setContent] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isActive && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isActive]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && content.trim()) {
      onConfirm(content);
      setContent('');
    } else if (e.key === 'Escape') {
      setContent('');
      onCancel();
    }
  };

  const handleBlur = () => {
    if (!content.trim()) {
      onCancel();
    }
  };

  if (isActive) {
    return (
      <div className="py-2">
        <input
          ref={inputRef}
          type="text"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={handleBlur}
          placeholder="Enter slide content and press Enter..."
          className="w-full px-3 py-2 border-2 border-[var(--md-sky)] rounded bg-[var(--md-cloud)] text-[var(--md-ink)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--md-sky)]"
        />
        <p className="text-xs text-[var(--md-slate)] mt-1">
          Press Enter to add, Esc to cancel
        </p>
      </div>
    );
  }

  return (
    <button
      onClick={onClick}
      className="w-full py-1 group hover:bg-[var(--md-soft-blue)] rounded transition-colors"
    >
      <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <div className="flex-1 h-0.5 bg-[var(--md-sky)]" />
        <svg
          className="w-4 h-4 text-[var(--md-sky)]"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path
            fillRule="evenodd"
            d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
            clipRule="evenodd"
          />
        </svg>
        <div className="flex-1 h-0.5 bg-[var(--md-sky)]" />
      </div>
    </button>
  );
}
