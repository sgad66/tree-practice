import puppeteer from 'puppeteer-core'

const BASE = process.env.APP_URL || 'http://127.0.0.1:5173'

/** Minimal full-program helpers shared by BAD/GOOD smoke solutions. */
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
  while (*s && isspace((unsigned char)*s)) s++;
  if (*s!='[') return NULL; s++;
  int vals[TP_NODE_MAX], nulls[TP_NODE_MAX], n=0;
  while (*s && *s!=']') {
    while (*s && isspace((unsigned char)*s)) s++;
    if (*s==']') break;
    if (n>=TP_NODE_MAX) break;
    if ((s[0]=='n'||s[0]=='N') && strncmp(s,"null",4)==0) { vals[n]=0; nulls[n]=1; n++; s+=4; }
    else { char *end=NULL; vals[n]=(int)strtol(s,&end,10); nulls[n]=0; n++; s=end?end:s; }
    while (*s && isspace((unsigned char)*s)) s++;
    if (*s==',') s++;
  }
  return tp_build_tree(vals,nulls,n);
}
static struct TreeNode *tp_read_tree(void) {
  if (!tp_read_line(tp_line, TP_LINE_MAX)) return NULL;
  return tp_parse_tree(tp_line);
}
static void tp_print_int_array(int *a, int n) {
  putchar('[');
  for (int i=0;i<n;i++) { if (i) putchar(','); printf("%d", a[i]); }
  putchar(']');
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

const LOOP = `#include <stdio.h>
int main(void) {
  for (;;) { /* intentional infinite loop */ }
  return 0;
}
`

const MEMBOMB = `#include <stdlib.h>
int main(void) {
  for (;;) {
    void *p = malloc(1024 * 1024);
    if (!p) return 1;
    ((volatile char *)p)[0] = 1;
    ((volatile char *)p)[1024 * 1024 - 1] = 2;
  }
  return 0;
}
`

const { result: empty } = await run('   \n\t  ', 'EMPTY')
const emptyMsg = empty?.compileError || ''
if (empty?.ok || !/提交内容为空/.test(emptyMsg)) {
  console.error('FAIL: empty submit should CE with 提交内容为空, got', emptyMsg)
  process.exitCode = 1
} else {
  console.log('empty submit ok')
}

const { result: noMain } = await run('#include <stdio.h>\nint x;\n', 'NOMAIN')
const noMainMsg = noMain?.compileError || ''
if (noMain?.ok || !/main/.test(noMainMsg)) {
  console.error('FAIL: missing main should CE, got', noMainMsg)
  process.exitCode = 1
} else {
  console.log('missing main ok')
}

const { result: loop, elapsed: loopMs } = await run(LOOP, 'LOOP')
const loopErr = loop?.cases?.[0]?.error || ''
const loopHint = loop?.cases?.[0]?.hint || ''
const loopText = JSON.stringify(loop)
if (loop?.ok) {
  console.error('FAIL: infinite loop should not pass')
  process.exitCode = 1
} else if (!/运行超时|死循环/.test(loopErr + loopHint + loopText)) {
  console.error('FAIL: expected timeout message, got', loopErr, loopHint)
  process.exitCode = 1
} else if (loopMs > 20000) {
  console.error('FAIL: timeout took too long (UI may have frozen)', loopMs)
  process.exitCode = 1
} else {
  console.log('loop timeout ok in', loopMs, 'ms')
}

const { result: mem, elapsed: memMs } = await run(MEMBOMB, 'MEM')
const memErr = mem?.cases?.[0]?.error || ''
const memHint = mem?.cases?.[0]?.hint || ''
const memText = JSON.stringify(mem)
if (mem?.ok) {
  console.error('FAIL: memory bomb should not pass')
  process.exitCode = 1
} else if (!/内存超限|运行超时|死循环/.test(memErr + memHint + memText)) {
  // Prefer 内存超限; timeout is acceptable if grow blocks until wall clock.
  console.error('FAIL: expected 内存超限 (or timeout), got', memErr, memHint)
  process.exitCode = 1
} else if (memMs > 25000) {
  console.error('FAIL: memory bomb took too long', memMs)
  process.exitCode = 1
} else {
  console.log('memory bomb ok in', memMs, 'ms:', memErr || memHint)
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

const { result: good } = await run(GOOD, 'GOOD')
if (!good?.ok) {
  console.error('FAIL: good solution did not pass', good)
  process.exitCode = 1
} else {
  console.log('good ok')
}

await browser.close()
