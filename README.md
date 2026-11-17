# 枝径 TreePath

专注**二叉树**知识的在线编程练习站：八大分类、**100** 道题，浏览器内写 **C 语言**。

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
- 浏览器内 C（[browsercc](https://github.com/BertalanD/browsercc) = clang/lld → WASM + WASI）提交与判题，**不在服务端**执行用户代码
- 用例级通过/失败：失败用例、期望 vs 实际、错误类型提示
- 练习区全视口布局（侧栏 + 题面 + 大编辑器 + 结果）
- 进度保存在 `localStorage`，无需登录

## 公开站点

**https://sgad66.github.io/tree-practice/**

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
3. 按 C 函数原型实现后「提交」；首次会从 CDN 加载 clang WASM 工具链
4. 全部用例通过后记为已完成

## 工具链说明 / 限制

- 判题在浏览器内：`browsercc`（Clang/LLD WASM）编译为 WASI 模块，再用 `@bjorn3/browser_wasi_shim` 运行
- 首次加载约需下载 **clang.wasm / lld.wasm / sysroot**（合计约 90MB 量级，视 CDN 与压缩而定），需联网
- 面向常见题解子集：C 风格 API（`struct TreeNode`、`malloc` 返回数组、`returnSize` / `returnColumnSizes`）
- 底层经 browsercc 的 **clang++ / C++17**（`-fno-exceptions`）编译；请写可被 C++17 接受的 C 代码（勿用 GCC 嵌套函数等扩展）
- WASI 环境无完整 POSIX 线程；请勿依赖文件、网络、多线程
- 不要在解法中定义 `main`（判题 harness 会提供）

## 技术栈

Vite · React · TypeScript · CodeMirror · browsercc · WASI shim

题面数据按分类拆在 `src/data/categories/*.ts`，由 `src/data/problems.ts` 汇总。
