import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ChevronLeft, ChevronRight } from 'lucide-react'

interface PaginationProps {
  total: number
  limit: number
  offset: number
  onPageChange: (newOffset: number) => void
  onLimitChange?: (newLimit: number) => void
}

export function Pagination({
  total,
  limit,
  offset,
  onPageChange,
  onLimitChange,
}: PaginationProps) {
  const currentPage = Math.floor(offset / limit) + 1
  const totalPages = Math.ceil(total / limit)
  const [pageInput, setPageInput] = useState(currentPage.toString())

  const handlePrevious = () => {
    if (offset > 0) {
      onPageChange(Math.max(0, offset - limit))
    }
  }

  const handleNext = () => {
    if (offset + limit < total) {
      onPageChange(offset + limit)
    }
  }

  const handlePageInputChange = (value: string) => {
    setPageInput(value)
  }

  const handlePageInputBlur = () => {
    const pageNum = parseInt(pageInput, 10)
    if (!isNaN(pageNum) && pageNum >= 1 && pageNum <= totalPages) {
      onPageChange((pageNum - 1) * limit)
    } else {
      setPageInput(currentPage.toString())
    }
  }

  const handlePageInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handlePageInputBlur()
    }
  }

  const handleLimitChange = (newLimit: string) => {
    const limitNum = parseInt(newLimit, 10)
    if (onLimitChange && !isNaN(limitNum)) {
      onLimitChange(limitNum)
      // 调整 offset 以保持在当前页
      const newPage = Math.floor(offset / limitNum) + 1
      const maxPage = Math.ceil(total / limitNum)
      const targetPage = Math.min(newPage, maxPage)
      onPageChange((targetPage - 1) * limitNum)
    }
  }

  // 同步 pageInput 与 currentPage
  useEffect(() => {
    setPageInput(currentPage.toString())
  }, [currentPage])

  if (totalPages <= 1 && !onLimitChange) {
    return null
  }

  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between rounded-xl bg-white/60 backdrop-blur-sm p-4 border border-gray-200/60">
      <div className="flex items-center gap-4">
        <div className="text-sm text-gray-600 font-medium">
          显示 {offset + 1} - {Math.min(offset + limit, total)} / 共 {total} 条
        </div>
        {onLimitChange && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600 font-medium">每页</span>
            <Select value={limit.toString()} onValueChange={handleLimitChange}>
              <SelectTrigger className="w-20">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="10">10</SelectItem>
                <SelectItem value="20">20</SelectItem>
                <SelectItem value="50">50</SelectItem>
                <SelectItem value="100">100</SelectItem>
              </SelectContent>
            </Select>
            <span className="text-sm text-gray-600 font-medium">条</span>
          </div>
        )}
      </div>
      {totalPages > 1 && (
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handlePrevious}
            disabled={offset === 0}
          >
            <ChevronLeft className="h-4 w-4" />
            上一页
          </Button>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600 font-medium">第</span>
            <Input
              type="number"
              min={1}
              max={totalPages}
              value={pageInput}
              onChange={(e) => handlePageInputChange(e.target.value)}
              onBlur={handlePageInputBlur}
              onKeyDown={handlePageInputKeyDown}
              className="w-16 text-center"
            />
            <span className="text-sm text-gray-600 font-medium">/ {totalPages} 页</span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleNext}
            disabled={offset + limit >= total}
          >
            下一页
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  )
}
