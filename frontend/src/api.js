// Thin client for the Spend Analyzer API.

export async function analyzeFile(file) {
  const body = new FormData()
  body.append('file', file)
  const res = await fetch('/api/analyze', { method: 'POST', body })
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}))
    throw new Error(detail.detail || `Request failed (${res.status})`)
  }
  return res.json()
}

export async function loadSample() {
  const res = await fetch('/api/sample')
  if (!res.ok) throw new Error(`Request failed (${res.status})`)
  return res.json()
}

// Posts the file and triggers a browser download of the Excel/PDF report.
export async function downloadReport(file, fmt) {
  const body = new FormData()
  body.append('file', file)
  const res = await fetch(`/api/report?fmt=${fmt}`, { method: 'POST', body })
  if (!res.ok) throw new Error(`Report failed (${res.status})`)
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = fmt === 'excel' ? 'spend_report.xlsx' : 'spend_report.pdf'
  a.click()
  URL.revokeObjectURL(url)
}
