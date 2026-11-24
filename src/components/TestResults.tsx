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
        <div className="toolchain-banner is-running">
          <span className="spinner-dot" aria-hidden />
          正在浏览器中编译并运行 C（clang → WASM）…
        </div>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="results">
        <div className="toolchain-banner">
          {toolchainReady
            ? '编写 C 解法后点击「提交」（或按 Ctrl / ⌘ + Enter）。失败时会标出具体用例、期望与实际，并给出简短提示。'
            : '首次加载会拉取浏览器内 C 工具链（约数十 MB），稍候即可提交。'}
        </div>
      </div>
    )
  }

  if (result.compileError) {
    return (
      <div className="results">
        <div className="results__summary is-fail">✕ 编译 / 运行失败</div>
        <pre className="compile-error">{result.compileError}</pre>
      </div>
    )
  }

  return (
    <div className="results">
      <div
        className={`results__summary ${result.ok ? 'is-pass' : 'is-fail'}`}
      >
        <span>
          {result.ok
            ? `✓ 全部通过（${result.passedCount}/${result.totalCount}）`
            : `✕ 未通过（${result.passedCount}/${result.totalCount}）`}
        </span>
      </div>
      <div className="cases-list">
        {result.cases.map((c) => (
          <div className={`case ${c.passed ? 'case--ok' : 'case--bad'}`} key={c.index}>
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
                  <div className="case__cell">
                    <span className="case__cell-title">期望输出</span>
                    <code>{fmt(c.expected)}</code>
                  </div>
                  <div className="case__cell">
                    <span className="case__cell-title">实际输出</span>
                    <code>{c.error ? '（运行异常）' : fmt(c.actual)}</code>
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
    </div>
  )
}
