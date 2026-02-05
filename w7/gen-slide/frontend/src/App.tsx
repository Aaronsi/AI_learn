import { useState, useEffect, useRef } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useParams } from 'react-router-dom';
import { useSlides } from '@/hooks/useSlides';
import { useSlideStore } from '@/stores/slideStore';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import { MainContent } from '@/components/layout/MainContent';
import { Carousel } from '@/components/carousel/Carousel';
import { StyleSelector } from '@/components/style/StyleSelector';
import { Toast } from '@/components/common/Toast';
import { Loading } from '@/components/common/Loading';

function ProjectPage() {
  const { slug } = useParams<{ slug: string }>();
  const { project, isLoading, error } = useSlides(slug!);
  const { createProject, loadProject } = useSlideStore();
  const [isCreating, setIsCreating] = useState(false);
  const hasAutoCreated = useRef(false);

  // Auto-create project if not found (first-time flow)
  useEffect(() => {
    if (error === 'PROJECT_NOT_FOUND' && slug && !isCreating && !hasAutoCreated.current) {
      hasAutoCreated.current = true;
      setIsCreating(true);

      // Create project with slug as default title
      createProject(slug, slug)
        .then(() => {
          // Project created successfully, reload to get full data
          return loadProject(slug);
        })
        .then(() => {
          // Style selector will auto-open via StyleSelector component
          // No need to manually open here
        })
        .catch((err: any) => {
          console.error('Failed to auto-create project:', err);
          const status = err?.status || err?.response?.status;
          
          // If 409 (already exists), try to load it
          if (status === 409) {
            return loadProject(slug).catch((loadErr) => {
              console.error('Failed to load existing project:', loadErr);
              hasAutoCreated.current = false;
              throw loadErr;
            });
          }
          
          // Reset flag on other errors so user can retry
          hasAutoCreated.current = false;
          throw err;
        })
        .finally(() => {
          setIsCreating(false);
        });
    }
  }, [error, slug, createProject, loadProject, isCreating]);

  if (isLoading || isCreating) {
    return <Loading fullScreen text={isCreating ? "Creating project..." : "Loading project..."} />;
  }

  // Show loading while auto-creating project
  if (error === 'PROJECT_NOT_FOUND') {
    return <Loading fullScreen text="Initializing project..." />;
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[var(--md-cream)]">
        <div className="text-center">
          <svg
            className="w-24 h-24 mx-auto text-[var(--md-watermelon)] mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <h1 className="text-2xl font-bold text-[var(--md-ink)] mb-2">Error Loading Project</h1>
          <p className="text-[var(--md-slate)]">{error}</p>
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[var(--md-cream)]">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-[var(--md-ink)] mb-2">Project Not Found</h1>
          <p className="text-[var(--md-slate)]">The requested project does not exist.</p>
        </div>
      </div>
    );
  }

  return (
    <div 
      className="bg-[var(--md-cream)]"
      style={{ 
        height: '100vh', 
        width: '100vw', 
        display: 'flex', 
        flexDirection: 'column',
        overflow: 'hidden',
        position: 'fixed',
        top: 0,
        left: 0
      }}
    >
      <Header />
      <div
        style={{ 
          display: 'flex', 
          flexDirection: 'row',
          flex: '1 1 0%', 
          minHeight: 0,
          overflow: 'hidden'
        }}
      >
        <Sidebar />
        <MainContent />
      </div>
      <Carousel />
      <StyleSelector />
      <Toast />
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/:slug" element={<ProjectPage />} />
        <Route path="/" element={<Navigate to="/demo" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
