import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Trash2, CheckCircle2, Circle, Edit, ChevronDown, ChevronUp } from 'lucide-react'
import { ticketsApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { useToast } from '@/components/ui/use-toast'
import { ErrorType } from '@/lib/api'
import { formatDate, cn } from '@/lib/utils'
import { Ticket, TicketStatus } from '@/types'
import { TicketForm } from './TicketForm'

interface TicketListProps {
  tickets: Ticket[]
  onEdit?: (ticket: Ticket) => void
}

export function TicketList({ tickets, onEdit }: TicketListProps) {
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const [editingTicket, setEditingTicket] = useState<Ticket | null>(null)
  const [expandedDescriptions, setExpandedDescriptions] = useState<Set<string>>(new Set())

  const toggleStatusMutation = useMutation({
    mutationFn: async (ticket: Ticket) => {
      const newStatus =
        ticket.status === TicketStatus.OPEN
          ? TicketStatus.DONE
          : TicketStatus.OPEN
      return ticketsApi.update(ticket.id, { status: newStatus })
    },
    onMutate: async (ticket) => {
      await queryClient.cancelQueries({ queryKey: ['tickets'] })
      const previousTickets = queryClient.getQueryData(['tickets'])
      queryClient.setQueryData(['tickets'], (old: any) => {
        if (!old) return old
        return {
          ...old,
          items: old.items.map((t: Ticket) =>
            t.id === ticket.id
              ? {
                  ...t,
                  status:
                    t.status === TicketStatus.OPEN
                      ? TicketStatus.DONE
                      : TicketStatus.OPEN,
                }
              : t
          ),
        }
      })
      return { previousTickets }
    },
    onError: (error: Error & { type?: ErrorType }, ticket, context) => {
      queryClient.setQueryData(['tickets'], context?.previousTickets)
      const isNetworkError = error.type === ErrorType.NETWORK
      toast({
        title: isNetworkError ? '网络错误' : '操作失败',
        description: error.message,
        variant: 'destructive',
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tickets'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => ticketsApi.delete(id),
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: ['tickets'] })
      const previousTickets = queryClient.getQueryData(['tickets'])
      queryClient.setQueryData(['tickets'], (old: any) => {
        if (!old) return old
        return {
          ...old,
          items: old.items.filter((t: Ticket) => t.id !== id),
          total: Math.max(0, old.total - 1),
        }
      })
      return { previousTickets, deletedId: id }
    },
    onError: (error: Error & { type?: ErrorType }, id, context) => {
      // 恢复之前的数据
      if (context?.previousTickets) {
        queryClient.setQueryData(['tickets'], context.previousTickets)
      }
      const isNetworkError = error.type === ErrorType.NETWORK
      toast({
        title: isNetworkError ? '网络错误' : '删除失败',
        description: error.message,
        variant: 'destructive',
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tickets'] })
      toast({
        title: '删除成功',
        description: 'Ticket 已删除',
      })
    },
  })

  const handleToggleStatus = (ticket: Ticket) => {
    toggleStatusMutation.mutate(ticket)
  }

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id)
  }

  const toggleDescription = (ticketId: string) => {
    setExpandedDescriptions((prev) => {
      const next = new Set(prev)
      if (next.has(ticketId)) {
        next.delete(ticketId)
      } else {
        next.add(ticketId)
      }
      return next
    })
  }

  const isDescriptionLong = (description: string | null): boolean => {
    if (!description) return false
    return description.length > 150
  }

  if (tickets.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <div className="rounded-full bg-gray-100 p-6 mb-4">
          <Circle className="h-12 w-12 text-gray-400" />
        </div>
        <h3 className="text-lg font-semibold mb-2 text-gray-900">暂无 ticket</h3>
        <p className="text-sm text-gray-500">
          创建第一个 ticket 来开始跟踪任务
        </p>
      </div>
    )
  }

  return (
    <>
      <div className="space-y-3">
        {tickets.map((ticket) => (
          <div
            key={ticket.id}
            className="group rounded-xl border border-gray-200/60 bg-white/90 backdrop-blur-sm p-5 macos-shadow transition-all duration-200 hover:shadow-md hover:border-gray-300/60"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1 space-y-2">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleToggleStatus(ticket)}
                    className="mt-1 disabled:opacity-50 disabled:cursor-not-allowed"
                    title={
                      ticket.status === TicketStatus.OPEN
                        ? '标记为已完成'
                        : '标记为进行中'
                    }
                    disabled={toggleStatusMutation.isPending}
                  >
                    {ticket.status === TicketStatus.OPEN ? (
                      <Circle className="h-5 w-5 text-muted-foreground hover:text-primary" />
                    ) : (
                      <CheckCircle2 className="h-5 w-5 text-primary" />
                    )}
                  </button>
                  <h3
                    className={cn(
                      'text-lg font-semibold text-gray-900 tracking-tight',
                      ticket.status === TicketStatus.DONE &&
                        'line-through text-gray-400'
                    )}
                  >
                    {ticket.title}
                  </h3>
                </div>
                {ticket.description && (
                  <div className="space-y-1">
                    <p
                      className={cn(
                        'text-sm text-gray-600 leading-relaxed',
                        !expandedDescriptions.has(ticket.id) && isDescriptionLong(ticket.description)
                          ? 'line-clamp-2'
                          : ''
                      )}
                    >
                      {ticket.description}
                    </p>
                    {isDescriptionLong(ticket.description) && (
                      <button
                        onClick={() => toggleDescription(ticket.id)}
                        className="text-xs text-primary hover:underline flex items-center gap-1"
                      >
                        {expandedDescriptions.has(ticket.id) ? (
                          <>
                            <ChevronUp className="h-3 w-3" />
                            收起
                          </>
                        ) : (
                          <>
                            <ChevronDown className="h-3 w-3" />
                            展开
                          </>
                        )}
                      </button>
                    )}
                  </div>
                )}
                {ticket.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {ticket.tags.map((tag) => (
                      <span
                        key={tag.id}
                        className="rounded-lg bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700 border border-blue-100/50"
                      >
                        {tag.name}
                      </span>
                    ))}
                  </div>
                )}
                <div className="flex items-center gap-4 text-xs text-gray-500 font-medium">
                  <span>创建: {formatDate(ticket.created_at)}</span>
                  <span>更新: {formatDate(ticket.updated_at)}</span>
                </div>
              </div>
              <div className="ml-4 flex gap-2">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setEditingTicket(ticket)}
                  disabled={deleteMutation.isPending}
                >
                  <Edit className="h-4 w-4" />
                </Button>
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      disabled={deleteMutation.isPending}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>确认删除</AlertDialogTitle>
                      <AlertDialogDescription>
                        确定要删除这个 ticket 吗？此操作无法撤销。
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel disabled={deleteMutation.isPending}>
                        取消
                      </AlertDialogCancel>
                      <AlertDialogAction
                        onClick={() => handleDelete(ticket.id)}
                        disabled={deleteMutation.isPending}
                        className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                      >
                        {deleteMutation.isPending ? '删除中...' : '删除'}
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
            </div>
          </div>
        ))}
      </div>

      {editingTicket && (
        <TicketForm
          ticket={editingTicket}
          open={!!editingTicket}
          onOpenChange={(open) => !open && setEditingTicket(null)}
        />
      )}
    </>
  )
}
