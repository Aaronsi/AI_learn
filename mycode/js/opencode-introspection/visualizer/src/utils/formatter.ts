/**
 * 格式化时间戳为可读日期时间
 */
export function formatTimestamp(timestamp: number): string {
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

/**
 * 格式化相对时间
 */
export function formatRelativeTime(timestamp: number): string {
  const now = Date.now()
  const diff = now - timestamp
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  
  if (days > 0) return `${days} 天前`
  if (hours > 0) return `${hours} 小时前`
  if (minutes > 0) return `${minutes} 分钟前`
  return `${seconds} 秒前`
}

/**
 * 截取文本预览
 */
export function truncateText(text: string, maxLength: number = 50): string {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

/**
 * 获取用户输入预览
 */
export function getInputPreview(turn: { input: { messages: Array<{ parts: Array<{ text?: string }> }> } }): string {
  for (const message of turn.input.messages) {
    for (const part of message.parts) {
      if (part.text) {
        return truncateText(part.text, 50)
      }
    }
  }
  return '(无输入)'
}

/**
 * 获取输出预览
 */
export function getOutputPreview(turn: { output: { textParts: Array<{ text: string }> } }): string {
  if (turn.output.textParts.length > 0) {
    return truncateText(turn.output.textParts[0].text, 50)
  }
  return '(无输出)'
}

