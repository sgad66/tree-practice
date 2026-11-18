import type {
  CParamKind,
  JsonValue,
  Problem,
  RunResult,
  CaseResult,
} from '../types'
import { inferHint } from './hints'
import { WASI, File, OpenFile, ConsoleStdout } from '@bjorn3/browser_wasi_shim'

type CompileFn = (job: {
  source: string
  fileName: string
  flags: string[]
}) => Promise<{ compileOutput: string; module: WebAssembly.Module | null }>

const BROWSERCC_CDN =
  'https://cdn.jsdelivr.net/npm/browsercc@0.1.1/dist/index.js'

let compilePromise: Promise<CompileFn> | null = null
let toolchainReady = false
let warmed = false

async function getCompile(): Promise<CompileFn> {
  if (!compilePromise) {
    compilePromise = (async () => {
      const mod = (await import(
        /* @vite-ignore */ BROWSERCC_CDN
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
    await compile({
      source: '#include <stdio.h>\nint main(void){puts("ok");return 0;}\n',
      fileName: 'warm.cpp',
      flags: ['-std=c++17', '-fno-exceptions', '-O0'],
    })
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

async function runWasm(
  module: WebAssembly.Module,
  stdinText: string,
): Promise<{ stdout: string; stderr: string }> {
  let stdout = ''
  let stderr = ''
  const stdinBytes = new TextEncoder().encode(stdinText)
  const fds = [
    new OpenFile(new File(stdinBytes)),
    new ConsoleStdout((data: Uint8Array) => {
      stdout += new TextDecoder().decode(data)
    }),
    new ConsoleStdout((data: Uint8Array) => {
      stderr += new TextDecoder().decode(data)
    }),
  ]
  const wasi = new WASI(['solution'], [], fds)
  const instance = await WebAssembly.instantiate(module, {
    wasi_snapshot_preview1: wasi.wasiImport,
  })
  try {
    wasi.start(instance as unknown as Parameters<WASI['start']>[0])
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e)
    if (!/exit|Exit|proc_exit/i.test(msg) && stderr) {
      throw new Error(stderr || msg)
    }
    if (!/exit|Exit|proc_exit/i.test(msg) && !stdout.trim()) {
      throw new Error(stderr || msg)
    }
  }
  return { stdout, stderr }
}

export async function runProblem(
  problem: Problem,
  userCode: string,
): Promise<RunResult> {
  let compile: CompileFn
  try {
    compile = await getCompile()
    toolchainReady = true
    await warmCompileOnce(compile)
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e)
    return {
      ok: false,
      compileError: `工具链加载失败：${msg}`,
      cases: [],
      passedCount: 0,
      totalCount: problem.tests.length,
    }
  }

  // Compile the user's whole program as-is (must include main).
  let compiled: { compileOutput: string; module: WebAssembly.Module | null }
  try {
    compiled = await compile({
      source: userCode,
      fileName: 'solution.cpp',
      flags: [
        '-std=c++17',
        '-fno-exceptions',
        '-O0',
        '-Wno-unused-variable',
        '-Wno-unused-function',
      ],
    })
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e)
    return {
      ok: false,
      compileError: `编译器异常：${msg}`,
      cases: [],
      passedCount: 0,
      totalCount: problem.tests.length,
    }
  }

  if (!compiled.module) {
    return {
      ok: false,
      compileError: compiled.compileOutput?.trim() || '编译失败（无详细输出）',
      cases: [],
      passedCount: 0,
      totalCount: problem.tests.length,
    }
  }

  const cases: CaseResult[] = []
  for (let index = 0; index < problem.tests.length; index++) {
    const t = problem.tests[index]
    const stdin = formatStdin(problem, t.args)
    let stdout = ''
    let runError: string | undefined
    try {
      const result = await runWasm(compiled.module, stdin)
      stdout = result.stdout
      if (!stdout.trim() && result.stderr.trim()) {
        runError = result.stderr.trim()
      }
    } catch (e) {
      runError = e instanceof Error ? e.message : String(e)
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

export const PAGES_BUILD = '20261118T060000Z-empty-editor'
