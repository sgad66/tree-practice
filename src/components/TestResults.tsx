import type { RunResult } from '../types'

interface Props {
  result: RunResult | null
  running: boolean
  toolchainReady: boolean
}

function fmt(v: unknown): string {
  if (v === undefined) return '（无返回值）'
  if (v === null) return 'null'
  try {
    return JSON.stringify(v)
  } catch {
    return String(v)
  }
}

export function TestResults({ result, running, toolchainReady }: Props) {
  if (running) {
    return (
      <div className="results">
        <div className="toolchain-banner">正在浏览器中编译并运行 C（clang → WASM）…</div>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="results">
        <div className="toolchain-banner">
          {toolchainReady
            ? '请编写完整 C 程序（含 main）后点击「提交」。每个用例经 stdin 注入，比较 stdout；失败时标出期望与实际。'
            : '首次加载会拉取浏览器内 C 工具链（约数十 MB），稍候即可提交。'}
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
