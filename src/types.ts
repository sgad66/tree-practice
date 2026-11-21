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
  | 'arrays'
  | 'stack'
  | 'queue'
  | 'linkedlist'
  | 'hash'
  | 'heap'
  | 'graph'
  | 'sorting'

/**
 * How stdin args are interpreted / expected stdout is shaped.
 * Judge compiles the user's full program and feeds each test via stdin.
 * I/O dialect: space/newline-separated numbers and NULL (no JSON brackets).
 */
export type JudgeMode =
  | 'value' // first list-looking arg → tree tokens; compare stdout tokens
  | 'trees' // every list-looking arg → tree tokens
  | 'tree_return' // like value; stdout is level-order tree tokens
  | 'trees_return' // every list-looking arg → tree; stdout tree tokens
  | 'raw' // keep arrays as token lines
  | 'raw_tree_return' // keep arrays; stdout tree tokens
  | 'lca' // stdin: tree, pVal, qVal → stdout node value
  | 'serialize' // stdin tree; stdout round-trip tree tokens

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

/** Describes how starter main maps stdin lines → solution call (documentation / generation). */
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
  /** Arguments (structured); judge emits token stdin (numbers / NULL) */
  args: JsonValue[]
  /** Expected stdout value (structured; compared via normalized tokens) */
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
  /** Suggested solution function name inside the full program */
  functionName: string
  /** Default editor contents — empty; users write a full program from scratch */
  starterCode: string
  /** @deprecated unused in full-program mode */
  harnessExtras?: string
  judgeMode?: JudgeMode
  /** Structured C ABI used to format stdin / starter main */
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
