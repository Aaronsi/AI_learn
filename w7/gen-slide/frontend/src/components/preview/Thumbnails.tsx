import { usePreviewStore } from '@/stores/previewStore';

export function Thumbnails() {
  const { images, currentImageHash, setCurrentImageHash } = usePreviewStore();

  if (images.length === 0) {
    return (
      <div className="text-center py-2">
        <p className="text-[var(--md-slate)] text-sm">No images generated yet</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <h3 className="text-xs font-bold text-[var(--md-slate)] uppercase tracking-wide">
        Image History ({images.length})
      </h3>
      <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-thin">
        {images.map((image) => {
          const isSelected = currentImageHash === image.hash;
          return (
            <button
              key={image.hash}
              onClick={() => setCurrentImageHash(image.hash)}
              className="relative flex-shrink-0 group flex flex-col"
              style={{ width: '120px' }}
            >
              <div className="relative">
                <img
                  src={image.url}
                  alt={`Generated image ${image.hash.slice(0, 8)}`}
                  className={`object-cover rounded border-2 transition-all ${
                    isSelected
                      ? 'border-[var(--md-sky)]'
                      : 'border-[var(--md-graphite)] hover:border-[var(--md-sky)]'
                  }`}
                  style={{ width: '120px', height: '68px' }}
                />
                {isSelected && (
                  <div className="absolute top-1 right-1 text-base">
                    ✅
                  </div>
                )}
                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors rounded" />
              </div>
              <div
                className="mt-1 text-xs text-[var(--md-slate)] text-left leading-tight"
                style={{
                  width: '120px',
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden',
                  wordBreak: 'break-word'
                }}
              >
                {image.content || `${image.hash.slice(0, 8)}...`}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
