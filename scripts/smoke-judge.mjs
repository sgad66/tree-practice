import puppeteer from 'puppeteer-core'

const BASE = process.env.APP_URL || 'http://127.0.0.1:5173'

/** Minimal full-program helpers shared by BAD/GOOD smoke solutions (token I/O). */
const HELPERS = `#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

struct TreeNode { int val; struct TreeNode *left; struct TreeNode *right; };
#define TP_LINE_MAX 65536
#define TP_NODE_MAX 4096
static char tp_line[TP_LINE_MAX];
static int tp_read_line(char *buf, int cap) {
  if (!fgets(buf, cap, stdin)) { if (cap>0) buf[0]=0; return 0; }
  size_t n=strlen(buf);
  while (n>0 && (buf[n-1]=='\\n'||buf[n-1]=='\\r')) buf[--n]=0;
  return 1;
}
static int tp_ci_eq(const char *a, const char *b) {
  while (*a && *b) {
    char ca=(char)tolower((unsigned char)*a++);
    char cb=(char)tolower((unsigned char)*b++);
    if (ca!=cb) return 0;
  }
  return !*a && !*b;
}
static int tp_next_token(const char **ps, char *buf, int cap) {
  const char *s=*ps;
  while (*s && (isspace((unsigned char)*s) || *s==',' || *s=='[' || *s==']')) s++;
  if (!*s) { *ps=s; return 0; }
  int n=0;
  while (*s && !isspace((unsigned char)*s) && *s!=',' && *s!='[' && *s!=']') {
    if (n+1<cap) buf[n++]=*s;
    s++;
  }
  buf[n]=0; *ps=s; return n>0;
}
static struct TreeNode *tp_new(int v) {
  struct TreeNode *n=(struct TreeNode*)malloc(sizeof(*n));
  n->val=v; n->left=n->right=NULL; return n;
}
static struct TreeNode *tp_build_tree(int *vals, int *nulls, int len) {
  if (len<=0) return NULL;
  struct TreeNode **nodes=(struct TreeNode**)calloc((size_t)len,sizeof(struct TreeNode*));
  for (int i=0;i<len;i++) nodes[i]=nulls[i]?NULL:tp_new(vals[i]);
  int kids=1;
  for (int i=0;i<len;i++) {
    if (!nodes[i]) continue;
    if (kids<len) { nodes[i]->left=nodes[kids]; kids++; }
    if (kids<len) { nodes[i]->right=nodes[kids]; kids++; }
  }
  struct TreeNode *root=nodes[0]; free(nodes); return root;
}
static struct TreeNode *tp_parse_tree(const char *s) {
  int vals[TP_NODE_MAX], nulls[TP_NODE_MAX], n=0;
  char tok[64];
  while (n<TP_NODE_MAX && tp_next_token(&s, tok, 64)) {
    if (tp_ci_eq(tok,"null")||tp_ci_eq(tok,"nil")) { vals[n]=0; nulls[n]=1; n++; }
    else { vals[n]=(int)strtol(tok,NULL,10); nulls[n]=0; n++; }
  }
  return tp_build_tree(vals,nulls,n);
}
static struct TreeNode *tp_read_tree(void) {
  if (!tp_read_line(tp_line, TP_LINE_MAX)) return NULL;
  return tp_parse_tree(tp_line);
}
static void tp_print_int_array(int *a, int n) {
  for (int i=0;i<n;i++) { if (i) putchar(' '); printf("%d", a[i]); }
}
static void tp_print_int_array_lines(int *a, int n) {
  for (int i=0;i<n;i++) printf("%d\\n", a[i]);
}
`

const BAD = `${HELPERS}
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
int main(void) {
  struct TreeNode* root = tp_read_tree();
  int rs = 0;
  int* res = preorderTraversal(root, &rs);
  tp_print_int_array(res, rs);
  putchar('\\n');
  return 0;
}
`

/** Correct preorder, printed one value per line (multi-line stdout). */
const GOOD_LINES = `${HELPERS}
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
int main(void) {
  struct TreeNode* root = tp_read_tree();
  int rs = 0;
  int* res = preorderTraversal(root, &rs);
  tp_print_int_array_lines(res, rs);
  return 0;
}
`

const GOOD = `${HELPERS}
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
int main(void) {
  struct TreeNode* root = tp_read_tree();
  int rs = 0;
  int* res = preorderTraversal(root, &rs);
  tp_print_int_array(res, rs);
  putchar('\\n');
  return 0;
}
`

/** Scalar: max depth of binary tree. */
const DEPTH = `${HELPERS}
int maxDepth(struct TreeNode* root) {
  if (!root) return 0;
  int L = maxDepth(root->left), R = maxDepth(root->right);
  return (L > R ? L : R) + 1;
}
int main(void) {
  struct TreeNode* root = tp_read_tree();
  printf("%d\\n", maxDepth(root));
  return 0;
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

await page.click('button.btn--primary')
await page.waitForFunction(
  () => document.body.innerText.includes('C 工具链就绪'),
  { timeout: 300000 },
)
await page.waitForFunction(() => window.__treePractice, { timeout: 30000 })

const initial = await page.evaluate(() => window.__treePractice.getCode())
if (initial.trim() !== '') {
  console.error('FAIL: editor should start empty, got length', initial.length)
  process.exitCode = 1
} else {
  console.log('editor starts empty')
}

await page.evaluate(() => {
  window.__treePractice.setCode('int x;')
})
await page.evaluate(() => {
  const btns = Array.from(document.querySelectorAll('.editor-toolbar button'))
  const reset = btns.find((b) => b.textContent?.includes('重置'))
  if (!reset) throw new Error('reset button missing')
  reset.click()
})
await new Promise((r) => setTimeout(r, 200))
const afterReset = await page.evaluate(() => window.__treePractice.getCode())
if (afterReset.trim() !== '') {
  console.error('FAIL: reset should clear editor', JSON.stringify(afterReset))
  process.exitCode = 1
} else {
  console.log('reset clears to empty')
}

const bodyText = await page.evaluate(() => document.body.innerText)
if (!/NULL|空格分隔|不要方括号/.test(bodyText)) {
  console.error('FAIL: statement/callout should describe token I/O')
  process.exitCode = 1
} else {
  console.log('I/O rules visible in UI')
}

console.log('ready')

async function run(code, label) {
  const t0 = Date.now()
  await page.evaluate(async (src) => {
    await window.__treePractice.submit(src)
  }, code)
  const elapsed = Date.now() - t0
  const result = await page.evaluate(() => window.__treePractice.getResult())
  console.log(`=== ${label} === (${elapsed}ms)`)
  console.log(
    JSON.stringify(
      {
        ok: result?.ok,
        passed: result?.passedCount,
        total: result?.totalCount,
        compileError: result?.compileError?.slice?.(0, 200),
        actual0: result?.cases?.[0]?.actual,
        error0: result?.cases?.[0]?.error,
        hint0: result?.cases?.[0]?.hint,
      },
      null,
      2,
    ),
  )
  return { result, elapsed }
}

async function openProblem(titleSubstr) {
  await page.evaluate((sub) => {
    const links = Array.from(document.querySelectorAll('button.problem-link'))
    const hit = links.find((b) => b.textContent?.includes(sub))
    if (!hit) throw new Error('problem not found: ' + sub)
    hit.click()
  }, titleSubstr)
  await new Promise((r) => setTimeout(r, 300))
}

const { result: empty } = await run('   \n\t  ', 'EMPTY')
const emptyMsg = empty?.compileError || ''
if (empty?.ok || !/提交内容为空/.test(emptyMsg)) {
  console.error('FAIL: empty submit should CE with 提交内容为空, got', emptyMsg)
  process.exitCode = 1
} else {
  console.log('empty submit ok')
}

const { result: bad } = await run(BAD, 'BAD')
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

const { result: goodLines } = await run(GOOD_LINES, 'GOOD_LINES')
if (!goodLines?.ok) {
  console.error('FAIL: multi-line good preorder should pass', goodLines)
  process.exitCode = 1
} else {
  console.log('good multi-line preorder ok')
}

const { result: good } = await run(GOOD, 'GOOD')
if (!good?.ok) {
  console.error('FAIL: good solution did not pass', good)
  process.exitCode = 1
} else {
  console.log('good space-separated ok')
}

await openProblem('最大深度')
const { result: depth } = await run(DEPTH, 'DEPTH')
if (!depth?.ok) {
  console.error('FAIL: scalar max-depth should pass', depth)
  process.exitCode = 1
} else {
  console.log('scalar max-depth ok')
}

await browser.close()
