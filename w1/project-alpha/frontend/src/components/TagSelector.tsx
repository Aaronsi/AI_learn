import { useState, useRef, useEffect, useMemo } from 'react'
import { createPortal } from 'react-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { X, ChevronDown, Plus } from 'lucide-react'
import { tagsApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useToast } from '@/components/ui/use-toast'
import { ErrorType } from '@/lib/api'
import { cn } from '@/lib/utils'
import type { Tag } from '@/types'

interface TagSelectorProps {
  selectedTags: string[]
  onTagsChange: (tags: string[]) => void
  className?: string
}

export function TagSelector({
  selectedTags,
  onTagsChange,
  className,
}: TagSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [searchValue, setSearchValue] = useState('')
  const [inputFocused, setInputFocused] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const dropdownContentRef = useRef<HTMLDivElement>(null)
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const { data: tags = [] } = useQuery({
    queryKey: ['tags'],
    queryFn: () => tagsApi.list(),
  })

  // 过滤标签：根据搜索值过滤，排除已选中的标签
  const filteredTags = useMemo(() => {
    const searchLower = searchValue.toLowerCase().trim()
    return tags.filter((tag) => {
      const matchesSearch = !searchLower || tag.name.toLowerCase().includes(searchLower)
      const notSelected = !selectedTags.includes(tag.id)
      return matchesSearch && notSelected
    })
  }, [tags, searchValue, selectedTags])

  // 检查是否可以创建新标签
  const canCreateTag = useMemo(() => {
    const trimmed = searchValue.trim()
    if (!trimmed || trimmed.length > 50) return false
    // 检查是否已存在同名标签
    const exists = tags.some((tag) => tag.name.toLowerCase() === trimmed.toLowerCase())
    // 检查是否已选中
    const selected = selectedTags.some((id) => {
      const tag = tags.find((t) => t.id === id)
      return tag?.name.toLowerCase() === trimmed.toLowerCase()
    })
    return !exists && !selected
  }, [searchValue, tags, selectedTags])

  // 获取已选中的标签对象
  const selectedTagObjects = useMemo(() => {
    return selectedTags
      .map((id) => tags.find((tag) => tag.id === id))
      .filter((tag): tag is Tag => tag !== undefined)
  }, [selectedTags, tags])

  // 计算下拉框位置
  const [dropdownPosition, setDropdownPosition] = useState<{ top: number; left: number; width: number } | null>(null)

  useEffect(() => {
    if (isOpen && containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect()
      setDropdownPosition({
        top: rect.bottom + window.scrollY + 8,
        left: rect.left + window.scrollX,
        width: rect.width,
      })
    } else {
      setDropdownPosition(null)
    }
  }, [isOpen, selectedTagObjects.length])

  // 点击外部关闭下拉框
  useEffect(() => {
    if (!isOpen) return

    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node

      // 检查点击是否在下拉框内
      if (dropdownContentRef.current?.contains(target)) {
        return // 点击在下拉框内，不关闭
      }

      // 检查点击是否在输入框容器内
      if (containerRef.current?.contains(target)) {
        return // 点击在输入框容器内，不关闭
      }

      // 点击在外部，关闭下拉框
      setIsOpen(false)
      setSearchValue('')
      setInputFocused(false)
    }

    // 使用捕获阶段监听，确保先于其他事件处理
    // 延迟添加，确保当前点击事件先处理
    const timeoutId = setTimeout(() => {
      document.addEventListener('mousedown', handleClickOutside, true)
    }, 0)

    return () => {
      clearTimeout(timeoutId)
      document.removeEventListener('mousedown', handleClickOutside, true)
    }
  }, [isOpen])

  // 当输入框获得焦点时打开下拉框
  useEffect(() => {
    if (inputFocused) {
      setIsOpen(true)
    }
  }, [inputFocused])

  const createTagMutation = useMutation({
    mutationFn: (name: string) => tagsApi.create({ name }),
    onSuccess: (newTag) => {
      queryClient.invalidateQueries({ queryKey: ['tags'] })
      if (!selectedTags.includes(newTag.id)) {
        onTagsChange([...selectedTags, newTag.id])
      }
      setSearchValue('')
      toast({
        title: '标签已创建',
        description: `标签 "${newTag.name}" 已添加`,
      })
    },
    onError: (error: Error & { type?: ErrorType }) => {
      const isValidationError = error.type === ErrorType.VALIDATION
      toast({
        title: isValidationError ? '验证失败' : '创建标签失败',
        description: error.message,
        variant: 'destructive',
      })
    },
  })

  const handleTagToggle = (tagId: string) => {
    if (selectedTags.includes(tagId)) {
      onTagsChange(selectedTags.filter((id) => id !== tagId))
    } else {
      onTagsChange([...selectedTags, tagId])
      setSearchValue('') // 选中后清空搜索
    }
    // 选中后不关闭下拉框，允许继续选择
    // setIsOpen(false)
  }

  const handleCreateTag = () => {
    const trimmedName = searchValue.trim()
    if (!trimmedName || !canCreateTag) return

    createTagMutation.mutate(trimmedName)
  }

  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      // 如果有可创建的标签，创建它；否则选择第一个过滤后的标签
      if (canCreateTag) {
        handleCreateTag()
      } else if (filteredTags.length > 0) {
        handleTagToggle(filteredTags[0].id)
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false)
      setSearchValue('')
      inputRef.current?.blur()
    } else if (e.key === 'Backspace' && searchValue === '' && selectedTags.length > 0) {
      // 当输入框为空且按下退格键时，删除最后一个选中的标签
      const lastTagId = selectedTags[selectedTags.length - 1]
      handleTagToggle(lastTagId)
    }
  }

  const handleRemoveTag = (tagId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    handleTagToggle(tagId)
  }

  return (
    <div className={cn('relative w-full', className)} ref={containerRef}>
      {/* 输入框容器 */}
      <div
        className={cn(
          'flex h-10 w-full min-h-10 items-center gap-1.5 rounded-xl border bg-white px-3 py-2 text-sm shadow-sm ring-offset-background transition-all duration-200',
          'focus-within:ring-2 focus-within:ring-primary/20 focus-within:border-primary',
          inputFocused ? 'border-primary' : 'border-gray-300 hover:border-gray-400',
          isOpen && 'border-primary'
        )}
        onClick={() => {
          inputRef.current?.focus()
          setInputFocused(true)
        }}
      >
        {/* 已选中的标签 */}
        <div className="flex flex-1 flex-wrap items-center gap-1.5">
          {selectedTagObjects.map((tag) => (
            <span
              key={tag.id}
              className="inline-flex items-center gap-1 rounded-md bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700 border border-blue-100/50"
            >
              {tag.name}
              <button
                type="button"
                onClick={(e) => handleRemoveTag(tag.id, e)}
                className="ml-0.5 hover:opacity-70 transition-opacity text-blue-600 focus:outline-none"
                tabIndex={-1}
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          ))}
          {/* 输入框 */}
          <input
            ref={inputRef}
            type="text"
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            onFocus={() => {
              setInputFocused(true)
              setIsOpen(true)
            }}
            onBlur={(e) => {
              // 检查下一个焦点目标是否是下拉框内的元素
              const relatedTarget = e.relatedTarget as Node | null

              // 如果焦点转移到下拉框内，不关闭
              if (dropdownContentRef.current?.contains(relatedTarget)) {
                return
              }

              // 延迟关闭，确保点击事件先处理
              setTimeout(() => {
                // 再次检查焦点是否在下拉框内
                const activeElement = document.activeElement
                if (
                  !dropdownContentRef.current?.contains(activeElement) &&
                  !containerRef.current?.contains(activeElement)
                ) {
                  setIsOpen(false)
                  setInputFocused(false)
                }
              }, 200)
            }}
            onKeyDown={handleInputKeyDown}
            placeholder={selectedTagObjects.length === 0 ? '选择标签...' : ''}
            className="flex-1 min-w-[120px] bg-transparent outline-none placeholder:text-gray-400 text-sm"
          />
        </div>
        {/* 下拉箭头 */}
        <ChevronDown
          className={cn(
            'h-4 w-4 text-gray-400 transition-transform duration-200 flex-shrink-0',
            isOpen && 'rotate-180'
          )}
        />
      </div>

      {/* 下拉列表 */}
      {isOpen && dropdownPosition && createPortal(
        <div
          ref={dropdownContentRef}
          data-tag-selector-dropdown
          className="fixed z-[10000] rounded-xl border border-gray-200 bg-white/95 backdrop-blur-xl text-popover-foreground macos-shadow-lg"
          style={{
            top: `${dropdownPosition.top}px`,
            left: `${dropdownPosition.left}px`,
            width: `${dropdownPosition.width}px`,
          }}
          onMouseDown={(e) => {
            // 阻止下拉框内的点击事件冒泡，避免触发外部点击关闭和 Dialog 的事件处理
            e.stopPropagation()
          }}
          onClick={(e) => {
            // 阻止点击事件冒泡
            e.stopPropagation()
          }}
          onPointerDown={(e) => {
            // 也阻止 pointer 事件，确保兼容性
            e.stopPropagation()
          }}
        >
          <div className="max-h-96 overflow-auto p-2">
            {/* 标签选项列表 */}
            {filteredTags.length > 0 && (
              <div className="space-y-1">
                {filteredTags.map((tag) => (
                  <button
                    key={tag.id}
                    type="button"
                    onMouseDown={(e) => {
                      // 阻止 blur 事件触发和事件冒泡
                      e.preventDefault()
                      e.stopPropagation()
                      // 在 mousedown 时立即执行选择，确保在 blur 之前完成
                      handleTagToggle(tag.id)
                    }}
                    onClick={(e) => {
                      // 处理点击事件，防止默认行为和冒泡
                      e.preventDefault()
                      e.stopPropagation()
                    }}
                    className="flex w-full cursor-pointer items-center rounded-lg px-3 py-2 text-sm outline-none hover:bg-gray-100 transition-colors duration-150 focus:bg-gray-100 text-left"
                  >
                    {tag.name}
                  </button>
                ))}
              </div>
            )}

            {/* 创建新标签选项 */}
            {canCreateTag && (
              <div className="border-t mt-2 pt-2">
                <button
                  type="button"
                  onMouseDown={(e) => {
                    // 阻止 blur 事件触发和事件冒泡
                    e.preventDefault()
                    e.stopPropagation()
                    // 在 mousedown 时立即执行创建，确保在 blur 之前完成
                    handleCreateTag()
                  }}
                  onClick={(e) => {
                    // 处理点击事件，防止默认行为和冒泡
                    e.preventDefault()
                    e.stopPropagation()
                  }}
                  disabled={createTagMutation.isPending}
                  className="flex w-full cursor-pointer items-center gap-2 rounded-lg px-3 py-2 text-sm outline-none hover:bg-gray-100 transition-colors duration-150 focus:bg-gray-100 text-left disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Plus className="h-4 w-4 text-gray-500" />
                  <span>创建标签 "{searchValue.trim()}"</span>
                </button>
              </div>
            )}

            {/* 空状态 */}
            {filteredTags.length === 0 && !canCreateTag && searchValue.trim() && (
              <div className="px-3 py-6 text-center text-sm text-gray-500">
                没有找到匹配的标签
              </div>
            )}

            {/* 无标签状态 */}
            {filteredTags.length === 0 && !canCreateTag && !searchValue.trim() && tags.length === 0 && (
              <div className="px-3 py-6 text-center text-sm text-gray-500">
                暂无标签，输入标签名创建
              </div>
            )}
          </div>
        </div>,
        document.body
      )}
    </div>
  )
}
