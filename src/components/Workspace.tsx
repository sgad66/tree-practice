import { useEffect, useMemo, useRef, useState } from 'react'
import { PROBLEMS, TOPICS, getProblem, topicCounts } from '../data/problems'
import type { Problem, RunResult } from '../types'
import { CodeEditor } from './CodeEditor'
import { TestResults } from './TestResults'
import {
  runProblem,
  preloadToolchain,
  ensureToolchain,
} from '../lib/clangJudge'
import { PAGES_BUILD } from '../lib/clangJudge'
import { markSolved } from '../lib/progress'

interface Props {
  initialId?: string
  solved: Set<string>
  onSolved: (ids: Set<string>) => void
  onBack: () => void
}

const draftKey = (id: string) => `tree-practice:draft:c-full:${id}`

function difficultyClass(d: Problem['difficulty']): string {
  if (d === '简单') return 'badge badge--easy'
  if (d === '中等') return 'badge badge--mid'
  return 'badge badge--hard'
}

/** Keep the short problem lede above examples; tuck long I/O notes. */
function splitStatement(text: string): { lede: string; ioNote: string } {
  const marker = '【编写说明】'
  const i = text.indexOf(marker)
  if (i < 0) return { lede: text, ioNote: '' }
  return {
    lede: text.slice(0, i).trim(),
    ioNote: text.slice(i).trim(),
  }
}

export function Workspace({ initialId, solved, onSolved, onBack }: Props) {
  const firstId = initialId ?? PROBLEMS[0]?.id ?? 'preorder'
  const [activeId, setActiveId] = useState(firstId)
  const problem = useMemo(() => getProblem(activeId) ?? PROBLEMS[0], [activeId])
  const [code, setCode] = useState(problem.starterCode)
  const [result, setResult] = useState<RunResult | null>(null)
  const [running, setRunning] = useState(false)
  const [toolchainReady, setToolchainReady] = useState(false)
  const [filterTopic, setFilterTopic] = useState<string>('all')
  const counts = useMemo(() => topicCounts(), [])

  const codeRef = useRef(code)
  const problemRef = useRef(problem)
  const resultRef = useRef(result)
  codeRef.current = code
  problemRef.current = problem
  resultRef.current = result

  useEffect(() => {
    preloadToolchain()
    ensureToolchain()
      .then(() => setToolchainReady(true))
      .catch(() => setToolchainReady(false))
  }, [])

  useEffect(() => {
    const saved = localStorage.getItem(draftKey(problem.id))
    setCode(saved ?? problem.starterCode)
    setResult(null)
  }, [problem])

  useEffect(() => {
    localStorage.setItem(draftKey(problem.id), code)
  }, [code, problem.id])

  async function handleSubmit(overrideCode?: string) {
    const currentProblem = problemRef.current
    const source = overrideCode ?? codeRef.current
    setRunning(true)
    setResult(null)
    try {
      const res = await runProblem(currentProblem, source)
      setResult(res)
      if (res.ok) {
        onSolved(markSolved(currentProblem.id))
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e)
      setResult({
        ok: false,
        compileError: msg,
        cases: [],
        passedCount: 0,
        totalCount: currentProblem.tests.length,
      })
    } finally {
      setRunning(false)
    }
  }

  useEffect(() => {
    const api = {
      setCode: (next: string) => {
        codeRef.current = next
        setCode(next)
      },
      getCode: () => codeRef.current,
      getResult: () => resultRef.current,
      submit: (overrideCode?: string) => handleSubmit(overrideCode),
    }
    ;(window as unknown as { __treePractice?: typeof api }).__treePractice = api
    return () => {
      delete (window as unknown as { __treePractice?: typeof api }).__treePractice
    }
  })

  function resetCode() {
    setCode(problem.starterCode)
    setResult(null)
  }

  const { lede, ioNote } = splitStatement(problem.statement)

  return (
    <div className="practice">
      <header className="practice__top">
        <div className="practice__top-left">
          <button type="button" className="btn btn--quiet" onClick={onBack}>
            ← 枝径
          </button>
          <span className="progress-pill">
            进度 {solved.size}/{PROBLEMS.length}
          </span>
        </div>
        <div className="progress-pill">
          {toolchainReady ? `C 工具链就绪 · ${PAGES_BUILD}` : '正在加载 C 工具链…'}
        </div>
      </header>

      <div className="practice__layout">
        <aside className="sidebar">
          <div className="sidebar__filters">
            <button
              type="button"
              className={`filter-chip ${filterTopic === 'all' ? 'is-active' : ''}`}
              onClick={() => setFilterTopic('all')}
            >
              全部 {PROBLEMS.length}
            </button>
            {TOPICS.map((t) => (
              <button
                type="button"
                key={t.id}
                className={`filter-chip ${filterTopic === t.id ? 'is-active' : ''}`}
                onClick={() => setFilterTopic(t.id)}
              >
                {t.name} {counts[t.id] ?? 0}
              </button>
            ))}
          </div>
          {TOPICS.filter((topic) => filterTopic === 'all' || filterTopic === topic.id).map(
            (topic) => {
              const list = PROBLEMS.filter((p) => p.topic === topic.id)
              if (!list.length) return null
              return (
                <div className="sidebar__topic" key={topic.id}>
                  <div className="sidebar__topic-name">
                    {topic.name}
                    <span className="sidebar__topic-count">{list.length}</span>
                  </div>
                  {list.map((p) => (
                    <button
                      type="button"
                      key={p.id}
                      className={`problem-link ${p.id === problem.id ? 'is-active' : ''}`}
                      onClick={() => setActiveId(p.id)}
                    >
                      <span
                        className={`dot ${solved.has(p.id) ? 'dot--done' : ''}`}
                        aria-hidden
                      />
                      <span className="problem-link__title">{p.title}</span>
                      <span className={difficultyClass(p.difficulty)}>
                        {p.difficulty}
                      </span>
                    </button>
                  ))}
                </div>
              )
            },
          )}
        </aside>

        <main className="workspace">
          <section className="statement">
            <h1>{problem.title}</h1>
            <div className="statement__meta">
              <span className={difficultyClass(problem.difficulty)}>
                {problem.difficulty}
              </span>
              <span>
                {TOPICS.find((t) => t.id === problem.topic)?.name}
              </span>
              <span className="statement__lang">C语言</span>
            </div>
            <p className="statement__body" style={{ whiteSpace: 'pre-wrap' }}>
              {lede}
            </p>
            <p className="statement__io-callout">
              请编写完整 C 程序（含 main）。判题经 stdin 注入用例，比较 stdout。
            </p>
            <h3>示例</h3>
            {problem.examples.map((ex, i) => (
              <div className="example" key={i}>
                <div>输入：{ex.input}</div>
                <div>输出：{ex.output}</div>
                {ex.explanation && <div>说明：{ex.explanation}</div>}
              </div>
            ))}
            {ioNote ? (
              <details className="statement__constraints">
                <summary>输入 / 输出格式</summary>
                <p style={{ whiteSpace: 'pre-wrap' }}>{ioNote}</p>
              </details>
            ) : null}
            <details className="statement__constraints">
              <summary>约束</summary>
              <ul>
                {problem.constraints.map((c) => (
                  <li key={c}>{c}</li>
                ))}
              </ul>
            </details>
          </section>

          <section className="editor-pane" aria-label="代码编辑器">
            <div className="editor-toolbar">
              <span className="editor-toolbar__lang">
                C · 完整程序 · {problem.functionName}
              </span>
              <div className="editor-toolbar__actions">
                <button type="button" className="btn btn--quiet" onClick={resetCode}>
                  重置代码
                </button>
                <button
                  type="button"
                  className="btn btn--solid"
                  onClick={() => void handleSubmit()}
                  disabled={running || !toolchainReady}
                >
                  {running ? '运行中…' : '提交'}
                </button>
              </div>
            </div>
            <CodeEditor value={code} onChange={setCode} />
          </section>

          <TestResults
            result={result}
            running={running}
            toolchainReady={toolchainReady}
          />
        </main>
      </div>
    </div>
  )
}
