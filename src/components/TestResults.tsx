import type { RunResult } from '../types'

interface Props {
  result: RunResult | null
  running: boolean
  pyodideReady: boolean
}

function fmt(v: unknown): string {
  if (v === undefined) return '（无返回值）'
  if (v === null) return 'null（None）'
  try {
    return JSON.stringify(v)
  } catch {
    return String(v)
  }
}

export function TestResults({ result, running, pyodideReady }: Props) {
  if (running) {
    return (
      <div className="results">
        <div className="pyodide-banner">正在浏览器中运行 Python（Pyodide）…</div>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="results">
        <div className="pyodide-banner">
          {pyodideReady
            ? '编写解法后点击「提交」。失败时会标出具体用例、期望与实际，并给出简短提示。'
            : '首次加载会拉取 Pyodide 运行时，稍候即可提交。'}
        </div>
      </div>
    )
  }

  if (result.compileError) {
    return (
      <div className="results">
        <div className="results__summary is-fail">未能运行</div>
        <pre className="compile-error">{result.compileError}</pre>
      </div>
    )
  }

  return (
    <div className="results">
      <div
        className={`results__summary ${result.ok ? 'is-pass' : 'is-fail'}`}
      >
        {result.ok
          ? `全部通过（${result.passedCount}/${result.totalCount}）`
          : `未通过（${result.passedCount}/${result.totalCount}）`}
      </div>
      {result.cases.map((c) => (
        <div className="case" key={c.index}>
          <div className="case__head">
            <span className={`case__status ${c.passed ? 'ok' : 'bad'}`}>
              {c.passed ? '通过' : '失败'}
            </span>
            <span className="case__label">
              用例 {c.index + 1}
              {c.sample ? ' · 样例' : ' · 隐藏'}
            </span>
            <span className="case__label">{c.inputLabel}</span>
          </div>
          {!c.passed && (
            <>
              <div className="case__grid">
                <div>期望：{fmt(c.expected)}</div>
                <div>
                  实际：
                  {c.error ? '（运行异常）' : fmt(c.actual)}
                </div>
              </div>
              {c.hint && <div className="hint">{c.hint}</div>}
              {c.error && (
                <pre className="compile-error" style={{ marginTop: '0.5rem' }}>
                  {c.error}
                </pre>
              )}
            </>
          )}
        </div>
      ))}
    </div>
  )
}
