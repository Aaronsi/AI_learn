import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { X } from 'lucide-react'
import { tagsApi } from '@/lib/api'
import { cn } from '@/lib/utils'
import type { Tag } from '@/types'

interface TagMultiSelectProps {
  selectedTags: string[]
  onTagsChange: (tags: string[]) => void
  className?: string
}

export function TagMultiSelect({
  selectedTags,
  onTagsChange,
  className,
}: TagMultiSelectProps) {
  const { data: tags = [] } = useQuery({
    queryKey: ['tags'],
    queryFn: () => tagsApi.list(),
  })

  const handleTagToggle = (tagId: string) => {
    if (selectedTags.includes(tagId)) {
      onTagsChange(selectedTags.filter((id) => id !== tagId))
    } else {
      onTagsChange([...selectedTags, tagId])
    }
  }

  // 获取已选中的标签对象
  const selectedTagObjects = useMemo(() => {
    return selectedTags
      .map((id) => tags.find((tag) => tag.id === id))
      .filter((tag): tag is Tag => tag !== undefined)
  }, [selectedTags, tags])

  return (
    <div className={cn('space-y-3', className)}>
      {/* 已选中的标签 */}
      {selectedTagObjects.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-semibold text-gray-700">已选标签</p>
          <div className="flex flex-wrap gap-2">
            {selectedTagObjects.map((tag) => (
              <button
                key={tag.id}
                type="button"
                onClick={() => handleTagToggle(tag.id)}
                className="inline-flex items-center gap-1.5 rounded-lg bg-blue-50 px-3 py-1.5 text-sm font-medium text-blue-700 border border-blue-100/50 hover:bg-blue-100 hover:border-blue-200 transition-all duration-150 active:scale-[0.98]"
              >
                <span>{tag.name}</span>
                <X className="h-3.5 w-3.5 opacity-70 hover:opacity-100" />
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 所有标签列表 */}
      <div className="space-y-2">
        <p className="text-sm font-semibold text-gray-700">所有标签</p>
        {tags.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {tags.map((tag) => {
              const isSelected = selectedTags.includes(tag.id)
              return (
                <button
                  key={tag.id}
                  type="button"
                  onClick={() => handleTagToggle(tag.id)}
                  className={cn(
                    'inline-flex items-center rounded-lg px-3 py-1.5 text-sm font-medium transition-all duration-150 active:scale-[0.98]',
                    isSelected
                      ? 'bg-blue-50 text-blue-700 border border-blue-100/50 hover:bg-blue-100 hover:border-blue-200 shadow-sm'
                      : 'bg-gray-50 text-gray-700 border border-gray-200/60 hover:bg-gray-100 hover:border-gray-300 hover:shadow-sm'
                  )}
                >
                  {tag.name}
                  {isSelected && (
                    <span className="ml-1.5 text-blue-600 font-semibold">✓</span>
                  )}
                </button>
              )
            })}
          </div>
        ) : (
          <div className="py-6 text-center text-sm text-gray-500 rounded-lg bg-gray-50/50 border border-gray-200/60">
            暂无标签
          </div>
        )}
      </div>
    </div>
  )
}
