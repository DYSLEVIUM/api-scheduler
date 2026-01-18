import { useEffect, useRef } from 'react'

export function useResizableTable() {
  const tableRef = useRef<HTMLTableElement>(null)

  useEffect(() => {
    const table = tableRef.current
    if (!table) return

    let isResizing = false
    let currentTh: HTMLTableCellElement | null = null
    let startX = 0
    let startWidth = 0

    const handleMouseMove = (e: MouseEvent) => {
      if (isResizing && currentTh) {
        const diff = e.clientX - startX
        const newWidth = Math.max(80, startWidth + diff)
        currentTh.style.width = `${newWidth}px`
        currentTh.style.minWidth = `${newWidth}px`

        const index = Array.from(currentTh.parentElement?.children || []).indexOf(currentTh)
        const rows = table.querySelectorAll('tbody tr')
        rows.forEach(row => {
          const cell = row.children[index] as HTMLTableCellElement
          if (cell) {
            cell.style.width = `${newWidth}px`
            cell.style.minWidth = `${newWidth}px`
          }
        })
        return
      }

      const target = e.target as HTMLElement
      const th = target.closest('th') as HTMLTableCellElement
      if (!th) {
        table.style.cursor = ''
        return
      }

      const rect = th.getBoundingClientRect()
      const isNearRightEdge = e.clientX > rect.right - 8

      if (isNearRightEdge) {
        table.style.cursor = 'col-resize'
      } else {
        table.style.cursor = ''
      }
    }

    const handleMouseDown = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      const th = target.closest('th') as HTMLTableCellElement
      if (!th) return

      const rect = th.getBoundingClientRect()
      const isNearRightEdge = e.clientX > rect.right - 8

      if (isNearRightEdge) {
        isResizing = true
        currentTh = th
        startX = e.clientX
        startWidth = th.offsetWidth
        document.body.style.cursor = 'col-resize'
        document.body.style.userSelect = 'none'
        e.preventDefault()
      }
    }

    const handleMouseUp = () => {
      isResizing = false
      currentTh = null
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
      table.style.cursor = ''
    }

    table.addEventListener('mousedown', handleMouseDown)
    table.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)

    return () => {
      table.removeEventListener('mousedown', handleMouseDown)
      table.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [])

  return tableRef
}
