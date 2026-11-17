import puppeteer from 'puppeteer-core'

const BASE = process.env.APP_URL || 'http://127.0.0.1:5173'

const CASES = [
  {
    label: 'basics/max-depth',
    openTitle: '二叉树的最大深度',
    bad: `int maxDepth(struct TreeNode* root) {
    if (!root) return 0;
    int l = maxDepth(root->left), r = maxDepth(root->right);
    return l > r ? l : r; /* missing +1 */
}
`,
    good: `int maxDepth(struct TreeNode* root) {
    if (!root) return 0;
    int l = maxDepth(root->left), r = maxDepth(root->right);
    return 1 + (l > r ? l : r);
}
`,
  },
  {
    label: 'bst/validate-bst',
    openTitle: '验证二叉搜索树',
    bad: `#include <stdbool.h>
bool isValidBST(struct TreeNode* root) {
    if (!root) return true;
    if (root->left && root->left->val >= root->val) return false;
    if (root->right && root->right->val <= root->val) return false;
    return isValidBST(root->left) && isValidBST(root->right);
}
`,
    good: `#include <stdbool.h>
#include <limits.h>
static bool ok(struct TreeNode* n, long lo, long hi) {
    if (!n) return true;
    if (n->val <= lo || n->val >= hi) return false;
    return ok(n->left, lo, n->val) && ok(n->right, n->val, hi);
}
bool isValidBST(struct TreeNode* root) {
    return ok(root, LONG_MIN, LONG_MAX);
}
`,
  },
  {
    label: 'levelview/level-order',
    openTitle: '二叉树的层序遍历',
    bad: `int** levelOrder(struct TreeNode* root, int* returnSize, int** returnColumnSizes) {
    *returnSize = 0;
    if (!root) return NULL;
    int* row = (int*)malloc(sizeof(int));
    row[0] = root->val;
    int** out = (int**)malloc(sizeof(int*));
    out[0] = row;
    int* cols = (int*)malloc(sizeof(int));
    cols[0] = 1;
    *returnColumnSizes = cols;
    *returnSize = 1;
    return out; /* incomplete BFS */
}
`,
    good: `int** levelOrder(struct TreeNode* root, int* returnSize, int** returnColumnSizes) {
    *returnSize = 0;
    if (!root) return NULL;
    struct TreeNode* q[256];
    int qh = 0, qt = 0;
    q[qt++] = root;
    int** res = (int**)malloc(sizeof(int*) * 64);
    int* cols = (int*)malloc(sizeof(int) * 64);
    int rows = 0;
    while (qh < qt) {
        int sz = qt - qh;
        int* lv = (int*)malloc(sizeof(int) * (size_t)sz);
        for (int i = 0; i < sz; i++) {
            struct TreeNode* n = q[qh++];
            lv[i] = n->val;
            if (n->left) q[qt++] = n->left;
            if (n->right) q[qt++] = n->right;
        }
        res[rows] = lv;
        cols[rows] = sz;
        rows++;
    }
    *returnColumnSizes = cols;
    *returnSize = rows;
    return res;
}
`,
  },
]

const browser = await puppeteer.launch({
  executablePath: '/usr/bin/google-chrome-stable',
  headless: true,
  protocolTimeout: 600000,
  args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'],
})
const page = await browser.newPage()
page.setDefaultTimeout(600000)
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
  () => document.body.innerText.includes('C 工具链就绪'),
  { timeout: 300000 },
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
  console.log(c.label, 'bad ok?', result?.ok, 'passed', result?.passedCount)
  if (result?.ok) {
    console.error('FAIL: bad should not pass', c.label)
    process.exitCode = 1
  }
  await page.evaluate(async (src) => {
    await window.__treePractice.submit(src)
  }, c.good)
  result = await page.evaluate(() => window.__treePractice.getResult())
  console.log(c.label, 'good ok?', result?.ok, 'passed', result?.passedCount)
  if (!result?.ok) {
    console.error('FAIL: good should pass', c.label, result)
    process.exitCode = 1
  }
}

await browser.close()
