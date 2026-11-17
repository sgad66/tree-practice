import puppeteer from 'puppeteer-core'

const BASE = process.env.APP_URL || 'http://127.0.0.1:5173'

const BAD = `#include <stdlib.h>

static void bad_walk(struct TreeNode* node, int* out, int* n, int cap) {
    if (!node) return;
    bad_walk(node->left, out, n, cap);
    if (*n < cap) out[(*n)++] = node->val;
    bad_walk(node->right, out, n, cap);
}

int* preorderTraversal(struct TreeNode* root, int* returnSize) {
    int cap = 128;
    int* out = (int*)malloc(sizeof(int) * (size_t)cap);
    int n = 0;
    bad_walk(root, out, &n, cap);
    *returnSize = n;
    return out;
}
`

const GOOD = `#include <stdlib.h>

static void good_walk(struct TreeNode* node, int* out, int* n, int cap) {
    if (!node) return;
    if (*n >= cap) return;
    out[(*n)++] = node->val;
    good_walk(node->left, out, n, cap);
    good_walk(node->right, out, n, cap);
}

int* preorderTraversal(struct TreeNode* root, int* returnSize) {
    int cap = 128;
    int* out = (int*)malloc(sizeof(int) * (size_t)cap);
    int n = 0;
    good_walk(root, out, &n, cap);
    *returnSize = n;
    return out;
}
`

const browser = await puppeteer.launch({
  executablePath: '/usr/bin/google-chrome-stable',
  headless: true,
  protocolTimeout: 600000,
  args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'],
})
const page = await browser.newPage()
await page.setViewport({ width: 1400, height: 900 })
page.setDefaultTimeout(600000)
page.on('console', (msg) => console.log('browser:', msg.type(), msg.text()))
page.on('pageerror', (err) => console.log('pageerror:', err.message))
await page.goto(BASE, { waitUntil: 'networkidle2' })

const landing = await page.evaluate(() => document.body.innerText)
if (!/C\s*语言|写 C|C语言/.test(landing)) {
  console.warn('Landing may not mention C:', landing.slice(0, 300))
}

await page.click('button.btn--primary')
await page.waitForFunction(
  () => document.body.innerText.includes('C 工具链就绪'),
  { timeout: 300000 },
)
await page.waitForFunction(() => window.__treePractice, { timeout: 30000 })

const layout = await page.evaluate(() => {
  const practice = document.querySelector('.practice')
  const editor = document.querySelector('.cm-wrapper')
  const ws = document.querySelector('.workspace')
  if (!practice || !editor || !ws) return null
  const pr = practice.getBoundingClientRect()
  const er = editor.getBoundingClientRect()
  return {
    practiceH: pr.height,
    viewportH: window.innerHeight,
    editorH: er.height,
    toolbar: document.querySelector('.editor-toolbar__lang')?.textContent || '',
  }
})
console.log('layout', layout)
if (!layout || layout.editorH < 160) {
  console.error('FAIL: editor too small / layout missing', layout)
  process.exitCode = 1
}
if (!layout?.toolbar.includes('C')) {
  console.error('FAIL: toolbar not C', layout?.toolbar)
  process.exitCode = 1
}
if (Math.abs(layout.practiceH - layout.viewportH) > 12) {
  console.error('FAIL: practice not filling viewport', layout.practiceH, layout.viewportH)
  process.exitCode = 1
}

console.log('ready')

async function run(code, label) {
  await page.evaluate(async (src) => {
    await window.__treePractice.submit(src)
  }, code)
  const result = await page.evaluate(() => window.__treePractice.getResult())
  const text = await page.evaluate(() => document.querySelector('.results')?.innerText || '')
  console.log(`=== ${label} ===`)
  console.log(JSON.stringify(result, null, 2))
  console.log(text)
  return result
}

const bad = await run(BAD, 'BAD')
const good = await run(GOOD, 'GOOD')

const badActual = bad?.cases?.[0]?.actual
if (bad?.compileError) {
  console.error('FAIL: bad solution failed to compile', bad.compileError)
  process.exitCode = 1
} else if (badActual == null) {
  console.error('FAIL: first bad case actual is null/undefined', badActual)
  process.exitCode = 1
} else if (JSON.stringify(badActual) === JSON.stringify([1, 2, 3])) {
  console.error('FAIL: bad solution unexpectedly matched expected')
  process.exitCode = 1
} else {
  console.log('bad actual ok:', badActual)
}

if (!good?.ok) {
  console.error('FAIL: good solution did not pass', good)
  process.exitCode = 1
} else {
  console.log('good ok')
}

await browser.close()
