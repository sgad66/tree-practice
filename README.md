# 枝径 TreePath

专注**二叉树**知识的在线编程练习站：八大分类、**100** 道题，浏览器内编写**完整 C 程序（含 main）**。

## 分类与题量

| 分类 | 题量 |
|------|------|
| 遍历与序列 | 13 |
| 二叉树基础属性 | 13 |
| 路径与递归 | 13 |
| 二叉搜索树 BST | 13 |
| 构造与序列化 | 12 |
| 最近公共祖先与祖先关系 | 12 |
| 层序与视图 | 12 |
| 进阶 / 综合 | 12 |
| **合计** | **100** |

## 功能

- 中文题面；侧边栏按分类浏览，并显示每类题量；可用分类筛选
- 浏览器内完整 C 程序判题（[browsercc](https://github.com/BertalanD/browsercc) = clang/lld → WASM + WASI）：编译用户整份程序，stdin 注入用例，比较 stdout
- 用例级通过/失败：失败用例、期望 vs 实际、错误类型提示
- 练习区全视口布局（侧栏 + 题面 + 大编辑器 + 结果）
- 进度保存在 `localStorage`，无需登录

## 公开站点

**https://sgad66.github.io/tree-practice/**

## 输入 / 输出约定（所有题目一致）

请编写**完整 C 程序（含 main）**。编辑器默认空白；树结构、stdin/stdout 约定写在题面中。

**stdin**（每个参数一行）：

- 树：层序数组，如 `[3,9,20,null,null,15,7]`；空树 `[]`
- 整数 / 浮点 / 布尔：各占一行（布尔为 `true` / `false`）
- 一维数组：`[1,2,3]`；二维数组：`[[1,2],[3,4]]`
- 字符串：一行原文
- LCA 题：第 1 行树，第 2 行 `p`，第 3 行 `q`（值为节点值）

**stdout**（一行）：

- 整数、`true`/`false`、层序数组，或 JSON 风格数组/字符串（与示例一致）

判题对每个用例：编译一次用户程序 → 用该用例的 stdin 运行 → 解析 stdout 与期望比较。

## 本地运行

```bash
npm install
npm run dev
```

重新生成题库（改 `scripts/gen_problems.py` 后）：

```bash
python3 scripts/gen_problems.py
```

生产构建：

```bash
npm run build
npm run preview
```

## 使用说明

1. 打开首页，点击「开始练习」
2. 左侧按分类选题（可点筛选芯片）
3. 编辑器默认空白：自行编写完整 C 程序（含 `main`），遵守题面 I/O；点击「提交」；首次会从 CDN 加载 clang WASM 工具链
4. 「重置代码」清空编辑器；全部用例通过后记为已完成

## 工具链说明 / 限制

- 判题在浏览器内：`browsercc`（Clang/LLD WASM）编译为 WASI 模块，再用 `@bjorn3/browser_wasi_shim` 运行
- 首次加载约需下载 **clang.wasm / lld.wasm / sysroot**（合计约 90MB 量级），需联网
- 底层经 browsercc 的 **clang++ / C++17**（`-fno-exceptions`）编译；请写可被 C++17 接受的 C 代码（勿用 GCC 嵌套函数等扩展）
- WASI 环境无完整 POSIX 线程；请勿依赖文件、网络、多线程（stdin/stdout 可用）
- **I/O**：无方括号。树/数组用空格分隔数字与 `NULL`（如 `1 NULL 2 3`）；输出同理，多行或空格分隔均可（按 token 比较）
- 判题护栏（每用例）：运行超时 **2.5s**（「运行超时（可能死循环）」）；WASM 内存上限 **32MB**（「内存超限」）；stdout 上限 **256KB**；空提交 / 缺 `main` 立即 CE；编译超时 45s；重复提交会取消上一次运行

## 技术栈

Vite · React · TypeScript · CodeMirror · browsercc · WASI shim

题面数据按分类拆在 `src/data/categories/*.ts`，由 `src/data/problems.ts` 汇总。
