import { useEffect, useMemo, useState } from 'react'
import { Landing } from './components/Landing'
import { Workspace } from './components/Workspace'
import { loadSolved } from './lib/progress'

type View = 'landing' | 'practice'
type Theme = 'paper' | 'forest'

const THEME_KEY = 'tree-practice:theme'

export default function App() {
  const [view, setView] = useState<View>('landing')
  const [initialTopic, setInitialTopic] = useState<string>('all')
  const [solved, setSolved] = useState(() => loadSolved())
  const [theme, setTheme] = useState<Theme>(() => {
    try {
      const saved = localStorage.getItem(THEME_KEY)
      return saved === 'forest' ? 'forest' : 'paper'
    } catch {
      return 'paper'
    }
  })

  const solvedCount = useMemo(() => solved.size, [solved])

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    try {
      localStorage.setItem(THEME_KEY, theme)
    } catch {
      // ignore storage errors
    }
  }, [theme])

  function enterWorkspace(topicId = 'all') {
    setInitialTopic(topicId)
    setView('practice')
  }

  function toggleTheme() {
    setTheme((prev) => (prev === 'paper' ? 'forest' : 'paper'))
  }

  if (view === 'landing') {
    return (
      <div className="app-shell">
        <Landing
          solved={solved}
          solvedCount={solvedCount}
          theme={theme}
          onToggleTheme={toggleTheme}
          onEnter={enterWorkspace}
        />
      </div>
    )
  }

  return (
    <div className="app-shell">
      <Workspace
        initialTopic={initialTopic}
        solved={solved}
        onSolved={setSolved}
        theme={theme}
        onToggleTheme={toggleTheme}
        onBack={() => setView('landing')}
      />
    </div>
  )
}
