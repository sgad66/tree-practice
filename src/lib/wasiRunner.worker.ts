/// <reference lib="webworker" />
import { WASI, File, OpenFile, ConsoleStdout } from '@bjorn3/browser_wasi_shim'

export type WasRunRequest = {
  /** Precompiled user module */
  module: WebAssembly.Module
  stdin: string
  /** Soft cap on captured stdout+stderr (bytes). */
  maxStdoutBytes: number
  /** Soft cap on linear memory (bytes); used for post-checks / messaging. */
  memoryLimitBytes: number
}

export type WasRunResponse =
  | { ok: true; stdout: string; stderr: string }
  | { ok: false; error: string }

export const MEMORY_EXCEEDED_MESSAGE = '内存超限'
export const STDOUT_EXCEEDED_MESSAGE = '输出超限（stdout 过大）'

const workerScope = self as DedicatedWorkerGlobalScope

function classifyRuntimeError(msg: string, stderr: string): string {
  const text = `${msg}\n${stderr}`
  if (
    /内存超限|out of memory|OutOfMemory|oom|unable to grow|failed to grow|memory\.grow|memory access out of bounds|table index|stack overflow|call stack|maximum memory|wasm memory/i.test(
      text,
    )
  ) {
    return MEMORY_EXCEEDED_MESSAGE
  }
  if (/输出超限/.test(text)) return STDOUT_EXCEEDED_MESSAGE
  return stderr.trim() || msg || '运行失败'
}

workerScope.onmessage = async (ev: MessageEvent<WasRunRequest>) => {
  const { module, stdin, maxStdoutBytes, memoryLimitBytes } = ev.data
  let stdout = ''
  let stderr = ''
  let stdoutBytes = 0
  let stderrBytes = 0
  let outputExceeded = false

  const append = (
    kind: 'stdout' | 'stderr',
    data: Uint8Array,
  ): void => {
    if (outputExceeded) return
    const chunk = new TextDecoder().decode(data)
    const n = data.byteLength
    if (kind === 'stdout') {
      stdoutBytes += n
      stdout += chunk
    } else {
      stderrBytes += n
      stderr += chunk
    }
    if (stdoutBytes + stderrBytes > maxStdoutBytes) {
      outputExceeded = true
      throw new Error(STDOUT_EXCEEDED_MESSAGE)
    }
  }

  try {
    const stdinBytes = new TextEncoder().encode(stdin)
    const fds = [
      new OpenFile(new File(stdinBytes)),
      new ConsoleStdout((data: Uint8Array) => append('stdout', data)),
      new ConsoleStdout((data: Uint8Array) => append('stderr', data)),
    ]
    const wasi = new WASI(['solution'], [], fds)
    const instance = await WebAssembly.instantiate(module, {
      wasi_snapshot_preview1: wasi.wasiImport,
    })

    const memory = (instance.exports as { memory?: WebAssembly.Memory }).memory
    if (memory && memory.buffer.byteLength > memoryLimitBytes) {
      const payload: WasRunResponse = {
        ok: false,
        error: MEMORY_EXCEEDED_MESSAGE,
      }
      workerScope.postMessage(payload)
      return
    }

    const memoryNearCap = (): boolean => {
      if (!memory) return false
      // Linker --max-memory may stop grow just at or slightly under the cap.
      return memory.buffer.byteLength >= Math.floor(memoryLimitBytes * 0.85)
    }

    let exitCode = 0
    try {
      // browser_wasi_shim returns the proc_exit code (does not throw on exit).
      exitCode = wasi.start(
        instance as unknown as Parameters<WASI['start']>[0],
      ) as unknown as number
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e)
      if (/输出超限/.test(msg)) {
        const payload: WasRunResponse = {
          ok: false,
          error: STDOUT_EXCEEDED_MESSAGE,
        }
        workerScope.postMessage(payload)
        return
      }
      if (!/exit|Exit|proc_exit/i.test(msg)) {
        const classified = classifyRuntimeError(msg, stderr)
        const payload: WasRunResponse = {
          ok: false,
          error: memoryNearCap() ? MEMORY_EXCEEDED_MESSAGE : classified,
        }
        workerScope.postMessage(payload)
        return
      }
      const exitMatch = /(?:exit|proc_exit)[^\d]*(\d+)/i.exec(msg)
      if (exitMatch) exitCode = Number(exitMatch[1])
    }

    if (exitCode !== 0) {
      const payload: WasRunResponse = {
        ok: false,
        error: memoryNearCap()
          ? MEMORY_EXCEEDED_MESSAGE
          : stderr.trim() || `程序异常退出（代码 ${exitCode}）`,
      }
      workerScope.postMessage(payload)
      return
    }

    if (memoryNearCap() && !stdout.trim()) {
      // Grew to the ceiling and produced no answer — treat as OOM.
      const payload: WasRunResponse = {
        ok: false,
        error: MEMORY_EXCEEDED_MESSAGE,
      }
      workerScope.postMessage(payload)
      return
    }

    if (memory && memory.buffer.byteLength > memoryLimitBytes) {
      const payload: WasRunResponse = {
        ok: false,
        error: MEMORY_EXCEEDED_MESSAGE,
      }
      workerScope.postMessage(payload)
      return
    }

    if (outputExceeded) {
      const payload: WasRunResponse = {
        ok: false,
        error: STDOUT_EXCEEDED_MESSAGE,
      }
      workerScope.postMessage(payload)
      return
    }

    const payload: WasRunResponse = { ok: true, stdout, stderr }
    workerScope.postMessage(payload)
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e)
    const payload: WasRunResponse = {
      ok: false,
      error: classifyRuntimeError(msg, stderr),
    }
    workerScope.postMessage(payload)
  }
}
