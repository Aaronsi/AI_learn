import { SlidePreview } from '@/components/preview/SlidePreview';
import { Thumbnails } from '@/components/preview/Thumbnails';
import { GenerateButton } from '@/components/preview/GenerateButton';

export function MainContent() {
  return (
    <main
      style={{ 
        flex: '1 1 0%', 
        minWidth: 0, 
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: 'var(--md-cream)',
        overflow: 'hidden'
      }}
    >
      {/* Preview Area */}
      <div
        style={{ 
          flex: '1 1 0%', 
          minHeight: 0, 
          overflow: 'hidden',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '16px'
        }}
      >
        <SlidePreview />
      </div>

      {/* Generate Button */}
      <div style={{ padding: '0 16px 12px 16px', flexShrink: 0 }}>
        <GenerateButton />
      </div>

      {/* Thumbnails */}
      <div 
        style={{ 
          borderTop: '2px solid var(--md-graphite)', 
          backgroundColor: 'var(--md-fog)', 
          padding: '12px',
          flexShrink: 0 
        }}
      >
        <Thumbnails />
      </div>
    </main>
  );
}
