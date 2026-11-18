import puppeteer from 'puppeteer-core'

const BASE = process.env.APP_URL || 'http://127.0.0.1:5173'

const HELPERS = `#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdbool.h>
#include <limits.h>
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
static void tp_print_int_matrix(int **a, int rows, int *cols) {
  for (int i=0;i<rows;i++) {
    if (i) putchar('\\n');
    tp_print_int_array(a?a[i]:NULL, cols?cols[i]:0);
  }
}
`

const CASES = [
  {
    label: 'basics/max-depth',
    openTitle: '二叉树的最大深度',
    bad: `${HELPERS}
int maxDepth(struct TreeNode* root) {
  if (!root) return 0;
  int l = maxDepth(root->left), r = maxDepth(root->right);
  return l > r ? l : r;
}
int main(void) {
  printf("%d\\n", maxDepth(tp_read_tree()));
  return 0;
}
`,
    good: `${HELPERS}
int maxDepth(struct TreeNode* root) {
  if (!root) return 0;
  int l = maxDepth(root->left), r = maxDepth(root->right);
  return 1 + (l > r ? l : r);
}
int main(void) {
  printf("%d\\n", maxDepth(tp_read_tree()));
  return 0;
}
`,
  },
  {
    label: 'bst/validate-bst',
    openTitle: '验证二叉搜索树',
    bad: `${HELPERS}
bool isValidBST(struct TreeNode* root) {
  if (!root) return true;
  if (root->left && root->left->val >= root->val) return false;
  if (root->right && root->right->val <= root->val) return false;
  return isValidBST(root->left) && isValidBST(root->right);
}
int main(void) {
  printf(isValidBST(tp_read_tree()) ? "true\\n" : "false\\n");
  return 0;
}
`,
    good: `${HELPERS}
static bool ok(struct TreeNode* n, long lo, long hi) {
  if (!n) return true;
  if (n->val <= lo || n->val >= hi) return false;
  return ok(n->left, lo, n->val) && ok(n->right, n->val, hi);
}
bool isValidBST(struct TreeNode* root) {
  return ok(root, LONG_MIN, LONG_MAX);
}
int main(void) {
  printf(isValidBST(tp_read_tree()) ? "true\\n" : "false\\n");
  return 0;
}
`,
  },
  {
    label: 'levelview/level-order',
    openTitle: '二叉树的层序遍历',
    bad: `${HELPERS}
int** levelOrder(struct TreeNode* root, int* returnSize, int** returnColumnSizes) {
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
  return out;
}
int main(void) {
  int rs=0; int* cols=NULL;
  int** res = levelOrder(tp_read_tree(), &rs, &cols);
  tp_print_int_matrix(res, rs, cols);
  putchar('\\n');
  return 0;
}
`,
    good: `${HELPERS}
int** levelOrder(struct TreeNode* root, int* returnSize, int** returnColumnSizes) {
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
int main(void) {
  int rs=0; int* cols=NULL;
  int** res = levelOrder(tp_read_tree(), &rs, &cols);
  tp_print_int_matrix(res, rs, cols);
  putchar('\\n');
  return 0;
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

await page.click('button.btn--primary')
await page.waitForFunction(
  () => document.body.innerText.includes('C 工具链就绪'),
  { timeout: 300000 },
)
await page.waitForFunction(() => window.__treePractice, { timeout: 30000 })

const initial = await page.evaluate(() => window.__treePractice.getCode())
if (initial.trim() !== '') {
  console.error('FAIL: editor should start empty')
  process.exitCode = 1
} else {
  console.log('editor starts empty')
}

const sidebarCount = await page.evaluate(() => document.querySelectorAll('.problem-link').length)
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
  const code = await page.evaluate(() => window.__treePractice.getCode())
  if (code.trim() !== '') {
    console.error('FAIL: editor not empty after switch', c.label, code.length)
    process.exitCode = 1
  }
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
  console.log(c.label, 'good ok?', result?.ok, 'passed', result?.passedCount, result?.compileError?.slice?.(0, 160))
  if (!result?.ok) {
    console.error('FAIL: good should pass', c.label, result)
    process.exitCode = 1
  }
}

await browser.close()
