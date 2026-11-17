import puppeteer from 'puppeteer-core'

const BASE = process.env.APP_URL || 'http://127.0.0.1:5173'

const CASES = [
  {
    label: 'basics/max-depth',
    openTitle: '二叉树的最大深度',
    bad: `from typing import Optional\n\ndef maxDepth(root: Optional[TreeNode]) -> int:\n    if not root:\n        return 0\n    return max(maxDepth(root.left), maxDepth(root.right))  # missing +1\n`,
    good: `from typing import Optional\n\ndef maxDepth(root: Optional[TreeNode]) -> int:\n    if not root:\n        return 0\n    return 1 + max(maxDepth(root.left), maxDepth(root.right))\n`,
  },
  {
    label: 'bst/validate-bst',
    openTitle: '验证二叉搜索树',
    bad: `from typing import Optional\n\ndef isValidBST(root: Optional[TreeNode]) -> bool:\n    if not root:\n        return True\n    if root.left and root.left.val >= root.val: return False\n    if root.right and root.right.val <= root.val: return False\n    return isValidBST(root.left) and isValidBST(root.right)\n`,
    good: `from typing import Optional\n\ndef isValidBST(root: Optional[TreeNode]) -> bool:\n    def ok(n, lo, hi):\n        if not n: return True\n        if n.val <= lo or n.val >= hi: return False\n        return ok(n.left, lo, n.val) and ok(n.right, n.val, hi)\n    return ok(root, float('-inf'), float('inf'))\n`,
  },
  {
    label: 'levelview/level-order',
    openTitle: '二叉树的层序遍历',
    bad: `from typing import Optional, List\n\ndef levelOrder(root: Optional[TreeNode]) -> List[List[int]]:\n    if not root: return []\n    # wrong: flat list wrapped once\n    from collections import deque\n    q=deque([root]); out=[]\n    while q:\n        n=q.popleft(); out.append(n.val)\n        if n.left: q.append(n.left)\n        if n.right: q.append(n.right)\n    return [out]\n`,
    good: `from typing import Optional, List\nfrom collections import deque\n\ndef levelOrder(root: Optional[TreeNode]) -> List[List[int]]:\n    if not root: return []\n    res=[]; q=deque([root])\n    while q:\n        lv=[]\n        for _ in range(len(q)):\n            n=q.popleft(); lv.append(n.val)\n            if n.left: q.append(n.left)\n            if n.right: q.append(n.right)\n        res.append(lv)\n    return res\n`,
  },
]

const browser = await puppeteer.launch({
  executablePath: '/usr/bin/google-chrome-stable',
  headless: true,
  args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'],
})
const page = await browser.newPage()
page.setDefaultTimeout(180000)
await page.goto(BASE, { waitUntil: 'networkidle2' })

const landingText = await page.evaluate(() => document.body.innerText)
if (!landingText.includes('100 题') && !/100/.test(landingText)) {
  console.error('Landing does not show 100 problems:', landingText.slice(0, 400))
  process.exitCode = 1
} else {
  console.log('landing shows 100')
}

await page.click('button.btn--primary')
await page.waitForFunction(
  () => document.body.innerText.includes('Pyodide 就绪'),
  { timeout: 180000 },
)
await page.waitForFunction(() => window.__treePractice, { timeout: 30000 })

const sidebarCount = await page.evaluate(() => {
  return document.querySelectorAll('.problem-link').length
})
console.log('sidebar problem links', sidebarCount)
if (sidebarCount !== 100) {
  console.error('Expected 100 problem links')
  process.exitCode = 1
}

async function openByTitle(title) {
  const ok = await page.evaluate((t) => {
    const btns = Array.from(document.querySelectorAll('.problem-link'))
    const b = btns.find((x) => x.textContent?.includes(t))
    if (!b) return false
    b.click()
    return true
  }, title)
  if (!ok) throw new Error('cannot open ' + title)
  await page.waitForFunction(
    (t) => document.querySelector('.statement h1')?.textContent?.includes(t),
    { timeout: 10000 },
    title,
  )
}

for (const c of CASES) {
  await openByTitle(c.openTitle)
  await page.evaluate(async (src) => {
    await window.__treePractice.submit(src)
  }, c.bad)
  let result = await page.evaluate(() => window.__treePractice.getResult())
  console.log(c.label, 'bad', {
    ok: result?.ok,
    passed: result?.passedCount,
    total: result?.totalCount,
    actual0: result?.cases?.[0]?.actual,
    hint0: result?.cases?.[0]?.hint,
  })
  if (result?.ok) {
    console.error(c.label, 'bad solution unexpectedly passed')
    process.exitCode = 1
  }
  if (result?.cases?.some((x) => !x.passed && x.actual === undefined && !x.error)) {
    console.error(c.label, 'missing actual on failure')
    process.exitCode = 1
  }

  await page.evaluate(async (src) => {
    await window.__treePractice.submit(src)
  }, c.good)
  result = await page.evaluate(() => window.__treePractice.getResult())
  console.log(c.label, 'good', { ok: result?.ok, passed: result?.passedCount })
  if (!result?.ok) {
    console.error(c.label, 'good failed', JSON.stringify(result, null, 2).slice(0, 800))
    process.exitCode = 1
  }
}

await browser.close()
console.log(process.exitCode ? 'SMOKE FAIL' : 'SMOKE OK')
