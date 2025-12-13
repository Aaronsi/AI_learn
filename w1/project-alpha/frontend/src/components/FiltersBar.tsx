import { useState, useEffect } from 'react'
import { Search } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { TagSelector } from '@/components/TagSelector'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useDebounce } from '@/hooks/use-debounce'
import { TicketStatus } from '@/types'
import { cn } from '@/lib/utils'

interface FiltersBarProps {
  status: TicketStatus | null
  onStatusChange: (status: TicketStatus | null) => void
  selectedTags: string[]
  onTagsChange: (tags: string[]) => void
  searchQuery: string
  onSearchChange: (query: string) => void
}

export function FiltersBar({
  status,
  onStatusChange,
  selectedTags,
  onTagsChange,
  searchQuery,
  onSearchChange,
}: FiltersBarProps) {
  const [localSearchQuery, setLocalSearchQuery] = useState(searchQuery)
  const debouncedSearchQuery = useDebounce(localSearchQuery, 300)

  useEffect(() => {
    onSearchChange(debouncedSearchQuery)
  }, [debouncedSearchQuery, onSearchChange])

  return (
    <div className="rounded-xl border border-gray-200/60 bg-white/80 backdrop-blur-sm macos-shadow-md p-6">
      <div className="grid gap-6 md:grid-cols-3">
        {/* 状态筛选 */}
        <div className="flex flex-col">
          <label className="text-sm font-semibold text-gray-700 mb-2.5">状态</label>
          <Select
            value={status || 'all'}
            onValueChange={(value) =>
              onStatusChange(value === 'all' ? null : (value as TicketStatus))
            }
          >
            <SelectTrigger className="w-full h-10">
              <SelectValue placeholder="全部状态" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部状态</SelectItem>
              <SelectItem value={TicketStatus.OPEN}>进行中</SelectItem>
              <SelectItem value={TicketStatus.DONE}>已完成</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* 标签筛选 */}
        <div className="flex flex-col">
          <label className="text-sm font-semibold text-gray-700 mb-2.5">标签</label>
          <TagSelector
            selectedTags={selectedTags}
            onTagsChange={onTagsChange}
            className="w-full"
          />
        </div>

        {/* 搜索 */}
        <div className="flex flex-col">
          <label className="text-sm font-semibold text-gray-700 mb-2.5">搜索</label>
          <div className="relative w-full">
            <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400 pointer-events-none" />
            <Input
              placeholder="搜索标题..."
              value={localSearchQuery}
              onChange={(e) => setLocalSearchQuery(e.target.value)}
              className="pl-10 w-full h-10"
            />
          </div>
        </div>
      </div>

      {/* 清除筛选 */}
      {(status !== null || selectedTags.length > 0 || searchQuery) && (
        <div className="flex justify-end mt-4 pt-4 border-t border-gray-200/60">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              onStatusChange(null)
              onTagsChange([])
              setLocalSearchQuery('')
              onSearchChange('')
            }}
            className="rounded-lg"
          >
            清除筛选
          </Button>
        </div>
      )}
    </div>
  )
}
