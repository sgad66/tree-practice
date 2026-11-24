import { TOPICS, PROBLEMS, topicCounts } from '../data/problems'

interface Props {
  solved: Set<string>
  solvedCount: number
  theme: 'paper' | 'forest'
  onToggleTheme: () => void
  onEnter: (topicId?: string) => void
}

export function Landing({
  solved,
  solvedCount,
  theme,
  onToggleTheme,
  onEnter,
}: Props) {
  const counts = topicCounts()
  const total = PROBLEMS.length
  const pct = total > 0 ? Math.round((solvedCount / total) * 100) : 0

  return (
    <div className="landing">
      <div className="landing__atmosphere" aria-hidden />
      <header className="landing__nav">
        <div className="brand-mark">
          <span className="brand-mark__dot" aria-hidden />
          枝径 <small>TREEPATH</small>
        </div>
        <div className="landing__nav-right">
          <div className="landing__nav-meta">
            {total} 题 · 已完成 {solvedCount} ({pct}%) · C 语言
          </div>
          <button
            type="button"
            className="btn btn--theme"
            onClick={onToggleTheme}
            title="切换宣纸亮色 / 松烟暗色"
          >
            {theme === 'forest' ? '☀ 宣纸亮' : '☾ 松烟暗'}
          </button>
        </div>
      </header>

      <section className="hero">
        <div className="hero__badge">浏览器内 C 工具链 · stdin / stdout 实时评测</div>
        <h1 className="hero__brand">
          <span>TreePath</span>
          枝径
        </h1>
        <p className="hero__lede">
          {total} 道数据结构与算法专项练习，覆盖二叉树核心专题与系统章节：遍历、基础属性、路径、BST、构造、LCA、层序视图与进阶综合。浏览器内写 C 语言，提交即见失败用例与提示。
        </p>
        <div className="hero__actions">
          <button
            type="button"
            className="btn btn--primary"
            onClick={() => onEnter('all')}
          >
            开始练习 →
          </button>
          <button
            type="button"
            className="btn btn--ghost"
            onClick={() => {
              document
                .getElementById('landing-topics')
                ?.scrollIntoView({ behavior: 'smooth' })
            }}
          >
            浏览专题 ({TOPICS.length})
          </button>
        </div>
      </section>

      <div id="landing-topics" className="landing__topics">
        {TOPICS.map((t, i) => {
          const totalInTopic = counts[t.id] ?? 0
          const doneInTopic = PROBLEMS.filter(
            (p) => p.topic === t.id && solved.has(p.id),
          ).length
          const topicPct =
            totalInTopic > 0 ? Math.round((doneInTopic / totalInTopic) * 100) : 0

          return (
            <button
              type="button"
              className="topic-chip"
              key={t.id}
              style={{ animationDelay: `${0.04 * i}s` }}
              onClick={() => onEnter(t.id)}
            >
              <div className="topic-chip__top">
                <strong>{t.name}</strong>
                <span className="topic-chip__count">{totalInTopic} 题</span>
              </div>
              <span className="topic-chip__blurb">{t.blurb}</span>
              <div className="topic-chip__progress">
                <div className="topic-chip__bar">
                  <div
                    className="topic-chip__fill"
                    style={{ width: `${topicPct}%` }}
                  />
                </div>
                <span>
                  {doneInTopic}/{totalInTopic}
                </span>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
