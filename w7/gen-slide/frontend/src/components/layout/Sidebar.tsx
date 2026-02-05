import { SlideList } from '@/components/slides/SlideList';

export function Sidebar() {
  return (
    <aside
      style={{
        width: '240px',
        minWidth: '240px',
        maxWidth: '240px',
        flexShrink: 0,
        display: 'flex',
        flexDirection: 'column',
        borderRight: '2px solid var(--md-graphite)',
        backgroundColor: 'var(--md-fog)',
        overflow: 'hidden'
      }}
    >
      <div 
        style={{ 
          padding: '12px', 
          flexShrink: 0, 
          borderBottom: '1px solid var(--md-graphite)' 
        }}
      >
        <h2 
          style={{ 
            fontSize: '12px', 
            fontWeight: 'bold', 
            color: 'var(--md-slate)', 
            textTransform: 'uppercase', 
            letterSpacing: '0.05em' 
          }}
        >
          Slides
        </h2>
      </div>
      <div
        style={{
          flex: '1 1 0%',
          overflowY: 'auto',
          overflowX: 'hidden',
          minHeight: 0,
          padding: '8px'
        }}
      >
        <SlideList />
      </div>
    </aside>
  );
}
