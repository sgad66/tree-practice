# 枝径 TreePath

数据结构在线编程练习站（C 语言）：树专题 + 数组 / 栈队列 / 链表 / 哈希 / 堆 / 图 / 排序查找，浏览器内编写**完整 C 程序（含 main）**。

## 分类与题量

| 分类 | 题量 |
|------|------|
| 树·遍历与序列 | 13 |
| 树·基础属性 | 13 |
| 树·路径与递归 | 13 |
| 树·二叉搜索树 | 13 |
| 树·构造与序列化 | 12 |
| 树·最近公共祖先 | 12 |
| 树·层序与视图 | 12 |
| 树·进阶综合 | 12 |
| 数组与列表 | 10 |
| 栈 | 10 |
| 队列 | 8 |
| 链表 | 10 |
| 哈希表 | 10 |
| 堆与优先队列 | 8 |
| 图论基础 | 10 |
| 排序与查找 | 8 |
| **合计** | **174** |

## 功能

- 中文题面；侧边栏按分类浏览与筛选
- 浏览器内完整 C 程序判题（[browsercc](https://github.com/BertalanD/browsercc) = clang/lld → WASM + WASI）
- 用例级通过/失败：期望 vs 实际、错误类型提示
- 练习区全视口布局；进度保存在 `localStorage`

## 公开站点

**https://sgad66.github.io/tree-practice/**

## 输入 / 输出约定

**不要方括号 / JSON。** 判题按 token 比较（多行与空格等价）。

- **输入**：树/数组用空格分隔数字与 `NULL`（如 `1 NULL 2 3`）；空 = 空行；整数一行一个；二维每行一组数并以空行结束
- **输出**：单值一行；一维空格分隔或每值一行；二维每行一组数字

详见题面【编写说明】与 Project 文档 `treepath-io-rules-zh.md`。

## 判题护栏

运行超时 2.5s/用例；WASM 内存 32MB；stdout 256KB；空提交 / 缺 `main` 立即 CE；重复提交取消上次运行。

## 本地开发

```bash
npm install
npm run dev
```

生成题库：

```bash
python3 scripts/gen_problems.py
```

## 技术栈

Vite · React · TypeScript · CodeMirror · browsercc · WASI shim
