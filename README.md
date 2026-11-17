# 枝径 TreePath

专注**二叉树**知识的在线编程练习站：八大分类、**100** 道题。

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
- 浏览器内 Python（[Pyodide](https://pyodide.org)）提交与判题，不在服务端执行用户代码
- 用例级通过/失败：失败用例、期望 vs 实际、错误类型提示
- 进度保存在 `localStorage`，无需登录

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
3. 实现指定函数后「提交」；首次会加载 Pyodide
4. 全部用例通过后记为已完成

## 技术栈

Vite · React · TypeScript · CodeMirror · Pyodide

题面数据按分类拆在 `src/data/categories/*.ts`，由 `src/data/problems.ts` 汇总。
