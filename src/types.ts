export type Difficulty = '简单' | '中等' | '困难'

export type TopicId =
  | 'traversal'
  | 'basics'
  | 'path'
  | 'bst'
  | 'construct'
  | 'lca'
  | 'levelview'
  | 'advanced'

/** How the in-browser C harness prepares args / compares results. */
export type JudgeMode =
  | 'value' // first list-looking arg → tree; compare JSON value
  | 'trees' // every list-looking arg → tree; compare JSON value
  | 'tree_return' // like value, but return TreeNode → level-order list
  | 'trees_return' // every list-looking arg → tree; return TreeNode → list
  | 'raw' // keep arrays as arrays; compare JSON value
  | 'raw_tree_return' // keep arrays; return TreeNode → list
  | 'lca' // (tree, pVal, qVal) → return node.val
  | 'serialize' // round-trip serialize/deserialize

export type CParamKind =
  | 'tree'
  | 'int'
  | 'float'
  | 'bool'
  | 'string'
  | 'optional_int'
  | 'int_array'
  | 'double_array'
  | 'string_array'
  | 'int_matrix'
  | 'string_matrix'

export type CReturnKind =
  | CParamKind
  | 'serialize'

export interface CAbi {
  params: { name: string; kind: CParamKind }[]
  returnKind: CReturnKind
}

export interface Topic {
  id: TopicId
  name: string
  blurb: string
}

/** Level-order array representation (null = empty child), LeetCode style. */
export type TreeArray = (number | null)[]

export type JsonValue =
  | null
  | boolean
  | number
  | string
  | JsonValue[]
  | { [key: string]: JsonValue }

export interface TestCase {
  /** Human-readable input description for sample / failure UI */
  inputLabel: string
  /** Arguments passed to the solution function (JSON-serializable) */
  args: JsonValue[]
  /** Expected return value */
  expected: JsonValue
  /** Whether this case is shown in the problem statement */
  sample?: boolean
  /** Optional explicit hint override when this case fails */
  hint?: string
}

export interface Problem {
  id: string
  title: string
  topic: TopicId
  difficulty: Difficulty
  statement: string
  examples: { input: string; output: string; explanation?: string }[]
  constraints: string[]
  /** C function name the user must implement */
  functionName: string
  starterCode: string
  /** Extra C helpers injected before user code (rare) */
  harnessExtras?: string
  judgeMode?: JudgeMode
  /** Structured C ABI for the judge harness */
  cAbi: CAbi
  tests: TestCase[]
}

export interface CaseResult {
  index: number
  passed: boolean
  sample: boolean
  inputLabel: string
  expected: JsonValue
  actual?: JsonValue
  error?: string
  hint?: string
}

export interface RunResult {
  ok: boolean
  compileError?: string
  cases: CaseResult[]
  passedCount: number
  totalCount: number
}
