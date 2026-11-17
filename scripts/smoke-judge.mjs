import puppeteer from 'puppeteer-core'

const BASE = process.env.APP_URL || 'http://127.0.0.1:5173'

const BAD = `from typing import Optional, List

def preorderTraversal(root: Optional[TreeNode]) -> List[int]:
    if not root:
        return []
    return preorderTraversal(root.left) + [root.val] + preorderTraversal(root.right)
`

const GOOD = `from typing import Optional, List

def preorderTraversal(root: Optional[TreeNode]) -> List[int]:
    if not root:
        return []
    return [root.val] + preorderTraversal(root.left) + preorderTraversal(root.right)
`

const browser = await puppeteer.launch({
  executablePath: '/usr/bin/google-chrome-stable',
  headless: true,
  args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'],
})
const page = await browser.newPage()
page.setDefaultTimeout(180000)
await page.goto(BASE, { waitUntil: 'networkidle2' })
await page.click('button.btn--primary')
await page.waitForFunction(
  () => document.body.innerText.includes('Pyodide 就绪'),
  { timeout: 180000 },
)
await page.waitForFunction(() => window.__treePractice, { timeout: 30000 })
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
if (badActual == null) {
  console.error('FAIL: first bad case actual is null/undefined', badActual)
  process.exitCode = 1
} else if (JSON.stringify(badActual) === JSON.stringify([1, 2, 3])) {
  console.error('FAIL: bad solution unexpectedly matched expected')
  process.exitCode = 1
} else {
  console.log('bad actual ok:', badActual)
}

if (!good?.ok) {
  console.error('FAIL: good solution did not pass')
  process.exitCode = 1
} else {
  console.log('good ok')
}

await browser.close()
