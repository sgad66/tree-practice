import type {
  CParamKind,
  JsonValue,
  Problem,
  RunResult,
  CaseResult,
} from '../types'
import { inferHint } from './hints'
import type { WasRunRequest, WasRunResponse } from './wasiRunner.worker'
import {
  MEMORY_EXCEEDED_MESSAGE,
  STDOUT_EXCEEDED_MESSAGE,
} from './wasiRunner.worker'

type CompileFn = (job: {
  source: string
  fileName: string
  flags: string[]
}) => Promise<{ compileOutput: string; module: WebAssembly.Module | null }>

const BROWSERCC_CDN =
  'https://cdn.jsdelivr.net/npm/browsercc@0.1.1/dist/index.js'

/** Per test-case wall-time limit for WASI execution (ms). */
export const RUN_TIMEOUT_MS = 2500

/** Wall-time limit for one compile job (ms). */
export const COMPILE_TIMEOUT_MS = 45000

/** Wall-time limit for loading the browsercc entry (ms). */
export const TOOLCHAIN_LOAD_TIMEOUT_MS = 60000

/** WASM linear-memory ceiling (bytes). Enforced via linker --max-memory. */
export const MEMORY_LIMIT_BYTES = 32 * 1024 * 1024

/** Cap captured stdout+stderr per case (bytes). */
export const MAX_STDOUT_BYTES = 256 * 1024

/** Truncate long compiler diagnostics shown in the UI. */
export const MAX_COMPILE_OUTPUT_CHARS = 8000

export const TIMEOUT_MESSAGE = '运行超时（可能死循环）'
export const EMPTY_SUBMIT_MESSAGE =
  '提交内容为空：请编写完整 C 程序（含 main）。'
export const MISSING_MAIN_MESSAGE =
  '未找到 main 函数：请编写完整 C 程序（含 main）。'
export const COMPILE_TIMEOUT_MESSAGE = '编译超时：请简化代码后重试。'
export const TOOLCHAIN_TIMEOUT_MESSAGE =
  '工具链加载超时：请检查网络后刷新重试。'
export const CANCELLED_MESSAGE = '已取消：检测到新的提交。'
export { MEMORY_EXCEEDED_MESSAGE, STDOUT_EXCEEDED_MESSAGE }

let compilePromise: Promise<CompileFn> | null = null
let toolchainReady = false
let warmed = false

/** Monotonic generation so a newer submit cancels in-flight work. */
let activeRunId = 0
const activeWorkers = new Set<Worker>()

export function cancelActiveRun(): void {
  activeRunId += 1
  for (const w of activeWorkers) {
    try {
      w.terminate()
    } catch {
      /* ignore */
    }
  }
  activeWorkers.clear()
}

function isCancelled(runId: number): boolean {
  return runId !== activeRunId
}

function withTimeout<T>(
  promise: Promise<T>,
  ms: number,
  message: string,
): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error(message)), ms)
    promise.then(
      (v) => {
        clearTimeout(timer)
        resolve(v)
      },
      (e) => {
        clearTimeout(timer)
        reject(e)
      },
    )
  })
}

function truncateCompileOutput(text: string): string {
  const t = text.trim()
  if (t.length <= MAX_COMPILE_OUTPUT_CHARS) return t
  return `${t.slice(0, MAX_COMPILE_OUTPUT_CHARS)}\n…（编译输出过长，已截断）`
}

function classifyHostError(msg: string): string {
  if (/运行超时|死循环/.test(msg)) return TIMEOUT_MESSAGE
  if (/内存超限|out of memory|Unable to grow|failed to grow|oom/i.test(msg)) {
    return MEMORY_EXCEEDED_MESSAGE
  }
  if (/输出超限/.test(msg)) return STDOUT_EXCEEDED_MESSAGE
  if (/已取消/.test(msg)) return CANCELLED_MESSAGE
  return msg
}

async function getCompile(): Promise<CompileFn> {
  if (!compilePromise) {
    compilePromise = (async () => {
      const mod = (await withTimeout(
        import(/* @vite-ignore */ BROWSERCC_CDN) as Promise<{
          compile: CompileFn
        }>,
        TOOLCHAIN_LOAD_TIMEOUT_MS,
        TOOLCHAIN_TIMEOUT_MESSAGE,
      )) as { compile: CompileFn }
      return mod.compile
    })()
  }
  return compilePromise
}

/** Load browsercc entry (CDN). Heavy clang.wasm download happens on first compile. */
export async function ensureToolchain(): Promise<void> {
  await getCompile()
  toolchainReady = true
}

async function warmCompileOnce(compile: CompileFn): Promise<void> {
  if (warmed) return
  warmed = true
  try {
    await withTimeout(
      compile({
        source: '#include <stdio.h>\nint main(void){puts("ok");return 0;}\n',
        fileName: 'warm.cpp',
        flags: [
          '-std=c++17',
          '-fno-exceptions',
          '-O0',
          `-Wl,--max-memory=${MEMORY_LIMIT_BYTES}`,
        ],
      }),
      COMPILE_TIMEOUT_MS,
      COMPILE_TIMEOUT_MESSAGE,
    )
  } catch {
    warmed = false
  }
}

export function preloadToolchain(): void {
  void ensureToolchain()
    .then(async () => {
      const compile = await getCompile()
      void warmCompileOnce(compile)
    })
    .catch(() => {
      /* surfaced on first submit / ready banner */
    })
}

export function isToolchainReady(): boolean {
  return toolchainReady
}

/** Canonical stdout line for an expected JSON value. */
export function formatStdoutValue(v: JsonValue): string {
  if (typeof v === 'boolean') return v ? 'true' : 'false'
  if (typeof v === 'number') {
    if (Number.isInteger(v)) return String(v)
    // Match starter printf("%.10g")
    return Number(v).toPrecision(10).replace(/\.?0+$/, '') === String(v)
      ? String(v)
      : JSON.stringify(v).replace(/^"|"$/g, '') || String(v)
  }
  return JSON.stringify(v)
}

function looksLikeTreeArr(a: JsonValue): a is (number | null)[] {
  return (
    Array.isArray(a) &&
    (a.length === 0 ||
      a.every((x) => x === null || typeof x === 'number'))
  )
}

function formatArgLine(arg: JsonValue, kind: CParamKind | undefined): string {
  if (kind === 'bool' || typeof arg === 'boolean') {
    return arg ? 'true' : 'false'
  }
  if (kind === 'string' || typeof arg === 'string') {
    return String(arg)
  }
  if (kind === 'int' || kind === 'float' || typeof arg === 'number') {
    return String(arg)
  }
  // trees, arrays, matrices — JSON line (null stays null)
  return JSON.stringify(arg)
}

function prepareArgKind(
  mode: string,
  argIndex: number,
  arg: JsonValue,
  paramKind: CParamKind | undefined,
): CParamKind {
  if (paramKind) return paramKind
  if (looksLikeTreeArr(arg)) {
    if (mode === 'raw' || mode === 'raw_tree_return') return 'int_array'
    if (mode === 'trees' || mode === 'trees_return') return 'tree'
    if (
      mode === 'value' ||
      mode === 'tree_return' ||
      mode === 'serialize' ||
      mode === 'lca'
    ) {
      return argIndex === 0 ? 'tree' : 'int'
    }
  }
  if (typeof arg === 'number') {
    return Number.isInteger(arg) ? 'int' : 'float'
  }
  if (typeof arg === 'boolean') return 'bool'
  if (typeof arg === 'string') return 'string'
  if (Array.isArray(arg) && arg.every((x) => Array.isArray(x))) return 'int_matrix'
  if (Array.isArray(arg) && arg.every((x) => typeof x === 'number')) return 'int_array'
  return 'int'
}

/** Build stdin for one test case from problem ABI + args. */
export function formatStdin(problem: Problem, args: JsonValue[]): string {
  const mode = problem.judgeMode ?? 'value'
  const lines: string[] = []

  if (mode === 'lca') {
    // tree, pVal, qVal — each on its own line
    lines.push(JSON.stringify(args[0] ?? []))
    lines.push(String(args[1]))
    lines.push(String(args[2]))
    return lines.join('\n') + '\n'
  }

  if (mode === 'serialize') {
    lines.push(JSON.stringify(args[0] ?? []))
    return lines.join('\n') + '\n'
  }

  const paramKinds = problem.cAbi?.params?.map((p) => p.kind) ?? []
  args.forEach((arg, ai) => {
    const kind = prepareArgKind(mode, ai, arg, paramKinds[ai])
    lines.push(formatArgLine(arg, kind))
  })
  return lines.join('\n') + '\n'
}

function deepEq(a: JsonValue, b: JsonValue): boolean {
  if (typeof a === 'number' && typeof b === 'number') {
    if (Number.isNaN(a) && Number.isNaN(b)) return true
    return Math.abs(a - b) < 1e-6
  }
  return JSON.stringify(a) === JSON.stringify(b)
}

function parseStdout(raw: string): { value?: JsonValue; error?: string } {
  const text = raw.replace(/^\uFEFF/, '').trim()
  if (!text) return { error: '程序无 stdout 输出' }
  // Prefer last non-empty line (ignore debug prints)
  const lines = text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean)
  const last = lines[lines.length - 1] ?? text
  try {
    return { value: JSON.parse(last) as JsonValue }
  } catch {
    // bare identifier / non-JSON
    if (last === 'true') return { value: true }
    if (last === 'false') return { value: false }
    if (last === 'null') return { value: null }
    const num = Number(last)
    if (last !== '' && !Number.isNaN(num) && /^-?\d+(\.\d+)?([eE][-+]?\d+)?$/.test(last)) {
      return { value: num }
    }
    return { value: last }
  }
}

function hasMainFunction(source: string): boolean {
  // Strip // and /* */ comments roughly, then look for main(
  const noBlock = source.replace(/\/\*[\s\S]*?\*\//g, ' ')
  const noLine = noBlock.replace(/\/\/.*$/gm, ' ')
  return /\bmain\s*\(/.test(noLine)
}

const COMPILE_FLAGS = [
  '-std=c++17',
  '-fno-exceptions',
  '-O0',
  '-Wno-unused-variable',
  '-Wno-unused-function',
  // Cap WASM linear memory so runaway malloc / recursion cannot grow forever.
  `-Wl,--max-memory=${MEMORY_LIMIT_BYTES}`,
]

/**
 * Run compiled WASM in a dedicated worker so a busy-loop can be aborted
 * with worker.terminate() without freezing the UI thread.
 */
async function runWasm(
  module: WebAssembly.Module,
  stdinText: string,
  runId: number,
  timeoutMs: number = RUN_TIMEOUT_MS,
): Promise<{ stdout: string; stderr: string }> {
  if (isCancelled(runId)) throw new Error(CANCELLED_MESSAGE)

  const worker = new Worker(
    new URL('./wasiRunner.worker.ts', import.meta.url),
    { type: 'module' },
  )
  activeWorkers.add(worker)

  return new Promise((resolve, reject) => {
    let settled = false
    const finish = (fn: () => void) => {
      if (settled) return
      settled = true
      window.clearTimeout(timer)
      activeWorkers.delete(worker)
      try {
        worker.terminate()
      } catch {
        /* ignore */
      }
      fn()
    }

    const timer = window.setTimeout(() => {
      finish(() => reject(new Error(TIMEOUT_MESSAGE)))
    }, timeoutMs)

    worker.onmessage = (ev: MessageEvent<WasRunResponse>) => {
      finish(() => {
        if (isCancelled(runId)) {
          reject(new Error(CANCELLED_MESSAGE))
          return
        }
        const data = ev.data
        if (!data.ok) {
          reject(new Error(classifyHostError(data.error || '运行失败')))
          return
        }
        resolve({ stdout: data.stdout, stderr: data.stderr })
      })
    }

    worker.onerror = (err) => {
      finish(() => {
        if (isCancelled(runId)) {
          reject(new Error(CANCELLED_MESSAGE))
          return
        }
        reject(
          new Error(
            classifyHostError(err.message || 'Worker 运行失败'),
          ),
        )
      })
    }

    try {
      const req: WasRunRequest = {
        module,
        stdin: stdinText,
        maxStdoutBytes: MAX_STDOUT_BYTES,
        memoryLimitBytes: MEMORY_LIMIT_BYTES,
      }
      worker.postMessage(req)
    } catch (e) {
      finish(() => {
        reject(e instanceof Error ? e : new Error(String(e)))
      })
    }
  })
}

export async function runProblem(
  problem: Problem,
  userCode: string,
): Promise<RunResult> {
  // New submit cancels any previous in-flight judge.
  cancelActiveRun()
  const runId = activeRunId

  const failCompile = (compileError: string): RunResult => ({
    ok: false,
    compileError,
    cases: [],
    passedCount: 0,
    totalCount: problem.tests.length,
  })

  if (!userCode.trim()) {
    return failCompile(EMPTY_SUBMIT_MESSAGE)
  }
  if (!hasMainFunction(userCode)) {
    return failCompile(MISSING_MAIN_MESSAGE)
  }

  let compile: CompileFn
  try {
    compile = await getCompile()
    if (isCancelled(runId)) return failCompile(CANCELLED_MESSAGE)
    toolchainReady = true
    await warmCompileOnce(compile)
    if (isCancelled(runId)) return failCompile(CANCELLED_MESSAGE)
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e)
    if (msg === TOOLCHAIN_TIMEOUT_MESSAGE || msg === COMPILE_TIMEOUT_MESSAGE) {
      return failCompile(msg)
    }
    return failCompile(`工具链加载失败：${msg}`)
  }

  // Compile the user's whole program as-is (must include main).
  let compiled: { compileOutput: string; module: WebAssembly.Module | null }
  try {
    compiled = await withTimeout(
      compile({
        source: userCode,
        fileName: 'solution.cpp',
        flags: COMPILE_FLAGS,
      }),
      COMPILE_TIMEOUT_MS,
      COMPILE_TIMEOUT_MESSAGE,
    )
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e)
    if (msg === COMPILE_TIMEOUT_MESSAGE) return failCompile(msg)
    return failCompile(`编译器异常：${msg}`)
  }

  if (isCancelled(runId)) return failCompile(CANCELLED_MESSAGE)

  if (!compiled.module) {
    const raw = compiled.compileOutput?.trim() || '编译失败（无详细输出）'
    return failCompile(truncateCompileOutput(raw))
  }

  const cases: CaseResult[] = []
  for (let index = 0; index < problem.tests.length; index++) {
    if (isCancelled(runId)) {
      return {
        ok: false,
        compileError: CANCELLED_MESSAGE,
        cases,
        passedCount: cases.filter((c) => c.passed).length,
        totalCount: problem.tests.length,
      }
    }

    const t = problem.tests[index]
    const stdin = formatStdin(problem, t.args)
    let stdout = ''
    let runError: string | undefined
    try {
      const result = await runWasm(compiled.module, stdin, runId)
      stdout = result.stdout
      if (!stdout.trim() && result.stderr.trim()) {
        runError = classifyHostError(result.stderr.trim())
      }
    } catch (e) {
      runError = classifyHostError(
        e instanceof Error ? e.message : String(e),
      )
    }

    if (runError === CANCELLED_MESSAGE || isCancelled(runId)) {
      return {
        ok: false,
        compileError: CANCELLED_MESSAGE,
        cases,
        passedCount: cases.filter((c) => c.passed).length,
        totalCount: problem.tests.length,
      }
    }

    const expected = t.expected
    let actual: JsonValue | undefined
    let error = runError
    if (!error) {
      const parsed = parseStdout(stdout)
      if (parsed.error) error = parsed.error
      else actual = parsed.value
    }

    const passed =
      !error && actual !== undefined && deepEq(expected, actual as JsonValue)
    const hint = passed
      ? undefined
      : t.hint || inferHint(expected, actual as JsonValue | undefined, error)
    cases.push({
      index,
      passed,
      sample: !!t.sample,
      inputLabel: t.inputLabel,
      expected,
      actual: actual as JsonValue | undefined,
      error,
      hint,
    })
  }

  const passedCount = cases.filter((c) => c.passed).length
  return {
    ok: passedCount === cases.length && cases.length > 0,
    cases,
    passedCount,
    totalCount: cases.length,
  }
}

export const PAGES_BUILD = '20261118T063000Z-judge-guards'
