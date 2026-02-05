import { useState, useEffect, useRef } from 'react';
import { useSlideStore } from '@/stores/slideStore';
import { useSlideStore as useSlideStoreDirect } from '@/stores/slideStore';
import { useUIStore, useUIStore as useUIStoreDirect } from '@/stores/uiStore';
import { Button } from '@/components/common/Button';
import { Loading } from '@/components/common/Loading';
import * as styleApi from '@/services/styleApi';
import { getStyleImageUrl, isBase64Image } from '@/services/imageApi';
import type { StyleCandidate } from '@/types/style';
import { createPortal } from 'react-dom';

export function StyleSelector() {
  const { project, setProject } = useSlideStore();
  const { isStyleSelectorOpen, closeStyleSelector, showToast } = useUIStore();
  const [prompt, setPrompt] = useState('');
  const [candidates, setCandidates] = useState<StyleCandidate[]>([]);
  const [selectedCandidate, setSelectedCandidate] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSelecting, setIsSelecting] = useState(false);
  const hasAutoOpened = useRef(false);

  // Determine if this is first-time setup (no style configured)
  const isFirstTimeSetup = !project?.style;

  // Auto-open if no style configured (first-time flow)
  useEffect(() => {
    if (project && !project.style && !isStyleSelectorOpen && !hasAutoOpened.current) {
      hasAutoOpened.current = true;
      const timer = setTimeout(() => {
        const currentProject = useSlideStoreDirect.getState().project;
        const currentIsOpen = useUIStoreDirect.getState().isStyleSelectorOpen;
        if (currentProject && !currentProject.style && !currentIsOpen) {
          useUIStoreDirect.getState().openStyleSelector();
        }
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [project, isStyleSelectorOpen]);

  // Reset auto-open flag when project slug changes
  useEffect(() => {
    if (project?.slug) {
      hasAutoOpened.current = false;
    }
  }, [project?.slug]);

  // Reset form when modal closes
  useEffect(() => {
    if (!isStyleSelectorOpen) {
      setPrompt('');
      setCandidates([]);
      setSelectedCandidate(null);
    }
  }, [isStyleSelectorOpen]);

  // Lock body scroll when modal is open
  useEffect(() => {
    if (isStyleSelectorOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isStyleSelectorOpen]);

  const handleClose = () => {
    if (project?.style) {
      closeStyleSelector();
      setPrompt('');
      setCandidates([]);
      setSelectedCandidate(null);
    } else {
      showToast('请先设置风格样式', 'error');
    }
  };

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isStyleSelectorOpen && !isFirstTimeSetup) {
        handleClose();
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isStyleSelectorOpen, isFirstTimeSetup]);

  const handleGenerate = async () => {
    if (!prompt.trim() || !project) return;

    setIsGenerating(true);
    setCandidates([]);
    setSelectedCandidate(null);

    try {
      const response = await styleApi.generateStyleCandidates(project.slug, {
        prompt: prompt.trim(),
      });
      setCandidates(response.candidates);
      showToast('风格候选图生成成功', 'success');
    } catch (error) {
      showToast('生成风格候选图失败，请重试', 'error');
    } finally {
      setIsGenerating(false);
    }
  };

  // Handle candidate image click - immediately select and save
  const handleCandidateClick = async (candidateImage: string) => {
    if (!project || !prompt.trim() || isSelecting) return;

    // Show selection effect immediately
    setSelectedCandidate(candidateImage);
    setIsSelecting(true);

    try {
      const updatedProject = await styleApi.selectStyle(project.slug, {
        prompt: prompt.trim(),
        image: candidateImage,
      });
      setProject(updatedProject);
      showToast('风格设置成功', 'success');
      closeStyleSelector();
      setPrompt('');
      setCandidates([]);
      setSelectedCandidate(null);
    } catch (error) {
      showToast('设置风格失败，请重试', 'error');
      setSelectedCandidate(null);
    } finally {
      setIsSelecting(false);
    }
  };

  // Don't render if no project or modal is closed
  if (!project || !isStyleSelectorOpen) {
    return null;
  }

  // Handle backdrop click - only close if not first-time setup
  const handleBackdropClick = () => {
    if (!isFirstTimeSetup) {
      handleClose();
    }
  };

  const modalContent = (
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center p-4"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px'
      }}
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)'
        }}
        onClick={handleBackdropClick}
      />

      {/* Modal Container */}
      <div
        className="relative bg-[var(--md-cloud)] border-2 border-[var(--md-graphite)] shadow-[0_8px_0_rgba(0,0,0,1)] rounded-lg w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col"
        style={{
          position: 'relative',
          zIndex: 10000,
          backgroundColor: 'var(--md-cloud, #ffffff)',
          maxWidth: '672px',
          width: '100%'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b-2 border-[var(--md-graphite)] flex-shrink-0">
          <h2 className="text-xl font-bold text-[var(--md-ink)]">
            {isFirstTimeSetup ? "设置幻灯片风格" : "修改风格样式"}
          </h2>
          {!isFirstTimeSetup && (
            <button
              onClick={handleClose}
              className="ml-auto p-2 hover:bg-[var(--md-fog)] rounded-md transition-colors"
              aria-label="Close modal"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          <div className="space-y-5">
            {/* First-time setup welcome message */}
            {isFirstTimeSetup && !candidates.length && !isGenerating && (
              <div className="p-4 bg-[var(--md-sunbeam)]/20 border-2 border-[var(--md-sunbeam)] rounded-lg">
                <h3 className="text-base font-bold text-[var(--md-ink)] mb-2">欢迎使用 GenSlides！</h3>
                <p className="text-sm text-[var(--md-ink)] leading-relaxed">
                  在开始之前，请先设置幻灯片的视觉风格。输入一段风格描述，系统将为您生成两张风格参考图供选择。
                </p>
              </div>
            )}

            {/* Current style display (only show when modifying) */}
            {project?.style && !candidates.length && !isGenerating && (
              <div className="p-4 bg-[var(--md-soft-blue)] border-2 border-[var(--md-sky)] rounded-lg">
                <h3 className="text-sm font-bold text-[var(--md-ink)] mb-3">当前风格</h3>
                <div className="flex gap-4 items-center">
                  <img
                    src={
                      isBase64Image(project.style.image)
                        ? (project.style.image.startsWith('data:') ? project.style.image : `data:image/png;base64,${project.style.image}`)
                        : getStyleImageUrl(project.slug)
                    }
                    alt="当前风格"
                    className="w-24 h-24 object-cover rounded border-2 border-[var(--md-graphite)] flex-shrink-0"
                  />
                  <p className="text-sm text-[var(--md-ink)] leading-relaxed">{project.style.prompt}</p>
                </div>
              </div>
            )}

            {/* Loading state - centered */}
            {isGenerating && (
              <div className="flex flex-col items-center justify-center py-12">
                <Loading size="lg" text="正在生成风格候选图，请稍候..." />
              </div>
            )}

            {/* Candidates display */}
            {candidates.length > 0 && !isGenerating && (
              <div className="space-y-4">
                <h3 className="text-base font-bold text-[var(--md-ink)] text-center">
                  点击选择一张作为风格基准
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  {candidates.map((candidate, index) => (
                    <button
                      key={index}
                      onClick={() => handleCandidateClick(candidate.image)}
                      disabled={isSelecting}
                      className={`relative group rounded-lg overflow-hidden border-2 transition-all ${
                        selectedCandidate === candidate.image
                          ? 'border-[var(--md-sky)] ring-4 ring-[var(--md-sky)]/30'
                          : 'border-[var(--md-graphite)] hover:border-[var(--md-sky)]'
                      } ${isSelecting ? 'cursor-wait' : 'cursor-pointer'}`}
                    >
                      <div className="aspect-square w-full relative">
                        <img
                          src={candidate.image}
                          alt={`风格候选图 ${index + 1}`}
                          className="w-full h-full object-cover"
                        />
                        {/* Selection overlay effect ON the image */}
                        {selectedCandidate === candidate.image && (
                          <div className="absolute inset-0 bg-[var(--md-sky)]/20 flex items-center justify-center">
                            <div className="w-16 h-16 bg-[var(--md-sky)] rounded-full flex items-center justify-center shadow-lg">
                              {isSelecting ? (
                                <svg className="w-8 h-8 text-white animate-spin" fill="none" viewBox="0 0 24 24">
                                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                              ) : (
                                <svg
                                  className="w-10 h-10 text-white"
                                  fill="currentColor"
                                  viewBox="0 0 20 20"
                                >
                                  <path
                                    fillRule="evenodd"
                                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                    clipRule="evenodd"
                                  />
                                </svg>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                      <div className="absolute bottom-0 left-0 right-0 p-2 bg-gradient-to-t from-black/70 to-transparent text-white text-sm font-medium text-center">
                        候选图 {index + 1}
                      </div>
                      {!selectedCandidate && (
                        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors" />
                      )}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Prompt input - only show when not showing candidates */}
            {!candidates.length && !isGenerating && (
              <>
                <div className="space-y-2">
                  <label className="block text-sm font-bold text-[var(--md-ink)]">
                    描述您想要的幻灯片风格
                  </label>
                  <textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="例如：科技感、蓝色调、扁平风格、简约现代"
                    className="w-full min-h-[80px] px-4 py-3 border-2 border-[var(--md-graphite)] rounded-lg bg-[var(--md-fog)] text-[var(--md-ink)] resize-none focus:outline-none focus:ring-2 focus:ring-[var(--md-sky)] leading-relaxed"
                  />
                  <p className="text-xs text-[var(--md-slate)] leading-relaxed">
                    提示：可以描述颜色、风格、氛围等，如"温暖的橙色调、手绘插画风格"
                  </p>
                </div>

                {/* Generate button */}
                <Button
                  variant="primary"
                  size="lg"
                  onClick={handleGenerate}
                  isLoading={isGenerating}
                  disabled={!prompt.trim() || isGenerating}
                  className="w-full"
                >
                  生成风格候选图
                </Button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
}
