import { useMemo, useState } from 'react'
import { Landing } from './components/Landing'
import { Workspace } from './components/Workspace'
import { loadSolved } from './lib/progress'

type View = 'landing' | 'practice'

export default function App() {
  const [view, setView] = useState<View>('landing')
  const [solved, setSolved] = useState(() => loadSolved())
  const solvedCount = useMemo(() => solved.size, [solved])

  if (view === 'landing') {
    return (
      <div className="app-shell">
        <Landing
          solvedCount={solvedCount}
          onEnter={() => setView('practice')}
        />
      </div>
    )
  }

  return (
    <div className="app-shell">
      <Workspace
        solved={solved}
        onSolved={setSolved}
        onBack={() => setView('landing')}
      />
    </div>
  )
}
