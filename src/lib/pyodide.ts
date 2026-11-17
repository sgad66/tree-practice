import type { JsonValue, Problem, RunResult, CaseResult } from '../types'
import { inferHint } from './hints'

type PyodideInterface = {
  runPythonAsync: (code: string) => Promise<unknown>
  globals: {
    get: (name: string) => { toString: () => string } | string | null | undefined
    set: (name: string, value: unknown) => void
  }
}

declare global {
  interface Window {
    loadPyodide?: (opts?: { indexURL?: string }) => Promise<PyodideInterface>
  }
}

let pyodidePromise: Promise<PyodideInterface> | null = null

const PYODIDE_INDEX = 'https://cdn.jsdelivr.net/pyodide/v0.26.4/full/'

function loadScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${src}"]`)
    if (existing) {
      resolve()
      return
    }
    const s = document.createElement('script')
    s.src = src
    s.async = true
    s.onload = () => resolve()
    s.onerror = () => reject(new Error('无法加载 Pyodide 脚本，请检查网络。'))
    document.head.appendChild(s)
  })
}

export async function getPyodide(): Promise<PyodideInterface> {
  if (!pyodidePromise) {
    pyodidePromise = (async () => {
      await loadScript(`${PYODIDE_INDEX}pyodide.js`)
      if (!window.loadPyodide) throw new Error('Pyodide 未就绪')
      return window.loadPyodide({ indexURL: PYODIDE_INDEX })
    })()
  }
  return pyodidePromise
}

const TREE_HELPERS = `
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def _build_tree(arr):
    if not arr:
        return None
    nodes = [None if v is None else TreeNode(v) for v in arr]
    kids = 1
    for i, node in enumerate(nodes):
        if node is None:
            continue
        if kids < len(nodes):
            node.left = nodes[kids]
            kids += 1
        if kids < len(nodes):
            node.right = nodes[kids]
            kids += 1
    return nodes[0]

def _tree_to_list(root):
    if root is None:
        return []
    out = []
    q = [root]
    while q:
        node = q.pop(0)
        if node is None:
            out.append(None)
        else:
            out.append(node.val)
            q.append(node.left)
            q.append(node.right)
    while out and out[-1] is None:
        out.pop()
    return out

def _find_node(root, val):
    if root is None:
        return None
    if root.val == val:
        return root
    return _find_node(root.left, val) or _find_node(root.right, val)

def _deep_eq(a, b):
    return a == b
`

function escapePyString(s: string): string {
  return JSON.stringify(s)
}

function buildJudgeScript(problem: Problem, userCode: string): string {
  const testsJson = JSON.stringify(
    problem.tests.map((t) => ({
      args: t.args,
      expected: t.expected,
      inputLabel: t.inputLabel,
      sample: !!t.sample,
      hint: t.hint ?? null,
    })),
  )

  const mode = problem.judgeMode ?? 'value'

  return `
import json
import traceback

${TREE_HELPERS}
${problem.harnessExtras ?? ''}

_user_src = ${escapePyString(userCode)}

_compile_error = None
try:
    exec(_user_src, globals())
except Exception as e:
    _compile_error = traceback.format_exc()

_tests = json.loads(${escapePyString(testsJson)})
_fn_name = ${escapePyString(problem.functionName)}
_mode = ${escapePyString(mode)}
_results = []

def _looks_like_tree_arr(a):
    return isinstance(a, list) and (len(a) == 0 or all(x is None or isinstance(x, (int, float)) for x in a))

def _prepare_args(args, mode):
    prepared = []
    for i, a in enumerate(args):
        if not _looks_like_tree_arr(a):
            prepared.append(a)
            continue
        if mode in ('raw', 'raw_tree_return'):
            prepared.append(list(a))
        elif mode in ('trees', 'trees_return'):
            prepared.append(_build_tree(a))
        elif mode in ('value', 'tree_return', 'serialize', 'lca'):
            prepared.append(_build_tree(a) if i == 0 else a)
        else:
            prepared.append(a)
    return prepared

if _compile_error:
    _out = {"compileError": _compile_error, "cases": []}
else:
    if _mode != 'serialize' and _fn_name not in globals():
        _out = {"compileError": f"未找到函数 {_fn_name}，请检查函数名是否与题目一致。", "cases": []}
    elif _mode == 'serialize' and ('serialize' not in globals() or 'deserialize' not in globals()):
        _out = {"compileError": "需要实现 serialize 与 deserialize（或 Codec 类中的对应方法，并由顶层函数转发）。", "cases": []}
    else:
        for idx, t in enumerate(_tests):
            case = {
                "index": idx,
                "passed": False,
                "sample": t.get("sample", False),
                "inputLabel": t["inputLabel"],
                "expected": t["expected"],
                "hint": t.get("hint"),
            }
            try:
                if _mode == 'serialize':
                    root = _build_tree(t["args"][0])
                    data = serialize(root)
                    rebuilt = deserialize(data)
                    actual = _tree_to_list(rebuilt)
                    case["actual"] = actual
                    case["passed"] = _deep_eq(actual, t["expected"])
                elif _mode == 'lca':
                    root = _build_tree(t["args"][0])
                    p = _find_node(root, t["args"][1])
                    q = _find_node(root, t["args"][2])
                    res = globals()[_fn_name](root, p, q)
                    actual = None if res is None else res.val
                    case["actual"] = actual
                    case["passed"] = actual == t["expected"]
                elif _mode in ('tree_return', 'trees_return', 'raw_tree_return'):
                    prepared = _prepare_args(t["args"], _mode)
                    res = globals()[_fn_name](*prepared)
                    actual = _tree_to_list(res)
                    case["actual"] = actual
                    case["passed"] = _deep_eq(actual, t["expected"])
                else:
                    prepared = _prepare_args(t["args"], _mode)
                    raw_actual = globals()[_fn_name](*prepared)
                    actual = json.loads(json.dumps(raw_actual))
                    case["actual"] = actual
                    case["passed"] = _deep_eq(actual, t["expected"])
            except Exception:
                case["error"] = traceback.format_exc()
                case["passed"] = False
            _results.append(case)
        _out = {"compileError": None, "cases": _results}

_JUDGE_OUT_JSON = json.dumps(_out, ensure_ascii=False)
`
}

function readJudgeJson(py: PyodideInterface): string {
  const proxy = py.globals.get('_JUDGE_OUT_JSON')
  if (proxy == null) {
    throw new Error('判题结果缺失')
  }
  if (typeof proxy === 'string') return proxy
  return proxy.toString()
}

export async function runProblem(
  problem: Problem,
  userCode: string,
): Promise<RunResult> {
  const py = await getPyodide()
  const script = buildJudgeScript(problem, userCode)
  let raw: string
  try {
    await py.runPythonAsync(script)
    raw = readJudgeJson(py)
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e)
    return {
      ok: false,
      compileError: msg,
      cases: [],
      passedCount: 0,
      totalCount: problem.tests.length,
    }
  }

  let parsed: {
    compileError: string | null
    cases: Array<{
      index: number
      passed: boolean
      sample: boolean
      inputLabel: string
      expected: JsonValue
      actual?: JsonValue
      error?: string
      hint?: string | null
    }>
  }
  try {
    parsed = JSON.parse(raw) as typeof parsed
  } catch {
    parsed = { compileError: `判题结果解析失败：${raw.slice(0, 200)}`, cases: [] }
  }

  if (parsed.compileError) {
    return {
      ok: false,
      compileError: parsed.compileError,
      cases: [],
      passedCount: 0,
      totalCount: problem.tests.length,
    }
  }

  const cases: CaseResult[] = parsed.cases.map((c) => {
    const hint =
      c.passed
        ? undefined
        : c.hint || inferHint(c.expected, c.actual, c.error)
    return {
      index: c.index,
      passed: c.passed,
      sample: c.sample,
      inputLabel: c.inputLabel,
      expected: c.expected,
      actual: c.actual,
      error: c.error,
      hint,
    }
  })

  const passedCount = cases.filter((c) => c.passed).length
  return {
    ok: passedCount === cases.length && cases.length > 0,
    cases,
    passedCount,
    totalCount: cases.length,
  }
}

export function preloadPyodide(): void {
  void getPyodide().catch(() => {
    /* surfaced on first submit */
  })
}
