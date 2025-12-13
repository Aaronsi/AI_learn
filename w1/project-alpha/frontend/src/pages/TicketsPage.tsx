import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { ticketsApi, tagsApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { FiltersBar } from '@/components/FiltersBar'
import { TicketList } from '@/components/TicketList'
import { TicketForm } from '@/components/TicketForm'
import { Pagination } from '@/components/Pagination'
import { ErrorType } from '@/lib/api'
import { TicketStatus } from '@/types'

const DEFAULT_LIMIT = 20

export function TicketsPage() {
  const [status, setStatus] = useState<TicketStatus | null>(null)
  const [selectedTags, setSelectedTags] = useState<string[]>([]) // 存储标签 ID
  const [searchQuery, setSearchQuery] = useState('')
  const [limit, setLimit] = useState(DEFAULT_LIMIT)
  const [offset, setOffset] = useState(0)
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)

  // 获取标签列表，用于将 ID 转换为名称
  const { data: tags = [] } = useQuery({
    queryKey: ['tags'],
    queryFn: () => tagsApi.list(),
  })

  // 将标签 ID 转换为标签名称
  const selectedTagNames = useMemo(() => {
    return selectedTags
      .map((tagId) => tags.find((tag) => tag.id === tagId)?.name)
      .filter((name): name is string => name !== undefined)
  }, [selectedTags, tags])

  const { data, isLoading, error } = useQuery({
    queryKey: ['tickets', { status, tags: selectedTagNames, q: searchQuery, limit, offset }],
    queryFn: () =>
      ticketsApi.list({
        status,
        tags: selectedTagNames.length > 0 ? selectedTagNames : undefined,
        q: searchQuery || undefined,
        limit,
        offset,
      }),
  })

  const handlePageChange = (newOffset: number) => {
    setOffset(newOffset)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleLimitChange = (newLimit: number) => {
    setLimit(newLimit)
    setOffset(0) // 重置到第一页
  }

  const handleFiltersChange = () => {
    setOffset(0) // 重置到第一页
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50/80">
      <div className="container mx-auto py-12 px-6 max-w-7xl">
        <div className="mb-8 flex items-center justify-between">
          <h1 className="text-4xl font-semibold tracking-tight text-gray-900">Tickets</h1>
          <Button
            onClick={() => setIsCreateDialogOpen(true)}
            className="rounded-xl px-6 py-2.5 font-medium shadow-sm hover:shadow-md transition-all duration-200"
          >
            <Plus className="mr-2 h-4 w-4" />
            创建 Ticket
          </Button>
        </div>

      <div className="mb-6">
        <FiltersBar
          status={status}
          onStatusChange={(newStatus) => {
            setStatus(newStatus)
            handleFiltersChange()
          }}
          selectedTags={selectedTags}
          onTagsChange={(tags) => {
            setSelectedTags(tags)
            handleFiltersChange()
          }}
          searchQuery={searchQuery}
          onSearchChange={(query) => {
            setSearchQuery(query)
            handleFiltersChange()
          }}
        />
      </div>

      {isLoading && (
        <div className="flex flex-col items-center justify-center py-24">
          <div className="mb-4 h-10 w-10 animate-spin rounded-full border-3 border-primary/30 border-t-primary"></div>
          <p className="text-muted-foreground text-sm font-medium">加载中...</p>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
          <p className="font-semibold text-destructive">
            {error instanceof Error && (error as Error & { type?: ErrorType }).type === ErrorType.NETWORK
              ? '网络连接失败'
              : '加载失败'}
          </p>
          <p className="mt-1 text-sm text-destructive/80">
            {error instanceof Error ? error.message : '未知错误'}
          </p>
          {error instanceof Error && (error as Error & { type?: ErrorType }).type === ErrorType.NETWORK && (
            <button
              onClick={() => window.location.reload()}
              className="mt-2 text-sm underline"
            >
              点击刷新页面
            </button>
          )}
        </div>
      )}

      {!isLoading && !error && data && (
        <>
          <TicketList tickets={data.items} />
          <div className="mt-6">
            <Pagination
              total={data.total}
              limit={limit}
              offset={offset}
              onPageChange={handlePageChange}
              onLimitChange={handleLimitChange}
            />
          </div>
        </>
      )}

      <TicketForm
        open={isCreateDialogOpen}
        onOpenChange={setIsCreateDialogOpen}
      />
      </div>
    </div>
  )
}
