import type { Problem, Topic } from '../types'
import { PROBLEMS_TRAVERSAL } from './categories/traversal'
import { PROBLEMS_BASICS } from './categories/basics'
import { PROBLEMS_PATH } from './categories/path'
import { PROBLEMS_BST } from './categories/bst'
import { PROBLEMS_CONSTRUCT } from './categories/construct'
import { PROBLEMS_LCA } from './categories/lca'
import { PROBLEMS_LEVELVIEW } from './categories/levelview'
import { PROBLEMS_ADVANCED } from './categories/advanced'

export const TOPICS: Topic[] = [
  { id: 'traversal', name: "遍历与序列", blurb: "前序 / 中序 / 后序与序列巩固" },
  { id: 'basics', name: "二叉树基础属性", blurb: "深度、对称、翻转、合并等" },
  { id: 'path', name: "路径与递归", blurb: "路径和、好节点、祖先差等" },
  { id: 'bst', name: "二叉搜索树 BST", blurb: "验证、搜索、插入删除、第 K 等" },
  { id: 'construct', name: "构造与序列化", blurb: "由遍历还原、编解码、展开" },
  { id: 'lca', name: "最近公共祖先与祖先关系", blurb: "LCA、距离、方向、堂兄弟" },
  { id: 'levelview', name: "层序与视图", blurb: "层序、锯齿、左右视图、垂直" },
  { id: 'advanced', name: "进阶 / 综合", blurb: "最大路径和、树 DP、翻转等价等" },
]

export const PROBLEMS: Problem[] = [
  ...PROBLEMS_TRAVERSAL,
  ...PROBLEMS_BASICS,
  ...PROBLEMS_PATH,
  ...PROBLEMS_BST,
  ...PROBLEMS_CONSTRUCT,
  ...PROBLEMS_LCA,
  ...PROBLEMS_LEVELVIEW,
  ...PROBLEMS_ADVANCED,
]

export function getProblem(id: string): Problem | undefined {
  return PROBLEMS.find((p) => p.id === id)
}

export function problemsByTopic(topic: Topic['id']): Problem[] {
  return PROBLEMS.filter((p) => p.topic === topic)
}

export function topicCounts(): Record<string, number> {
  const counts: Record<string, number> = {}
  for (const t of TOPICS) counts[t.id] = 0
  for (const p of PROBLEMS) counts[p.topic] = (counts[p.topic] ?? 0) + 1
  return counts
}
