import type { JsonValue } from '../types'

function isNumberArray(v: JsonValue): v is number[] {
  return Array.isArray(v) && v.every((x) => typeof x === 'number')
}

function sameMultiset(a: number[], b: number[]): boolean {
  if (a.length !== b.length) return false
  const sa = [...a].sort((x, y) => x - y)
  const sb = [...b].sort((x, y) => x - y)
  return sa.every((v, i) => v === sb[i])
}

/** Infer a short Chinese hint about the bug class from expected vs actual. */
export function inferHint(
  expected: JsonValue,
  actual: JsonValue | undefined,
  error?: string,
): string {
  if (error) {
    if (/NoneType|AttributeError.*None/i.test(error)) {
      return '空指针问题：访问了 None 的属性。递归前先判断节点是否为空。'
    }
    if (/IndexError|list index out of range/i.test(error)) {
      return '越界：数组/队列下标超出范围，检查 off-by-one 与空层处理。'
    }
    if (/RecursionError|maximum recursion/i.test(error)) {
      return '递归过深或未正确收敛：检查基线条件，是否对空节点仍继续递归。'
    }
    if (/NameError|is not defined/i.test(error)) {
      return '名称错误：函数名或变量未定义，请对照题目要求的函数签名。'
    }
    if (/TypeError/i.test(error)) {
      return '类型错误：参数个数或返回值类型与约定不符。'
    }
    return `运行出错：${error.split('\n').filter(Boolean).slice(-1)[0] ?? error}`
  }

  if (actual === undefined) {
    return '没有得到返回值：请确认函数有 return，且不要只写 pass。'
  }

  if (typeof expected === 'boolean' && typeof actual === 'boolean') {
    return '布尔结果相反：复查边界（空树、单节点、相等节点）与比较方向。'
  }

  if (typeof expected === 'number' && typeof actual === 'number') {
    if (actual === expected - 1 || actual === expected + 1) {
      return '疑似 off-by-one：深度/计数是节点数还是边数？空树返回值是否正确？'
    }
    if (actual === 0 && expected < 0) {
      return '负数路径被吞掉了：不要把答案默认初始化为 0。'
    }
    return '数值不对：检查是否漏统计某条子树，或在中途错误截断。'
  }

  if (isNumberArray(expected) && isNumberArray(actual)) {
    if (sameMultiset(expected, actual) && expected.join() !== actual.join()) {
      return '元素对但顺序不对：遍历次序（前/中/后/层序）写错了。'
    }
    if (actual.length === 0 && expected.length > 0) {
      return '返回了空列表：可能未真正遍历，或根为 None 时过早返回。'
    }
    return '序列不匹配：对照样例手推一遍遍历/构造过程。'
  }

  if (Array.isArray(expected) && Array.isArray(actual)) {
    const flatE = JSON.stringify(expected)
    const flatA = JSON.stringify(actual)
    if (flatE.replace(/[\[\],\s]/g, '') === flatA.replace(/[\[\],\s]/g, '')) {
      return '结构分组有误：层序应「按层分包」；或树的 null 占位丢失导致形状不对。'
    }
    return '结构或内容不匹配：注意 null 子节点与左右顺序。'
  }

  return '输出与期望不符：对比失败用例的输入，逐步跟踪递归状态。'
}
