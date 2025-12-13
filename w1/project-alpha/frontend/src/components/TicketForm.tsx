import { useState, useEffect, useMemo } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ticketsApi, tagsApi } from '@/lib/api'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { TagMultiSelect } from '@/components/TagMultiSelect'
import { useToast } from '@/components/ui/use-toast'
import { ErrorType } from '@/lib/api'
import type { Ticket, TicketCreate, TicketUpdate } from '@/types'

interface TicketFormProps {
  ticket?: Ticket
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function TicketForm({ ticket, open, onOpenChange }: TicketFormProps) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [selectedTags, setSelectedTags] = useState<string[]>([]) // 存储标签 ID
  const [errors, setErrors] = useState<{ title?: string; description?: string }>({})
  const [touched, setTouched] = useState<{ title?: boolean; description?: boolean }>({})
  const { toast } = useToast()
  const queryClient = useQueryClient()

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

  useEffect(() => {
    if (ticket) {
      setTitle(ticket.title)
      setDescription(ticket.description || '')
      setSelectedTags(ticket.tags.map((tag) => tag.id))
    } else {
      setTitle('')
      setDescription('')
      setSelectedTags([])
    }
    setErrors({})
    setTouched({})
  }, [ticket, open])

  // 实时校验
  const validateTitle = (value: string): string | undefined => {
    if (!value.trim()) {
      return '标题不能为空'
    }
    if (value.length > 200) {
      return '标题长度不能超过 200 个字符'
    }
    return undefined
  }

  const validateDescription = (value: string): string | undefined => {
    if (value.length > 2000) {
      return '描述长度不能超过 2000 个字符'
    }
    return undefined
  }

  const createMutation = useMutation({
    mutationFn: (data: TicketCreate) => ticketsApi.create(data),
    onSuccess: () => {
      // 使所有 tickets 查询失效，确保列表刷新
      queryClient.invalidateQueries({ queryKey: ['tickets'] })
      // 同时刷新标签列表（以防创建了新标签）
      queryClient.invalidateQueries({ queryKey: ['tags'] })
      toast({
        title: '创建成功',
        description: 'Ticket 已创建',
      })
      onOpenChange(false)
    },
    onError: (error: Error & { type?: ErrorType }) => {
      const isValidationError = error.type === ErrorType.VALIDATION
      toast({
        title: isValidationError ? '验证失败' : '创建失败',
        description: error.message,
        variant: 'destructive',
      })
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: TicketUpdate) =>
      ticketsApi.update(ticket!.id, data),
    onSuccess: () => {
      // 使所有 tickets 查询失效，确保列表刷新
      queryClient.invalidateQueries({ queryKey: ['tickets'] })
      // 同时刷新标签列表（以防创建了新标签）
      queryClient.invalidateQueries({ queryKey: ['tags'] })
      toast({
        title: '更新成功',
        description: 'Ticket 已更新',
      })
      onOpenChange(false)
    },
    onError: (error: Error & { type?: ErrorType }) => {
      const isValidationError = error.type === ErrorType.VALIDATION
      toast({
        title: isValidationError ? '验证失败' : '更新失败',
        description: error.message,
        variant: 'destructive',
      })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    // 标记所有字段为已触摸
    setTouched({ title: true, description: true })

    // 验证
    const newErrors: { title?: string; description?: string } = {}
    const titleError = validateTitle(title)
    const descriptionError = validateDescription(description)

    if (titleError) {
      newErrors.title = titleError
    }
    if (descriptionError) {
      newErrors.description = descriptionError
    }

    setErrors(newErrors)

    if (Object.keys(newErrors).length > 0) {
      return
    }

    const data = {
      title: title.trim(),
      description: description.trim() || null,
      tags: selectedTagNames,
    }

    if (ticket) {
      updateMutation.mutate(data)
    } else {
      createMutation.mutate(data)
    }
  }

  const isLoading = createMutation.isPending || updateMutation.isPending

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle>{ticket ? '编辑 Ticket' : '创建 Ticket'}</DialogTitle>
          <DialogDescription>
            {ticket
              ? '更新 ticket 的信息'
              : '创建一个新的 ticket 来跟踪任务'}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col min-h-0 flex-1 overflow-hidden">
          <div className="space-y-4 py-4 overflow-y-auto flex-1 min-h-0 pr-1">
            <div className="space-y-2">
              <Label htmlFor="title">
                标题 <span className="text-destructive">*</span>
              </Label>
              <Input
                id="title"
                value={title}
                onChange={(e) => {
                  setTitle(e.target.value)
                  if (touched.title && errors.title) {
                    const error = validateTitle(e.target.value)
                    setErrors({ ...errors, title: error })
                  }
                }}
                onBlur={() => {
                  setTouched({ ...touched, title: true })
                  const error = validateTitle(title)
                  setErrors({ ...errors, title: error })
                }}
                placeholder="输入 ticket 标题"
                maxLength={200}
                className={touched.title && errors.title ? 'border-destructive' : ''}
              />
              {touched.title && errors.title && (
                <p className="text-sm text-destructive">{errors.title}</p>
              )}
              <p className="text-xs text-muted-foreground">
                {title.length}/200
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">描述</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => {
                  setDescription(e.target.value)
                  if (touched.description && errors.description) {
                    const error = validateDescription(e.target.value)
                    setErrors({ ...errors, description: error })
                  }
                }}
                onBlur={() => {
                  setTouched({ ...touched, description: true })
                  const error = validateDescription(description)
                  setErrors({ ...errors, description: error })
                }}
                placeholder="输入 ticket 描述（可选）"
                rows={4}
                maxLength={2000}
                className={touched.description && errors.description ? 'border-destructive' : ''}
              />
              {touched.description && errors.description && (
                <p className="text-sm text-destructive">{errors.description}</p>
              )}
              <p className="text-xs text-muted-foreground">
                {description.length}/2000
              </p>
            </div>

            <div className="space-y-2">
              <Label>标签</Label>
              <TagMultiSelect
                selectedTags={selectedTags}
                onTagsChange={setSelectedTags}
                className="w-full"
              />
            </div>
          </div>
          <DialogFooter className="flex-shrink-0 pt-4 border-t border-gray-200/60">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isLoading}
            >
              取消
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? '保存中...' : ticket ? '更新' : '创建'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
