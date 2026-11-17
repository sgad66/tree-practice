import type {
  CAbi,
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

function looksLikeTreeArr(a: JsonValue): a is (number | null)[] {
  return (
    Array.isArray(a) &&
    (a.length === 0 ||
      a.every((x) => x === null || typeof x === 'number'))
  )
}

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
  // Prefetch sysroot/clang via a tiny compile; ignore failure (surfaced on real submit).
  try {
    await compile({
      source: '#include <stdio.h>\nint main(void){puts("ok");return 0;}\n',
      fileName: 'warm.cpp',
      // browsercc drives clang++; C-looking solutions are accepted as C++17.
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
      // Kick off asset download in background without blocking UI ready state.
      void warmCompileOnce(compile)
    })
    .catch(() => {
      /* surfaced on first submit / ready banner */
    })
}

export function isToolchainReady(): boolean {
  return toolchainReady
}

function cEscape(s: string): string {
  return JSON.stringify(s)
}

function emitIntArray(name: string, arr: number[]): string {
  if (arr.length === 0) {
    return `int* ${name} = NULL; int ${name}_len = 0;\n`
  }
  return `int ${name}_data[] = {${arr.join(', ')}}; int ${name}_len = ${arr.length}; int* ${name} = ${name}_data;\n`
}

function emitTreeArray(name: string, arr: (number | null)[]): string {
  if (arr.length === 0) {
    return `int* ${name}_vals = NULL; int* ${name}_nulls = NULL; int ${name}_len = 0;\n`
  }
  const vals = arr.map((v) => (v === null ? 0 : v)).join(', ')
  const nulls = arr.map((v) => (v === null ? 1 : 0)).join(', ')
  return (
    `int ${name}_vals_data[] = {${vals}}; int ${name}_nulls_data[] = {${nulls}}; ` +
    `int ${name}_len = ${arr.length}; int* ${name}_vals = ${name}_vals_data; int* ${name}_nulls = ${name}_nulls_data;\n`
  )
}

function emitIntMatrix(name: string, matrix: number[][]): string {
  if (matrix.length === 0) {
    return `int** ${name} = NULL; int ${name}_rows = 0; int* ${name}_cols = NULL;\n`
  }
  const lines: string[] = []
  const rowPtrs: string[] = []
  matrix.forEach((row, i) => {
    if (row.length === 0) {
      lines.push(`int* ${name}_r${i} = NULL;`)
    } else {
      lines.push(`int ${name}_r${i}_data[] = {${row.join(', ')}}; int* ${name}_r${i} = ${name}_r${i}_data;`)
    }
    rowPtrs.push(`${name}_r${i}`)
  })
  lines.push(`int* ${name}_rows_data[] = {${rowPtrs.join(', ')}};`)
  lines.push(`int ${name}_cols_data[] = {${matrix.map((r) => r.length).join(', ')}};`)
  lines.push(
    `int** ${name} = ${name}_rows_data; int ${name}_rows = ${matrix.length}; int* ${name}_cols = ${name}_cols_data;`,
  )
  return lines.join('\n') + '\n'
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

function emitArgSetup(
  prefix: string,
  kind: CParamKind,
  arg: JsonValue,
): { decls: string; exprParts: string[] } {
  switch (kind) {
    case 'tree': {
      const arr = looksLikeTreeArr(arg) ? arg : []
      return {
        decls: emitTreeArray(prefix, arr),
        exprParts: [`tp_build_tree(${prefix}_vals, ${prefix}_nulls, ${prefix}_len)`],
      }
    }
    case 'int':
      return { decls: '', exprParts: [String(arg as number)] }
    case 'float':
      return { decls: '', exprParts: [String(arg as number)] }
    case 'bool':
      return { decls: '', exprParts: [(arg as boolean) ? 'true' : 'false'] }
    case 'string':
      return {
        decls: `char* ${prefix}_str = ${cEscape(String(arg))};\n`,
        exprParts: [`${prefix}_str`],
      }
    case 'int_array': {
      const arr = Array.isArray(arg)
        ? (arg as JsonValue[]).map((x) => Number(x))
        : []
      return {
        decls: emitIntArray(prefix, arr),
        exprParts: [prefix, `${prefix}_len`],
      }
    }
    case 'double_array': {
      const arr = Array.isArray(arg)
        ? (arg as JsonValue[]).map((x) => Number(x))
        : []
      if (arr.length === 0) {
        return {
          decls: `double* ${prefix} = NULL; int ${prefix}_len = 0;\n`,
          exprParts: [prefix, `${prefix}_len`],
        }
      }
      return {
        decls: `double ${prefix}_data[] = {${arr.join(', ')}}; int ${prefix}_len = ${arr.length}; double* ${prefix} = ${prefix}_data;\n`,
        exprParts: [prefix, `${prefix}_len`],
      }
    }
    case 'int_matrix': {
      const matrix = Array.isArray(arg)
        ? (arg as JsonValue[]).map((row) =>
            Array.isArray(row) ? row.map((x) => Number(x)) : [],
          )
        : []
      return {
        decls: emitIntMatrix(prefix, matrix),
        exprParts: [prefix, `${prefix}_rows`, `${prefix}_cols`],
      }
    }
    default:
      return { decls: '', exprParts: ['0'] }
  }
}

function buildCallAndCapture(
  problem: Problem,
  abi: CAbi,
  callArgs: string[],
  caseIdx: number,
): string {
  const fn = problem.functionName
  const mode = problem.judgeMode ?? 'value'
  const rk = abi.returnKind
  const lines: string[] = []

  if (mode === 'serialize') {
    lines.push(`struct TreeNode* _root = ${callArgs[0] ?? 'NULL'};`)
    lines.push(`char* _ser = serialize(_root);`)
    lines.push(`struct TreeNode* _back = deserialize(_ser);`)
    lines.push(`tp_print_tree_list(_back);`)
    return lines.join('\n')
  }

  if (mode === 'lca') {
    // args: tree, pVal, qVal — callArgs already has tree; p/q are ints in abi as tree nodes
    lines.push(`struct TreeNode* _root = ${callArgs[0] ?? 'NULL'};`)
    lines.push(`int _p = ${callArgs[1] ?? '0'};`)
    lines.push(`int _q = ${callArgs[2] ?? '0'};`)
    lines.push(`struct TreeNode* _pn = tp_find_node(_root, _p);`)
    lines.push(`struct TreeNode* _qn = tp_find_node(_root, _q);`)
    lines.push(`struct TreeNode* _res = ${fn}(_root, _pn, _qn);`)
    lines.push(`if (_res) printf("%d", _res->val); else printf("null");`)
    return lines.join('\n')
  }

  const argsJoined = callArgs.join(', ')

  if (mode === 'tree_return' || mode === 'trees_return' || mode === 'raw_tree_return' || rk === 'tree') {
    lines.push(`struct TreeNode* _res = ${fn}(${argsJoined});`)
    lines.push(`tp_print_tree_list(_res);`)
    return lines.join('\n')
  }

  if (rk === 'int') {
    lines.push(`int _res = ${fn}(${argsJoined});`)
    lines.push(`printf("%d", _res);`)
    return lines.join('\n')
  }
  if (rk === 'bool') {
    lines.push(`bool _res = ${fn}(${argsJoined});`)
    lines.push(`printf(_res ? "true" : "false");`)
    return lines.join('\n')
  }
  if (rk === 'float') {
    lines.push(`double _res = ${fn}(${argsJoined});`)
    lines.push(`printf("%.10g", _res);`)
    return lines.join('\n')
  }
  if (rk === 'string') {
    lines.push(`char* _res = ${fn}(${argsJoined});`)
    lines.push(`tp_print_string(_res);`)
    return lines.join('\n')
  }
  if (rk === 'optional_int') {
    lines.push(`int* _res = ${fn}(${argsJoined});`)
    lines.push(`if (_res) printf("%d", *_res); else printf("null");`)
    return lines.join('\n')
  }
  if (rk === 'int_array') {
    lines.push(`int _rs = 0;`)
    lines.push(`int* _res = ${fn}(${argsJoined}, &_rs);`)
    lines.push(`tp_print_int_array(_res, _rs);`)
    return lines.join('\n')
  }
  if (rk === 'double_array') {
    lines.push(`int _rs = 0;`)
    lines.push(`double* _res = ${fn}(${argsJoined}, &_rs);`)
    lines.push(`tp_print_double_array(_res, _rs);`)
    return lines.join('\n')
  }
  if (rk === 'string_array') {
    lines.push(`int _rs = 0;`)
    lines.push(`char** _res = ${fn}(${argsJoined}, &_rs);`)
    lines.push(`tp_print_string_array(_res, _rs);`)
    return lines.join('\n')
  }
  if (rk === 'int_matrix') {
    lines.push(`int _rs = 0; int* _cols = NULL;`)
    lines.push(`int** _res = ${fn}(${argsJoined}, &_rs, &_cols);`)
    lines.push(`tp_print_int_matrix(_res, _rs, _cols);`)
    return lines.join('\n')
  }
  if (rk === 'string_matrix') {
    lines.push(`int _rs = 0; int* _cols = NULL;`)
    lines.push(`char*** _res = ${fn}(${argsJoined}, &_rs, &_cols);`)
    lines.push(`tp_print_string_matrix(_res, _rs, _cols);`)
    return lines.join('\n')
  }

  lines.push(`/* unsupported return kind for case ${caseIdx} */`)
  lines.push(`printf("null");`)
  return lines.join('\n')
}

function buildJudgeSource(problem: Problem, userCode: string): string {
  const mode = problem.judgeMode ?? 'value'
  const abi = problem.cAbi
  const unifiedCases: string[] = []

  problem.tests.forEach((t, idx) => {
    const decls: string[] = []
    let callArgExprs: string[] = []

    if (mode === 'lca') {
      // Tests pass (treeArr, pVal, qVal); solution takes (root, pNode, qNode).
      const treeSetup = emitArgSetup(`t${idx}_a0`, 'tree', t.args[0] ?? [])
      decls.push(treeSetup.decls)
      callArgExprs = [
        treeSetup.exprParts[0],
        String(t.args[1]),
        String(t.args[2]),
      ]
    } else {
      const paramKinds = abi.params.map((p) => p.kind)
      t.args.forEach((arg, ai) => {
        const kind = prepareArgKind(mode, ai, arg, paramKinds[ai])
        const setup = emitArgSetup(`t${idx}_a${ai}`, kind, arg)
        decls.push(setup.decls)
        callArgExprs.push(...setup.exprParts)
      })
    }

    const capture = buildCallAndCapture(problem, abi, callArgExprs, idx)
    // Escape carefully: C++ string literals need \" for quotes inside.
    unifiedCases.push(
      `fputs(${idx === 0 ? '"["' : '","'}, stdout);\n` +
        `fputs("{\\"index\\":${idx},\\"actual\\":", stdout);\n` +
        `{\n${decls.join('')}${capture}\n}\n` +
        `fputs("}", stdout);\n`,
    )
  })

  const harnessExtras = problem.harnessExtras ?? ''

  return `/* TreePath in-browser C judge harness — generated */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <math.h>
#include <limits.h>
#include <stdint.h>

struct TreeNode {
  int val;
  struct TreeNode *left;
  struct TreeNode *right;
};

static struct TreeNode* tp_new(int v) {
  struct TreeNode* n = (struct TreeNode*)malloc(sizeof(struct TreeNode));
  n->val = v; n->left = NULL; n->right = NULL;
  return n;
}

static struct TreeNode* tp_build_tree(int* vals, int* nulls, int len) {
  if (len <= 0) return NULL;
  struct TreeNode** nodes = (struct TreeNode**)calloc((size_t)len, sizeof(struct TreeNode*));
  for (int i = 0; i < len; i++) {
    if (nulls && nulls[i]) nodes[i] = NULL;
    else nodes[i] = tp_new(vals[i]);
  }
  int kids = 1;
  for (int i = 0; i < len; i++) {
    if (!nodes[i]) continue;
    if (kids < len) { nodes[i]->left = nodes[kids]; kids++; }
    if (kids < len) { nodes[i]->right = nodes[kids]; kids++; }
  }
  struct TreeNode* root = nodes[0];
  free(nodes);
  return root;
}

static struct TreeNode* tp_find_node(struct TreeNode* root, int val) {
  if (!root) return NULL;
  if (root->val == val) return root;
  struct TreeNode* L = tp_find_node(root->left, val);
  if (L) return L;
  return tp_find_node(root->right, val);
}

static void tp_print_string(const char* s) {
  if (!s) { printf("null"); return; }
  putchar('"');
  for (const unsigned char* p = (const unsigned char*)s; *p; p++) {
    unsigned char c = *p;
    if (c == '"' || c == '\\\\') { putchar('\\\\'); putchar((char)c); }
    else if (c == '\\n') { putchar('\\\\'); putchar('n'); }
    else if (c == '\\r') { putchar('\\\\'); putchar('r'); }
    else if (c == '\\t') { putchar('\\\\'); putchar('t'); }
    else if (c < 0x20) printf("\\\\u%04x", c);
    else putchar((char)c);
  }
  putchar('"');
}

static void tp_print_int_array(int* a, int n) {
  putchar('[');
  for (int i = 0; i < n; i++) {
    if (i) putchar(',');
    printf("%d", a[i]);
  }
  putchar(']');
}

static void tp_print_double_array(double* a, int n) {
  putchar('[');
  for (int i = 0; i < n; i++) {
    if (i) putchar(',');
    printf("%.10g", a[i]);
  }
  putchar(']');
}

static void tp_print_string_array(char** a, int n) {
  putchar('[');
  for (int i = 0; i < n; i++) {
    if (i) putchar(',');
    tp_print_string(a ? a[i] : NULL);
  }
  putchar(']');
}

static void tp_print_int_matrix(int** a, int rows, int* cols) {
  putchar('[');
  for (int i = 0; i < rows; i++) {
    if (i) putchar(',');
    tp_print_int_array(a ? a[i] : NULL, cols ? cols[i] : 0);
  }
  putchar(']');
}

static void tp_print_string_matrix(char*** a, int rows, int* cols) {
  putchar('[');
  for (int r = 0; r < rows; r++) {
    if (r) putchar(',');
    putchar('[');
    int cmax = cols ? cols[r] : 0;
    for (int c = 0; c < cmax; c++) {
      if (c) putchar(',');
      tp_print_string(a && a[r] ? a[r][c] : NULL);
    }
    putchar(']');
  }
  putchar(']');
}

static void tp_print_tree_list(struct TreeNode* root) {
  if (!root) { printf("[]"); return; }
  struct TreeNode** q = (struct TreeNode**)malloc(sizeof(struct TreeNode*) * 4096);
  int* out_vals = (int*)malloc(sizeof(int) * 4096);
  int* out_null = (int*)malloc(sizeof(int) * 4096);
  int qh = 0, qt = 0, on = 0;
  q[qt++] = root;
  while (qh < qt) {
    struct TreeNode* n = q[qh++];
    if (!n) {
      out_vals[on] = 0; out_null[on] = 1; on++;
    } else {
      out_vals[on] = n->val; out_null[on] = 0; on++;
      if (qt < 4095) q[qt++] = n->left;
      if (qt < 4095) q[qt++] = n->right;
    }
  }
  while (on > 0 && out_null[on - 1]) on--;
  putchar('[');
  for (int i = 0; i < on; i++) {
    if (i) putchar(',');
    if (out_null[i]) printf("null");
    else printf("%d", out_vals[i]);
  }
  putchar(']');
  free(q); free(out_vals); free(out_null);
}

${harnessExtras}

/* ===== user solution ===== */
${userCode}
/* ===== end user solution ===== */

int main(void) {
  fputs("{\\"cases\\":", stdout);
${unifiedCases.join('\n')}
  fputs("]}\\n", stdout);
  return 0;
}
`
}

function deepEq(a: JsonValue, b: JsonValue): boolean {
  if (typeof a === 'number' && typeof b === 'number') {
    if (Number.isNaN(a) && Number.isNaN(b)) return true
    return Math.abs(a - b) < 1e-6
  }
  return JSON.stringify(a) === JSON.stringify(b)
}

async function runWasm(module: WebAssembly.Module): Promise<string> {
  let stdout = ''
  let stderr = ''
  const fds = [
    new OpenFile(new File(new Uint8Array())),
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
    // browser_wasi_shim typings expect a narrower Instance shape than WebAssembly.Instance
    wasi.start(instance as unknown as Parameters<WASI['start']>[0])
  } catch (e) {
    // WASI proc_exit throws on some shims; ignore clean exits
    const msg = e instanceof Error ? e.message : String(e)
    if (!/exit|Exit|proc_exit/i.test(msg) && stderr) {
      throw new Error(stderr || msg)
    }
  }
  if (!stdout.trim() && stderr.trim()) {
    throw new Error(stderr)
  }
  return stdout
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

  const source = buildJudgeSource(problem, userCode)
  let compiled: { compileOutput: string; module: WebAssembly.Module | null }
  try {
    compiled = await compile({
      source,
      // clang++ driver (browsercc): keep C-style API, compile as C++17.
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

  let stdout: string
  try {
    stdout = await runWasm(compiled.module)
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e)
    return {
      ok: false,
      compileError: `运行失败：${msg}`,
      cases: [],
      passedCount: 0,
      totalCount: problem.tests.length,
    }
  }

  let parsed: { cases: Array<{ index: number; actual?: JsonValue; error?: string }> }
  try {
    // Find last JSON object in stdout
    const start = stdout.indexOf('{')
    const end = stdout.lastIndexOf('}')
    if (start < 0 || end < start) throw new Error('no json')
    parsed = JSON.parse(stdout.slice(start, end + 1)) as typeof parsed
  } catch {
    return {
      ok: false,
      compileError: `判题输出解析失败：${stdout.slice(0, 400)}`,
      cases: [],
      passedCount: 0,
      totalCount: problem.tests.length,
    }
  }

  const byIndex = new Map(parsed.cases.map((c) => [c.index, c]))
  const cases: CaseResult[] = problem.tests.map((t, index) => {
    const got = byIndex.get(index)
    const actual = got?.actual
    const error = got?.error
    const passed =
      !error && actual !== undefined && deepEq(t.expected, actual as JsonValue)
    const hint = passed
      ? undefined
      : t.hint || inferHint(t.expected, actual as JsonValue | undefined, error)
    return {
      index,
      passed,
      sample: !!t.sample,
      inputLabel: t.inputLabel,
      expected: t.expected,
      actual: actual as JsonValue | undefined,
      error,
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

export const PAGES_BUILD = '20261117T172249Z'
