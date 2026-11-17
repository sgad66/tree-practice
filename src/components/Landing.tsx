import { TOPICS, PROBLEMS, topicCounts } from '../data/problems'

interface Props {
  solvedCount: number
  onEnter: () => void
}

export function Landing({ solvedCount, onEnter }: Props) {
  const counts = topicCounts()

  return (
    <div className="landing">
      <div className="landing__atmosphere" aria-hidden />
      <header className="landing__nav">
        <div className="brand-mark">枝径</div>
        <div className="landing__nav-meta">
          {PROBLEMS.length} 题 · 已完成 {solvedCount} · C语言
        </div>
      </header>

      <section className="hero">
        <h1 className="hero__brand">
          <span>TreePath</span>
          枝径
        </h1>
        <p className="hero__lede">
          一百道二叉树专项题，按八大分类练习：遍历、基础属性、路径、BST、构造、
          LCA、层序视图与进阶综合。浏览器内编写完整 C 程序（含 main），提交即见失败用例与提示。
        </p>
        <div className="hero__actions">
          <button type="button" className="btn btn--primary" onClick={onEnter}>
            开始练习
          </button>
          <button type="button" className="btn btn--ghost" onClick={onEnter}>
            查看题库
          </button>
        </div>
      </section>

      <div className="landing__topics">
        {TOPICS.map((t, i) => (
          <div
            className="topic-chip"
            key={t.id}
            style={{ animationDelay: `${0.06 * i}s` }}
          >
            <strong>
              {t.name}
              <span className="topic-chip__count">{counts[t.id] ?? 0}</span>
            </strong>
            <span>{t.blurb}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
