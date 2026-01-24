import type { Turn } from '../types/turn'

/**
 * 解析 JSONL 文件内容
 * @param content 文件文本内容
 * @returns Turn 数组
 */
export function parseJSONL(content: string): Turn[] {
  const lines = content.trim().split('\n').filter(line => line.trim())
  const turns: Turn[] = []
  
  for (const line of lines) {
    try {
      const turn = JSON.parse(line) as Turn
      turns.push(turn)
    } catch (error) {
      console.error('Failed to parse line:', line, error)
    }
  }
  
  return turns
}

/**
 * 读取文件内容
 */
export async function readFile(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      if (e.target?.result) {
        resolve(e.target.result as string)
      } else {
        reject(new Error('Failed to read file'))
      }
    }
    reader.onerror = reject
    reader.readAsText(file)
  })
}

