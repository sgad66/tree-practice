import type { Problem, Topic } from '../types'
import { PROBLEMS_TRAVERSAL } from './categories/traversal'
import { PROBLEMS_BASICS } from './categories/basics'
import { PROBLEMS_PATH } from './categories/path'
import { PROBLEMS_BST } from './categories/bst'
import { PROBLEMS_CONSTRUCT } from './categories/construct'
import { PROBLEMS_LCA } from './categories/lca'
import { PROBLEMS_LEVELVIEW } from './categories/levelview'
import { PROBLEMS_ADVANCED } from './categories/advanced'
import { PROBLEMS_ARRAYS } from './categories/arrays'
import { PROBLEMS_STACK } from './categories/stack'
import { PROBLEMS_QUEUE } from './categories/queue'
import { PROBLEMS_LINKEDLIST } from './categories/linkedlist'
import { PROBLEMS_HASH } from './categories/hash'
import { PROBLEMS_HEAP } from './categories/heap'
import { PROBLEMS_GRAPH } from './categories/graph'
import { PROBLEMS_SORTING } from './categories/sorting'

export const TOPICS: Topic[] = [
  { id: 'traversal', name: "树·遍历与序列", blurb: "前序 / 中序 / 后序与序列巩固" },
  { id: 'basics', name: "树·基础属性", blurb: "深度、对称、翻转、合并等" },
  { id: 'path', name: "树·路径与递归", blurb: "路径和、好节点、祖先差等" },
  { id: 'bst', name: "树·二叉搜索树", blurb: "验证、搜索、插入删除、第 K、平衡" },
  { id: 'construct', name: "树·构造与序列化", blurb: "由遍历还原、编解码、展开" },
  { id: 'lca', name: "树·最近公共祖先", blurb: "LCA、距离、方向、堂兄弟" },
  { id: 'levelview', name: "树·层序与视图", blurb: "层序、锯齿、左右视图、垂直" },
  { id: 'advanced', name: "树·进阶综合", blurb: "最大路径和、树 DP、翻转等价等" },
  { id: 'arrays', name: "数组与列表", blurb: "双指针、前缀、原地修改、经典扫描" },
  { id: 'stack', name: "栈", blurb: "括号、单调栈、表达式与直方图" },
  { id: 'queue', name: "队列", blurb: "滑窗、模拟、循环队列与调度" },
  { id: 'linkedlist', name: "链表", blurb: "反转、合并、环、双指针技巧" },
  { id: 'hash', name: "哈希表", blurb: "计数、前缀和、映射与去重" },
  { id: 'heap', name: "堆与优先队列", blurb: "Top-K、多路归并、调度" },
  { id: 'graph', name: "图论基础", blurb: "BFS/DFS、最短路、连通性、网格" },
  { id: 'sorting', name: "排序与查找", blurb: "二分、区间、基础排序" },
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
  ...PROBLEMS_ARRAYS,
  ...PROBLEMS_STACK,
  ...PROBLEMS_QUEUE,
  ...PROBLEMS_LINKEDLIST,
  ...PROBLEMS_HASH,
  ...PROBLEMS_HEAP,
  ...PROBLEMS_GRAPH,
  ...PROBLEMS_SORTING,
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
