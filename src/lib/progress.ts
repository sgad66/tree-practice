const KEY = 'tree-practice:solved'

export function loadSolved(): Set<string> {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return new Set()
    const arr = JSON.parse(raw) as unknown
    if (!Array.isArray(arr)) return new Set()
    return new Set(arr.filter((x): x is string => typeof x === 'string'))
  } catch {
    return new Set()
  }
}

export function markSolved(id: string): Set<string> {
  const set = loadSolved()
  set.add(id)
  localStorage.setItem(KEY, JSON.stringify([...set]))
  return set
}

export function clearProgress(): void {
  localStorage.removeItem(KEY)
}
