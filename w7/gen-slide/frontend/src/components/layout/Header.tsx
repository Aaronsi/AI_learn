import React, { useState } from 'react';
import { useSlideStore } from '@/stores/slideStore';
import { useUIStore } from '@/stores/uiStore';
import { Button } from '@/components/common/Button';

export function Header() {
  const { project, updateProjectTitle } = useSlideStore();
  const { openCarousel, openStyleSelector } = useUIStore();
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [titleValue, setTitleValue] = useState('');

  const handleTitleClick = () => {
    if (project) {
      setTitleValue(project.title);
      setIsEditingTitle(true);
    }
  };

  const handleTitleSave = async () => {
    if (titleValue.trim() && titleValue !== project?.title) {
      try {
        await updateProjectTitle(titleValue.trim());
      } catch (error) {
        console.error('Failed to update title:', error);
      }
    }
    setIsEditingTitle(false);
  };

  const handleTitleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleTitleSave();
    } else if (e.key === 'Escape') {
      setIsEditingTitle(false);
    }
  };

  return (
    <header
      style={{ 
        height: '56px', 
        minHeight: '56px', 
        flexShrink: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
        borderBottom: '2px solid var(--md-graphite)',
        backgroundColor: 'var(--md-cream)'
      }}
    >
      {/* Left: Logo + Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexShrink: 0 }}>
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
          <div 
            style={{ 
              width: '32px', 
              height: '32px', 
              backgroundColor: 'var(--md-sunbeam)', 
              border: '2px solid var(--md-graphite)', 
              borderRadius: '4px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 'bold',
              fontSize: '14px'
            }}
          >
            G
          </div>
          <span style={{ fontSize: '18px', fontWeight: 'bold', color: 'var(--md-ink)' }}>GenSlides</span>
        </div>

        {/* Project Title (editable) */}
        {project && (
          <div style={{ display: 'flex', alignItems: 'center' }}>
            {isEditingTitle ? (
              <input
                type="text"
                value={titleValue}
                onChange={(e) => setTitleValue(e.target.value)}
                onBlur={handleTitleSave}
                onKeyDown={handleTitleKeyDown}
                style={{
                  padding: '6px 16px',
                  border: '2px solid var(--md-graphite)',
                  borderRadius: '8px',
                  backgroundColor: 'var(--md-cloud)',
                  color: 'var(--md-ink)',
                  fontWeight: 500,
                  textAlign: 'center',
                  minWidth: '200px',
                  outline: 'none'
                }}
                autoFocus
              />
            ) : (
              <button
                onClick={handleTitleClick}
                style={{
                  padding: '6px 16px',
                  border: '2px solid var(--md-graphite)',
                  borderRadius: '8px',
                  backgroundColor: 'var(--md-cloud)',
                  color: 'var(--md-ink)',
                  fontWeight: 500,
                  minWidth: '200px',
                  textAlign: 'center',
                  cursor: 'pointer',
                  maxWidth: '400px',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap'
                }}
              >
                {project.title}
              </button>
            )}
          </div>
        )}
      </div>

      {/* Right: Actions - Style selector + Play button */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
        {project && (
          <Button 
            variant="secondary" 
            size="sm" 
            onClick={openStyleSelector}
          >
            {project.style ? '修改风格' : '设置风格'}
          </Button>
        )}
        {project && project.slides.length > 0 && (
          <Button variant="primary" size="sm" onClick={openCarousel}>
            <svg
              className="w-4 h-4 mr-1"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
                clipRule="evenodd"
              />
            </svg>
            播放
          </Button>
        )}
      </div>
    </header>
  );
}
