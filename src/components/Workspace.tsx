import { useEffect, useMemo, useRef, useState } from 'react'
import { PROBLEMS, TOPICS, getProblem, topicCounts } from '../data/problems'
import type { Problem, RunResult } from '../types'
import { CodeEditor } from './CodeEditor'
import { TestResults } from './TestResults'
import {
  runProblem,
  preloadToolchain,
  ensureToolchain,
  PAGES_BUILD,
} from '../lib/clangJudge'
import { markSolved } from '../lib/progress'

interface Props {
  initialId?: string
  initialTopic?: string
  solved: Set<string>
  onSolved: (ids: Set<string>) => void
  theme: 'paper' | 'forest'
  onToggleTheme: () => void
  onBack: () => void
}

const draftKey = (id: string) => `tree-practice:draft:c:${id}`

function difficultyClass(d: Problem['difficulty']): string {
  if (d === '简单') return 'badge badge--easy'
  if (d === '中等') return 'badge badge--mid'
  return 'badge badge--hard'
}

export function Workspace({
  initialId,
  initialTopic = 'all',
  solved,
  onSolved,
  theme,
  onToggleTheme,
  onBack,
}: Props) {
  const [filterTopic, setFilterTopic] = useState<string>(initialTopic)
  const [filterDiff, setFilterDiff] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(true)
  const [splitLayout, setSplitLayout] = useState<boolean>(true)
  const [confirmReset, setConfirmReset] = useState<boolean>(false)
  const [copiedId, setCopiedId] = useState<string | null>(null)

  const defaultId = useMemo(() => {
    if (initialId) return initialId
    if (initialTopic !== 'all') {
      const topicMatch =
        PROBLEMS.find((p) => p.topic === initialTopic && !solved.has(p.id)) ??
        PROBLEMS.find((p) => p.topic === initialTopic)
      if (topicMatch) return topicMatch.id
    }
    return PROBLEMS[0]?.id ?? 'preorder'
  }, [initialId, initialTopic, solved])

  const [activeId, setActiveId] = useState(defaultId)
  const problem = useMemo(() => getProblem(activeId) ?? PROBLEMS[0], [activeId])
  const [code, setCode] = useState(problem.starterCode)
  const [result, setResult] = useState<RunResult | null>(null)
  const [running, setRunning] = useState(false)
  const [toolchainReady, setToolchainReady] = useState(false)
  const counts = useMemo(() => topicCounts(), [])

  const searchInputRef = useRef<HTMLInputElement>(null)
  const codeRef = useRef(code)
  const problemRef = useRef(problem)
  const resultRef = useRef(result)
  codeRef.current = code
  problemRef.current = problem
  resultRef.current = result

  const visibleProblems = useMemo(() => {
    const q = searchQuery.trim().toLowerCase()
    return PROBLEMS.filter((p) => {
      const okTopic = filterTopic === 'all' || p.topic === filterTopic
      const okDiff = filterDiff === 'all' || p.difficulty === filterDiff
      const okQuery =
        !q ||
        p.title.toLowerCase().includes(q) ||
        p.statement.toLowerCase().includes(q)
      return okTopic && okDiff && okQuery
    })
  }, [filterTopic, filterDiff, searchQuery])

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
    setConfirmReset(false)
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

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        if (!running && toolchainReady) {
          e.preventDefault()
          void handleSubmit()
        }
      } else if (
        e.key === '/' &&
        !['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement)?.tagName) &&
        !(e.target as HTMLElement)?.closest('.cm-editor')
      ) {
        e.preventDefault()
        setSidebarOpen(true)
        setTimeout(() => searchInputRef.current?.focus(), 20)
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [running, toolchainReady])

  function confirmResetCode() {
    setCode(problem.starterCode)
    setResult(null)
    setConfirmReset(false)
  }

  function copyText(text: string, tag: string) {
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(text).catch(() => {})
    }
    setCopiedId(tag)
    setTimeout(() => setCopiedId((prev) => (prev === tag ? null : prev)), 1600)
  }

  function stepProblem(delta: number) {
    const list = visibleProblems.length ? visibleProblems : PROBLEMS
    const idx = list.findIndex((p) => p.id === problem.id)
    const nextIdx =
      idx === -1 ? 0 : (idx + delta + list.length) % list.length
    setActiveId(list[nextIdx].id)
  }

  const progressPct =
    PROBLEMS.length > 0
      ? Math.round((solved.size / PROBLEMS.length) * 100)
      : 0

  return (
    <div className={`practice ${splitLayout ? 'practice--split' : ''}`}>
      <header className="practice__top">
        <div className="practice__top-left">
          <button type="button" className="btn btn--quiet" onClick={onBack}>
            ← 枝径
          </button>
          <button
            type="button"
            className="btn btn--quiet"
            onClick={() => setSidebarOpen((v) => !v)}
          >
            {sidebarOpen ? '收起题库' : '展开题库'}
          </button>
          <div className="progress-pill progress-pill--bar">
            <span>
              进度 {solved.size}/{PROBLEMS.length} ({progressPct}%)
            </span>
            <span className="progress-track" aria-hidden>
              <span
                className="progress-fill"
                style={{ width: `${progressPct}%` }}
              />
            </span>
          </div>
        </div>

        <div className="practice__top-right">
          <button
            type="button"
            className="btn btn--quiet layout-toggle-btn"
            onClick={() => setSplitLayout((v) => !v)}
          >
            {splitLayout ? '上下视图' : '左右分栏'}
          </button>
          <button
            type="button"
            className="btn btn--quiet"
            onClick={onToggleTheme}
            title="切换主题"
          >
            {theme === 'forest' ? '☀ 宣纸' : '☾ 松烟'}
          </button>
          <span className="toolchain-pill">
            <span
              className={`toolchain-dot ${toolchainReady ? 'is-ready' : ''}`}
              aria-hidden
            />
            {toolchainReady ? `C 就绪 · ${PAGES_BUILD}` : '加载 C 工具链…'}
          </span>
        </div>
      </header>

      <div
        className={`practice__layout ${sidebarOpen ? '' : 'is-sidebar-collapsed'}`}
      >
        {sidebarOpen && (
          <aside className="sidebar">
            <div className="sidebar__search">
              <input
                ref={searchInputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="搜索题目（按 / 聚焦）…"
                className="sidebar__search-input"
              />
              {searchQuery && (
                <button
                  type="button"
                  className="sidebar__search-clear"
                  onClick={() => setSearchQuery('')}
                  title="清空搜索"
                >
                  ×
                </button>
              )}
            </div>

            <div className="sidebar__diff-row">
              {(['all', '简单', '中等', '困难'] as const).map((d) => (
                <button
                  type="button"
                  key={d}
                  className={`filter-chip ${filterDiff === d ? 'is-active' : ''}`}
                  onClick={() => setFilterDiff(d)}
                >
                  {d === 'all' ? '全部难度' : d}
                </button>
              ))}
            </div>

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

            {visibleProblems.length === 0 ? (
              <div className="sidebar__empty">
                没有匹配的题目，试试调整筛选条件
              </div>
            ) : (
              TOPICS.filter(
                (topic) => filterTopic === 'all' || filterTopic === topic.id,
              ).map((topic) => {
                const list = visibleProblems.filter((p) => p.topic === topic.id)
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
              })
            )}
          </aside>
        )}

        <main className="workspace">
          <section className="statement">
            <div className="statement__header">
              <h1>{problem.title}</h1>
              <div className="statement__nav-btns">
                <button
                  type="button"
                  className="btn btn--quiet btn--xs"
                  onClick={() => stepProblem(-1)}
                  title="上一题"
                >
                  ← 上一题
                </button>
                <button
                  type="button"
                  className="btn btn--quiet btn--xs"
                  onClick={() => stepProblem(1)}
                  title="下一题"
                >
                  下一题 →
                </button>
              </div>
            </div>

            <div className="statement__meta">
              <span className={difficultyClass(problem.difficulty)}>
                {problem.difficulty}
              </span>
              <span className="statement__topic-tag">
                {TOPICS.find((t) => t.id === problem.topic)?.name}
              </span>
              <span className="statement__lang">C 语言</span>
              {solved.has(problem.id) && (
                <span className="statement__solved">✓ 已通过</span>
              )}
            </div>

            <p style={{ whiteSpace: 'pre-wrap' }}>{problem.statement}</p>

            <h3>示例</h3>
            {problem.examples.map((ex, i) => (
              <div className="example" key={i}>
                <div className="example__row">
                  <span>输入：{ex.input}</span>
                  <button
                    type="button"
                    className="copy-mini"
                    onClick={() => copyText(ex.input, `ex-${i}`)}
                  >
                    {copiedId === `ex-${i}` ? '已复制' : '复制输入'}
                  </button>
                </div>
                <div>输出：{ex.output}</div>
                {ex.explanation && (
                  <div className="example__exp">说明：{ex.explanation}</div>
                )}
              </div>
            ))}

            <h3>约束</h3>
            <ul>
              {problem.constraints.map((c) => (
                <li key={c}>{c}</li>
              ))}
            </ul>
          </section>

          <div className="workspace__right">
            <section className="editor-pane">
              <div className="editor-toolbar">
                <span className="editor-toolbar__lang">
                  C11 · {problem.functionName}
                </span>
                <div className="editor-toolbar__actions">
                  <button
                    type="button"
                    className="btn btn--quiet"
                    onClick={() => copyText(code, 'code')}
                  >
                    {copiedId === 'code' ? '已复制 ✓' : '复制代码'}
                  </button>
                  <button
                    type="button"
                    className="btn btn--quiet"
                    onClick={() => setConfirmReset(true)}
                  >
                    重置代码
                  </button>
                  <button
                    type="button"
                    className="btn btn--solid"
                    onClick={() => void handleSubmit()}
                    disabled={running || !toolchainReady}
                    title="Ctrl / Cmd + Enter 提交"
                  >
                    {running ? '运行中…' : '提交评测'}
                  </button>
                </div>
              </div>

              {confirmReset && (
                <div className="reset-banner">
                  <span>确认恢复为本题初始代码模板吗？</span>
                  <div className="reset-banner__actions">
                    <button
                      type="button"
                      className="btn btn--danger-mini"
                      onClick={confirmResetCode}
                    >
                      确认重置
                    </button>
                    <button
                      type="button"
                      className="btn btn--quiet btn--xs"
                      onClick={() => setConfirmReset(false)}
                    >
                      取消
                    </button>
                  </div>
                </div>
              )}

              <CodeEditor value={code} onChange={setCode} />
            </section>

            <TestResults
              result={result}
              running={running}
              toolchainReady={toolchainReady}
            />
          </div>
        </main>
      </div>
    </div>
  )
}
