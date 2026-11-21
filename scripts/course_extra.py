#!/usr/bin/env python3
"""Problems tightly aligned to BUPT struct-analysis courseware (CH0–CH7 + 引用传递)."""
from __future__ import annotations

from collections import Counter, defaultdict, deque
from heapq import heappop, heappush
from typing import Callable

COURSE_CONSTRAINTS = [
    "请编写完整 C 程序（含 main）；不要依赖判题替你写入口",
    "输入为数字与 NULL 的空格/换行分隔 token（无方括号）",
    "本题对齐《结构分析》课件相应章节；注意边界与课件术语",
]


def add_course_problems(P: Callable, T: Callable) -> list[dict]:
    C: list[dict] = []

    # ── CH0/CH1 intro ────────────────────────────────────────────────────────
    def ref_seq_search(nums, x):
        for i, v in enumerate(nums):
            if v == x:
                return i + 1  # 1-based position like slides
        return 0

    def ref_bin_search_pos(nums, x):
        lo, hi = 0, len(nums) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if nums[mid] == x:
                return mid + 1
            if nums[mid] < x:
                lo = mid + 1
            else:
                hi = mid - 1
        return 0

    def ref_surname_block_start(keys, starts, q):
        # keys: surname codes sorted; starts: start index in phonebook (1-based)
        # return start address for surname q, or 0
        for k, s in zip(keys, starts):
            if k == q:
                return s
        return 0

    def ref_adt_is_empty(n):
        return n == 0

    def ref_list_size(nums):
        return len(nums)

    def ref_unique_successor_ok(nums):
        # linear list positions 1..n — always true for array; return n (successor count of non-last)
        return max(0, len(nums) - 1)

    C += [
        P(
            "sa-sequential-find",
            "顺序表顺序查找（课件位置）",
            "sa_intro",
            "简单",
            "【CH1/电话簿直觉】在整数序列中顺序查找 `x`，返回**1-based**首次出现位置；未找到返回 0。",
            [{"input": "3 1 4 1 5\n1", "output": "2"}],
            "seqFind",
            "(nums: List[int], x: int) -> int",
            "顺序查找",
            "raw",
            ref_seq_search,
            [
                T("样例", [[3, 1, 4, 1, 5], 1], True),
                T("未找到", [[1, 2, 3], 9], True),
                T("首元", [[7], 7]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-sorted-bin-find",
            "有序表二分查找位置",
            "sa_intro",
            "简单",
            "【CH0 有序排书】升序表中二分查找 `x`，返回 1-based 位置；否则 0。",
            [{"input": "1 3 5 7 9\n7", "output": "4"}],
            "binFind",
            "(nums: List[int], x: int) -> int",
            "二分",
            "raw",
            ref_bin_search_pos,
            [
                T("命中", [[1, 3, 5, 7, 9], 7], True),
                T("未命中", [[1, 3, 5], 2], True),
                T("空", [[], 1]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-surname-index",
            "姓氏索引表定位",
            "sa_intro",
            "中等",
            "【CH0 电话簿索引】输入姓氏码序列 `keys` 与对应起始地址 `starts`（等长），"
            "再给查询姓氏 `q`，返回索引表中的起始地址；无则 0。",
            [{"input": "1 2 3\n10 40 70\n2", "output": "40"}],
            "surnameIndex",
            "(keys: List[int], starts: List[int], q: int) -> int",
            "索引表",
            "raw",
            ref_surname_block_start,
            [
                T("样例", [[1, 2, 3], [10, 40, 70], 2], True),
                T("无", [[1, 2], [1, 5], 9], True),
                T("首", [[5], [100], 5]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-adt-isempty",
            "ADT：表是否为空",
            "sa_intro",
            "简单",
            "【CH1 ADT】给定表长 `n`，`IsEmpty`：n=0 为 true。",
            [{"input": "0", "output": "true"}],
            "isEmptyList",
            "(n: int) -> bool",
            "IsEmpty",
            "raw",
            ref_adt_is_empty,
            [T("空", [0], True), T("非空", [3], True), T("1", [1])],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-list-length",
            "ADT：表长",
            "sa_intro",
            "简单",
            "【CH3 List】返回线性表元素个数。",
            [{"input": "2 4 6", "output": "3"}],
            "listLength",
            "(nums: List[int]) -> int",
            "Length",
            "raw",
            ref_list_size,
            [T("样例", [[2, 4, 6]], True), T("空", [[]], True), T("单", [[9]])],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-successor-count",
            "线性表后继个数",
            "sa_intro",
            "简单",
            "【CH3】线性表中每个非末元素有唯一后继。返回「有后继」的元素个数，即 max(0, n-1)。",
            [{"input": "1 2 3 4", "output": "3"}],
            "successorCount",
            "(nums: List[int]) -> int",
            "后继定义",
            "raw",
            ref_unique_successor_ok,
            [T("样例", [[1, 2, 3, 4]], True), T("单", [[1]], True), T("空", [[]])],
            constraints=COURSE_CONSTRAINTS,
        ),
    ]

    # ── CH2 analysis ─────────────────────────────────────────────────────────
    def ref_simplify_big_o(coeffs):
        # coeffs[i] = coeff of n^i ; return highest i with nonzero coeff (degree)
        deg = 0
        for i, c in enumerate(coeffs):
            if c != 0:
                deg = i
        return deg

    def ref_compare_growth(a, b, n):
        # compare n^a vs n^b at given n: return -1 if a-side smaller time, 0 equal, 1 if a larger
        # use log: a*log n vs b*log n
        if n <= 1:
            return 0 if a == b else (-1 if a < b else 1)
        import math

        la, lb = a * math.log(n), b * math.log(n)
        if abs(la - lb) < 1e-12:
            return 0
        return -1 if la < lb else 1

    def ref_sum_cubes_steps(n):
        # from slides: partialsum=0 (1) + for 1+(n+1)+n + body ~ ; return 2n+3 style for sum 1..n iterative
        return 2 * n + 3

    def ref_max_sub_cubic_ops(nums):
        # count of triple-loop iterations i..j..k (classic O(n^3) MSS)
        n = len(nums)
        ops = 0
        for i in range(n):
            for j in range(i, n):
                for _k in range(i, j + 1):
                    ops += 1
        return ops

    def ref_mss_online(nums):
        best = cur = nums[0]
        for x in nums[1:]:
            cur = max(x, cur + x)
            best = max(best, cur)
        return best

    def ref_mss_quadratic(nums):
        n = len(nums)
        best = nums[0]
        for i in range(n):
            s = 0
            for j in range(i, n):
                s += nums[j]
                best = max(best, s)
        return best

    def ref_order_rank(code):
        # map growth class code to rank: 1=1,2=logn,3=n,4=nlogn,5=n2,6=n3,7=2n
        return code  # identity; problem asks compare two codes which is slower

    def ref_which_slower(c1, c2):
        return c1 if c1 > c2 else (c2 if c2 > c1 else 0)

    def ref_fact_calls(n):
        # number of calls to factorial including top:  n+1 for naive recursive
        return n + 1

    def ref_binary_search_worst(n):
        # worst-case comparisons upper ~ floor(log2 n)+1
        if n <= 0:
            return 0
        c = 0
        while n > 0:
            n //= 2
            c += 1
        return c

    C += [
        P(
            "sa-big-o-degree",
            "化简多项式得 O 的次数",
            "sa_analysis",
            "简单",
            "【CH2】多项式系数按 `n^0, n^1, …` 给出（可含 0）。返回主导项次数（最高非零系数的次数）。"
            "例：`5 4 0 3` → 3n³+… → 3。",
            [{"input": "5 4 0 3", "output": "3"}],
            "polyDegree",
            "(coeffs: List[int]) -> int",
            "去低阶取主导",
            "raw",
            ref_simplify_big_o,
            [
                T("样例", [[5, 4, 0, 3]], True),
                T("常数", [[7]], True),
                T("2n+3", [[3, 2]]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-growth-compare",
            "比较 n^a 与 n^b 在给定 N",
            "sa_analysis",
            "中等",
            "【CH2】输入 a b N。比较 N^a 与 N^b 增长：若前者更小输出 -1，相等 0，更大 1。",
            [{"input": "1\n2\n100", "output": "-1"}],
            "cmpGrowth",
            "(a: int, b: int, n: int) -> int",
            "相对增长",
            "raw",
            ref_compare_growth,
            [
                T("N^1 vs N^2", [1, 2, 100], True),
                T("相等", [3, 3, 10], True),
                T("大指数", [3, 2, 5]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-sum-iter-steps",
            "迭代求和语句步数 2n+3",
            "sa_analysis",
            "简单",
            "【CH2 1+…+n 迭代】课件给出 T(n)=2n+3。输入 n，输出该估算步数。",
            [{"input": "100", "output": "203"}],
            "sumSteps",
            "(n: int) -> int",
            "步数公式",
            "raw",
            ref_sum_cubes_steps,
            [T("100", [100], True), T("1", [1], True), T("0", [0])],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-mss-cubic-ops",
            "最大子段和三重循环操作次数",
            "sa_analysis",
            "中等",
            "【CH2 MSS】对长度为 n 的数组，统计经典三重循环（i≤k≤j）的内层执行次数。",
            [{"input": "1 2 3", "output": "10"}],
            "mssCubicOps",
            "(nums: List[int]) -> int",
            "O(n³) 计数",
            "raw",
            ref_max_sub_cubic_ops,
            [
                T("n=3", [[1, 2, 3]], True),
                T("n=1", [[5]], True),
                T("n=2", [[1, -1]]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-mss-online",
            "最大子序列和（在线/Kadane）",
            "sa_analysis",
            "中等",
            "【CH2 MSS 最优】用在线算法求最大连续子段和。",
            [{"input": "-2 11 -4 13 -5 -2", "output": "20"}],
            "mssOnline",
            "(nums: List[int]) -> int",
            "在线算法",
            "raw",
            ref_mss_online,
            [
                T("Weiss 例", [[-2, 11, -4, 13, -5, -2]], True),
                T("全负", [[-3, -1, -2]], True),
                T("单", [[4]]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-mss-quadratic",
            "最大子序列和（二重循环）",
            "sa_analysis",
            "中等",
            "【CH2】用 O(n²) 前缀累加求最大子段和（与在线结果应一致）。",
            [{"input": "-2 11 -4 13 -5 -2", "output": "20"}],
            "mssQuadratic",
            "(nums: List[int]) -> int",
            "O(n²)",
            "raw",
            ref_mss_quadratic,
            [
                T("Weiss", [[-2, 11, -4, 13, -5, -2]], True),
                T("正", [[1, 2, 3]], True),
                T("交替", [[1, -1, 1]]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-complexity-slower",
            "哪个渐近阶更慢",
            "sa_analysis",
            "简单",
            "【CH2 阶梯】用编码：1=O(1) 2=O(log n) 3=O(n) 4=O(n log n) 5=O(n²) 6=O(n³) 7=O(2ⁿ)。"
            "输入两码，返回更慢者；相同返回 0。",
            [{"input": "3\n5", "output": "5"}],
            "slowerClass",
            "(c1: int, c2: int) -> int",
            "阶比较",
            "raw",
            ref_which_slower,
            [T("n vs n2", [3, 5], True), T("同", [4, 4], True), T("2n vs n3", [7, 6])],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-fact-call-count",
            "递归阶乘调用次数",
            "sa_analysis",
            "简单",
            "【CH2 递归】朴素 `fact(n)=n*fact(n-1)`，`fact(0)=1`。返回调用 `fact` 的总次数（含顶层）。",
            [{"input": "5", "output": "6"}],
            "factCalls",
            "(n: int) -> int",
            "递归代价",
            "raw",
            ref_fact_calls,
            [T("5", [5], True), T("0", [0], True), T("1", [1])],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-binsearch-worst-cmp",
            "二分查找最坏比较次数上界",
            "sa_analysis",
            "简单",
            "【CH2】长度 n 的有序表，二分最坏比较次数上界取 ⌊log2 n⌋+1（n>0）；n=0 为 0。",
            [{"input": "8", "output": "4"}],
            "binWorst",
            "(n: int) -> int",
            "log 界",
            "raw",
            ref_binary_search_worst,
            [T("8", [8], True), T("1", [1], True), T("0", [0])],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-ta-vs-tb",
            "TA=1000N 与 TB=N² 谁更快",
            "sa_analysis",
            "简单",
            "【CH2】课件例：TA=1000N，TB=N²。输入 N，若 TA 更小（更快）输出 1；TB 更快输出 2；相等输出 0。",
            [{"input": "100", "output": "2"}],
            "cmpTAB",
            "(n: int) -> int",
            "交叉点 1000",
            "raw",
            lambda n: (1 if 1000 * n < n * n else (2 if 1000 * n > n * n else 0)),
            [T("100", [100], True), T("1000", [1000], True), T("10000", [10000])],
            constraints=COURSE_CONSTRAINTS,
        ),
    ]

    # ── CH3 linear list ──────────────────────────────────────────────────────
    def ref_arr_insert(nums, x, loc):
        # 0-based loc like slides' location; insert x at loc, shift right
        a = list(nums)
        loc = max(0, min(loc, len(a)))
        a.insert(loc, x)
        return a

    def ref_arr_delete_val(nums, x):
        a = list(nums)
        for i, v in enumerate(a):
            if v == x:
                del a[i]
                return a
        return a  # not found: unchanged

    def ref_arr_find(nums, x):
        for i, v in enumerate(nums):
            if v == x:
                return i + 1
        return len(nums) + 1  # slides: last+1

    def ref_retrieve(nums, p):
        # 1-based
        if p < 1 or p > len(nums):
            return -1
        return nums[p - 1]

    def ref_find_prev(nums, x):
        for i, v in enumerate(nums):
            if v == x:
                return i  # 1-based previous position; if first, 0
        return -1

    def ref_ll_insert_head(nums, x):
        return [x] + list(nums)

    def ref_ll_delete_first(nums, x):
        a = list(nums)
        for i, v in enumerate(a):
            if v == x:
                del a[i]
                break
        return a

    def ref_cursor_next(nexts, p):
        # cursor list: nexts[i] is next index of node i (0=null); return nexts[p]
        if p < 0 or p >= len(nexts):
            return 0
        return nexts[p]

    def ref_doubly_neighbors(prev, nxt, p):
        # return prev[p], next[p]
        return [prev[p], nxt[p]]

    def ref_is_last(nums, p):
        return p == len(nums)

    C += [
        P(
            "sa-array-insert",
            "顺序表按位置插入",
            "sa_linear",
            "中等",
            "【CH3 Array Insert】在 0-based 位置 `loc` 插入 `x`（越界则插到两端），返回新序列。",
            [{"input": "34 12 52 16 12\n99\n3", "output": "34 12 52 99 16 12"}],
            "arrayInsert",
            "(nums: List[int], x: int, loc: int) -> List[int]",
            "搬移插入",
            "raw",
            ref_arr_insert,
            [
                T("课件风", [[34, 12, 52, 16, 12], 99, 3], True),
                T("头插", [[1, 2], 0, 0], True),
                T("尾", [[1], 5, 9]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-array-delete",
            "顺序表按值删除",
            "sa_linear",
            "中等",
            "【CH3 Delete】删除首次出现的值 `x` 并前移后续元素；不存在则原样返回。",
            [{"input": "34 12 52 16 12\n52", "output": "34 12 16 12"}],
            "arrayDelete",
            "(nums: List[int], x: int) -> List[int]",
            "搬移删除",
            "raw",
            ref_arr_delete_val,
            [
                T("样例", [[34, 12, 52, 16, 12], 52], True),
                T("无", [[1, 2], 9], True),
                T("删头", [[3, 4], 3]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-array-find",
            "顺序表 Find",
            "sa_linear",
            "简单",
            "【CH3 Find】返回 `x` 的 1-based 位置；未找到返回 n+1。",
            [{"input": "34 12 52 16 12\n16", "output": "4"}],
            "arrayFind",
            "(nums: List[int], x: int) -> int",
            "Find",
            "raw",
            ref_arr_find,
            [
                T("样例", [[34, 12, 52, 16, 12], 16], True),
                T("无", [[1, 2], 3], True),
                T("重复取首", [[2, 2], 2]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-retrieve",
            "顺序表 Retrieve",
            "sa_linear",
            "简单",
            "【CH3 Retrieve】取 1-based 位置 `p` 的元素；非法返回 -1。",
            [{"input": "10 20 30\n2", "output": "20"}],
            "retrieve",
            "(nums: List[int], p: int) -> int",
            "Retrieve",
            "raw",
            ref_retrieve,
            [T("样例", [[10, 20, 30], 2], True), T("非法", [[1], 3], True), T("1", [[9], 1])],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-find-previous",
            "FindPrevious 位置",
            "sa_linear",
            "中等",
            "【CH3 FindPrevious】找值 `x` 首次出现的前驱位置（1-based）；若 `x` 在首位返回 0；不存在 -1。",
            [{"input": "34 12 52 16 12\n12", "output": "1"}],
            "findPrevious",
            "(nums: List[int], x: int) -> int",
            "FindPrevious",
            "raw",
            ref_find_prev,
            [
                T("样例", [[34, 12, 52, 16, 12], 12], True),
                T("首位", [[5, 6], 5], True),
                T("无", [[1], 2]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-ll-push-front",
            "链表头插",
            "sa_linear",
            "简单",
            "【CH3 链表】在链表（值序列）头部插入 `x`。",
            [{"input": "2 3\n1", "output": "1 2 3"}],
            "llPushFront",
            "(nums: List[int], x: int) -> List[int]",
            "头插",
            "raw",
            ref_ll_insert_head,
            [T("样例", [[2, 3], 1], True), T("空", [[], 5], True), T("单", [[9], 8])],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-ll-delete-first",
            "链表按值删首个",
            "sa_linear",
            "简单",
            "【CH3】删除链表中首次出现的 `x`。",
            [{"input": "1 2 2 3\n2", "output": "1 2 3"}],
            "llDelete",
            "(nums: List[int], x: int) -> List[int]",
            "删结点",
            "raw",
            ref_ll_delete_first,
            [T("样例", [[1, 2, 2, 3], 2], True), T("无", [[1], 9], True), T("删唯一", [[4], 4])],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-cursor-next",
            "游标实现：取后继下标",
            "sa_linear",
            "中等",
            "【CH3 Cursor List】`nexts[i]` 为结点 i 的后继下标（0 表示空）。输入 nexts 与当前位置 `p`，返回后继。",
            [{"input": "0 2 3 0\n1", "output": "2"}],
            "cursorNext",
            "(nexts: List[int], p: int) -> int",
            "游标",
            "raw",
            ref_cursor_next,
            [
                T("样例", [[0, 2, 3, 0], 1], True),
                T("空后继", [[0, 0], 1], True),
                T("越界", [[1, 2], 5]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-doubly-neighbors",
            "双向链表邻接",
            "sa_linear",
            "中等",
            "【CH3 双向链表】给定 `prev` 与 `next` 数组及结点 `p`，输出 `prev[p] next[p]`。",
            [{"input": "0 0 1 2\n0 2 3 0\n2", "output": "1 3"}],
            "doublyNeighbors",
            "(prev: List[int], nxt: List[int], p: int) -> List[int]",
            "双向",
            "raw",
            ref_doubly_neighbors,
            [
                T("样例", [[0, 0, 1, 2], [0, 2, 3, 0], 2], True),
                T("端点", [[0, 0, 1], [0, 2, 0], 1], True),
                T("中", [[0, 0, 1, 2], [0, 2, 3, 0], 3]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-is-last",
            "IsLast 判定",
            "sa_linear",
            "简单",
            "【CH3 IsLast】1-based 位置 `p` 是否为表尾。",
            [{"input": "1 2 3\n3", "output": "true"}],
            "isLast",
            "(nums: List[int], p: int) -> bool",
            "IsLast",
            "raw",
            ref_is_last,
            [T("是", [[1, 2, 3], 3], True), T("否", [[1, 2, 3], 1], True), T("空表", [[], 1])],
            constraints=COURSE_CONSTRAINTS,
        ),
    ]

    # ── CH4 stack & queue ────────────────────────────────────────────────────
    OP_ADD, OP_SUB, OP_MUL, OP_DIV = 10**9 + 1, 10**9 + 2, 10**9 + 3, 10**9 + 4
    PREC = {OP_ADD: 1, OP_SUB: 1, OP_MUL: 2, OP_DIV: 2}

    def ref_balance(codes):
        # 1=( 2=) 3=[ 4=] 5={ 6=}
        mp = {2: 1, 4: 3, 6: 5}
        st = []
        for c in codes:
            if c in (1, 3, 5):
                st.append(c)
            else:
                if not st or st[-1] != mp.get(c):
                    return False
                st.pop()
        return not st

    def ref_infix_to_postfix(tokens):
        # tokens: operands >=0 small; ops as OP_*; parentheses  -10=( -11=)
        out = []
        st = []
        for t in tokens:
            if t == -10:
                st.append(t)
            elif t == -11:
                while st and st[-1] != -10:
                    out.append(st.pop())
                if st:
                    st.pop()
            elif t in PREC:
                while st and st[-1] in PREC and PREC[st[-1]] >= PREC[t]:
                    out.append(st.pop())
                st.append(t)
            else:
                out.append(t)
        while st:
            out.append(st.pop())
        return out

    def ref_eval_postfix(tokens):
        st = []
        for t in tokens:
            if t in PREC:
                b, a = st.pop(), st.pop()
                if t == OP_ADD:
                    st.append(a + b)
                elif t == OP_SUB:
                    st.append(a - b)
                elif t == OP_MUL:
                    st.append(a * b)
                else:
                    st.append(int(a / b))
            else:
                st.append(t)
        return st[-1]

    def ref_array_stack_ops(ops):
        # 1 x push; 2 pop->collect; 3 top->collect (empty -> -1)
        st = []
        out = []
        i = 0
        while i < len(ops):
            if ops[i] == 1:
                st.append(ops[i + 1])
                i += 2
            elif ops[i] == 2:
                out.append(st.pop() if st else -1)
                i += 1
            else:
                out.append(st[-1] if st else -1)
                i += 1
        return out

    def ref_circular_queue(k, ops):
        q = deque()
        for x in ops:
            if x == -1:
                if q:
                    q.popleft()
            else:
                if len(q) < k:
                    q.append(x)
        return list(q)

    def ref_queue_ops(ops):
        # 1 x enqueue; 2 dequeue collect
        q = deque()
        out = []
        i = 0
        while i < len(ops):
            if ops[i] == 1:
                q.append(ops[i + 1])
                i += 2
            else:
                out.append(q.popleft() if q else -1)
                i += 1
        return out

    def ref_stack_perm_valid(push_n, popped):
        st = []
        cur = 1
        for x in popped:
            while cur <= push_n and (not st or st[-1] != x):
                st.append(cur)
                cur += 1
            if not st or st[-1] != x:
                return False
            st.pop()
        return True

    C += [
        P(
            "sa-balance-symbols",
            "括号平衡（课件算法）",
            "sa_stackq",
            "简单",
            "【CH4 Balancing Symbols】编码 1=( 2=) 3=[ 4=] 5={ 6=}。按课件栈算法判定是否平衡。",
            [{"input": "1 3 4 2", "output": "true"}],
            "balanceSymbols",
            "(codes: List[int]) -> bool",
            "栈匹配",
            "raw",
            ref_balance,
            [
                T("()[]", [[1, 3, 4, 2]], True),
                T("错", [[1, 4]], True),
                T("空", [[]]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-infix-to-postfix",
            "中缀转后缀",
            "sa_stackq",
            "困难",
            "【CH4】token：操作数为非负整数；运算符 "
            f"{OP_ADD}=+ {OP_SUB}=- {OP_MUL}=* {OP_DIV}=/；括号 -10=( -11=)。输出后缀 token 序列。",
            [{"input": f"1 {OP_ADD} 2 {OP_MUL} 3", "output": f"1 2 3 {OP_MUL} {OP_ADD}"}],
            "infixToPostfix",
            "(tokens: List[int]) -> List[int]",
            "中缀→后缀",
            "raw",
            ref_infix_to_postfix,
            [
                T("a+b*c", [[1, OP_ADD, 2, OP_MUL, 3]], True),
                T("(1+2)*3", [[-10, 1, OP_ADD, 2, -11, OP_MUL, 3]], True),
                T("单", [[9]]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-eval-postfix",
            "后缀表达式求值",
            "sa_stackq",
            "中等",
            "【CH4】后缀求值；运算符编码同中缀题；除法向 0 取整。",
            [{"input": f"1 2 3 {OP_MUL} {OP_ADD}", "output": "7"}],
            "evalPostfix",
            "(tokens: List[int]) -> int",
            "后缀求值",
            "raw",
            ref_eval_postfix,
            [
                T("1+2*3", [[1, 2, 3, OP_MUL, OP_ADD]], True),
                T("除", [[8, 2, OP_DIV]], True),
                T("单", [[5]]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-array-stack-ops",
            "数组栈操作序列",
            "sa_stackq",
            "中等",
            "【CH4 数组栈】`1 x` push；`2` pop 输出；`3` top 输出；空栈得 -1。返回所有输出。",
            [{"input": "1 5 1 6 3 2 2", "output": "6 6 5"}],
            "arrayStackOps",
            "(ops: List[int]) -> List[int]",
            "数组栈",
            "raw",
            ref_array_stack_ops,
            [
                T("样例", [[1, 5, 1, 6, 3, 2, 2]], True),
                T("空弹", [[2]], True),
                T("仅顶", [[1, 1, 3]]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-circular-queue-sim",
            "循环队列模拟",
            "sa_stackq",
            "中等",
            "【CH4 Circular queue】容量 `k`；正数入队，-1 出队；满则忽略入队。返回最终队内从前到后。",
            [{"input": "3\n1 2 3 4 -1 5", "output": "2 3 5"}],
            "circularSim",
            "(k: int, ops: List[int]) -> List[int]",
            "循环队列",
            "raw",
            ref_circular_queue,
            [
                T("样例", [3, [1, 2, 3, 4, -1, 5]], True),
                T("空出", [2, [-1]], True),
                T("k1", [1, [9, 8]]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-queue-ops",
            "队列入取出序列",
            "sa_stackq",
            "简单",
            "【CH4】`1 x` 入队；`2` 出队并记录；空队 -1。",
            [{"input": "1 1 1 2 2 2", "output": "1 2"}],
            "queueOps",
            "(ops: List[int]) -> List[int]",
            "FIFO",
            "raw",
            ref_queue_ops,
            [
                T("样例", [[1, 1, 1, 2, 2, 2]], True),
                T("空", [[2]], True),
                T("单", [[1, 7, 2]]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-stack-permutation",
            "栈混洗合法性",
            "sa_stackq",
            "中等",
            "【CH4 应用】1..n 依次入栈，给定出栈序列，判断是否合法。",
            [{"input": "3\n1 2 3", "output": "true"}],
            "stackPerm",
            "(n: int, popped: List[int]) -> bool",
            "栈排列",
            "raw",
            ref_stack_perm_valid,
            [
                T("顺序", [3, [1, 2, 3]], True),
                T("非法", [3, [3, 1, 2]], True),
                T("经典", [3, [2, 3, 1]]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-two-stack-queue-enqueue-cost",
            "双栈模拟队列：一次入队后栈中元素数",
            "sa_stackq",
            "简单",
            "【CH4】用栈 A/B 模拟队列时，连续 `n` 次 enqueue 且尚未 dequeue，返回主栈中元素个数（即 n）。",
            [{"input": "4", "output": "4"}],
            "enqueueCount",
            "(n: int) -> int",
            "双栈队列",
            "raw",
            lambda n: n,
            [T("4", [4], True), T("0", [0], True), T("1", [1])],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-underflow-safe-pop",
            "空栈 Pop 次数统计",
            "sa_stackq",
            "简单",
            "【CH4 Underflow】操作：`1 x` push，`2` pop。统计发生下溢（空栈 pop）的次数。",
            [{"input": "2 1 3 2 2 2", "output": "2"}],
            "underflowCount",
            "(ops: List[int]) -> int",
            "下溢",
            "raw",
            lambda ops: _underflow(ops),
            [
                T("样例", [[2, 1, 3, 2, 2, 2]], True),
                T("无", [[1, 1, 2]], True),
                T("全下溢", [[2, 2]]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-postfix-from-infix-eval",
            "中缀经后缀再求值",
            "sa_stackq",
            "困难",
            "【CH4】对中缀 token（同前）先转后缀再求值，输出结果。",
            [{"input": f"2 {OP_ADD} 3 {OP_MUL} 4", "output": "14"}],
            "infixEval",
            "(tokens: List[int]) -> int",
            "综合",
            "raw",
            lambda tokens: ref_eval_postfix(ref_infix_to_postfix(tokens)),
            [
                T("2+3*4", [[2, OP_ADD, 3, OP_MUL, 4]], True),
                T("(2+3)*4", [[-10, 2, OP_ADD, 3, -11, OP_MUL, 4]], True),
                T("9", [[9]]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
    ]

    def _underflow(ops):
        st = []
        cnt = 0
        i = 0
        while i < len(ops):
            if ops[i] == 1:
                st.append(ops[i + 1])
                i += 2
            else:
                if not st:
                    cnt += 1
                else:
                    st.pop()
                i += 1
        return cnt

    # fix underflow problem to use helper
    for i, p in enumerate(C):
        if p.get("id") == "sa-underflow-safe-pop":
            C[i] = P(
                "sa-underflow-safe-pop",
                "空栈 Pop 次数统计",
                "sa_stackq",
                "简单",
                "【CH4 Underflow】操作：`1 x` push，`2` pop。统计空栈 pop 次数。",
                [{"input": "2 1 3 2 2 2", "output": "2"}],
                "underflowCount",
                "(ops: List[int]) -> int",
                "下溢",
                "raw",
                _underflow,
                [
                    T("样例", [[2, 1, 3, 2, 2, 2]], True),
                    T("无", [[1, 1, 2]], True),
                    T("全下溢", [[2, 2]]),
                ],
                constraints=COURSE_CONSTRAINTS,
            )
            break

    # ── CH5 string ───────────────────────────────────────────────────────────
    def ref_strlen(s):
        return len(s)

    def ref_strcmp(a, b):
        # -1 / 0 / 1
        if a < b:
            return -1
        if a > b:
            return 1
        return 0

    def ref_concat(a, b):
        return list(a) + list(b)

    def ref_substr(s, pos, length):
        # 1-based pos
        i = pos - 1
        if i < 0 or length < 0 or i >= len(s):
            return []
        return list(s[i : i + length])

    def ref_naive_index(s, t, pos):
        # 1-based; return 1-based start or 0
        if not t:
            return pos if 1 <= pos <= len(s) + 1 else 0
        start = pos - 1
        for i in range(start, len(s) - len(t) + 1):
            if list(s[i : i + len(t)]) == list(t):
                return i + 1
        return 0

    def ref_kmp_next(pat):
        # 1-indexed next as in slides; return next[1..m] as list length m (next[1]=0)
        m = len(pat)
        if m == 0:
            return []
        # use 1-based pattern p[1..m]
        p = [0] + list(pat)
        nxt = [0] * (m + 1)
        nxt[1] = 0
        j, k = 1, 0
        while j < m:
            if k == 0 or p[j] == p[k]:
                j += 1
                k += 1
                nxt[j] = k
            else:
                k = nxt[k]
        return nxt[1:]

    def ref_replace_once(s, t, v):
        # replace first non-overlap occurrence of t with v
        if not t:
            return list(s)
        s = list(s)
        n, m = len(s), len(t)
        for i in range(n - m + 1):
            if s[i : i + m] == list(t):
                return s[:i] + list(v) + s[i + m :]
        return s

    def ref_str_insert(s, pos, t):
        i = pos - 1
        i = max(0, min(i, len(s)))
        return list(s[:i]) + list(t) + list(s[i:])

    def ref_equal(a, b):
        return list(a) == list(b)

    def ref_kmp_index(s, t, pos):
        # using next
        if not t:
            return pos if pos >= 1 else 0
        nxt = [0] + ref_kmp_next(t)  # 1-based
        s = [0] + list(s)
        t = [0] + list(t)
        i, j = pos, 1
        n, m = len(s) - 1, len(t) - 1
        while i <= n and j <= m:
            if j == 0 or s[i] == t[j]:
                i += 1
                j += 1
            else:
                j = nxt[j]
        if j > m:
            return i - m
        return 0

    C += [
        P(
            "sa-strlen",
            "串长",
            "sa_string",
            "简单",
            "【CH5】字符用正整数编码。返回串长。",
            [{"input": "1 2 3", "output": "3"}],
            "strLength",
            "(s: List[int]) -> int",
            "StrLength",
            "raw",
            ref_strlen,
            [T("样例", [[1, 2, 3]], True), T("空", [[]], True), T("单", [[9]])],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-strcmp",
            "串比较",
            "sa_string",
            "简单",
            "【CH5】字典序比较两串：小于 -1，等于 0，大于 1。",
            [{"input": "1 2\n1 3", "output": "-1"}],
            "strCompare",
            "(a: List[int], b: List[int]) -> int",
            "StrCompare",
            "raw",
            ref_strcmp,
            [
                T("小", [[1, 2], [1, 3]], True),
                T("等", [[2, 2], [2, 2]], True),
                T("前缀", [[1, 2], [1, 2, 3]]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-concat",
            "串联结",
            "sa_string",
            "简单",
            "【CH5 Concat】联结 S1 与 S2。",
            [{"input": "1 2\n3 4", "output": "1 2 3 4"}],
            "strConcat",
            "(a: List[int], b: List[int]) -> List[int]",
            "Concat",
            "raw",
            ref_concat,
            [T("样例", [[1, 2], [3, 4]], True), T("空", [[], [1]], True), T("双空", [[], []])],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-substr",
            "取子串",
            "sa_string",
            "中等",
            "【CH5 SubString】1-based 起点 `pos` 与长度 `len`；非法得空。",
            [{"input": "1 2 3 4 5\n2\n3", "output": "2 3 4"}],
            "subString",
            "(s: List[int], pos: int, length: int) -> List[int]",
            "SubString",
            "raw",
            ref_substr,
            [
                T("样例", [[1, 2, 3, 4, 5], 2, 3], True),
                T("超长截断", [[1, 2], 2, 5], True),
                T("非法", [[1], 0, 1]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-naive-index",
            "朴素模式匹配 Index",
            "sa_string",
            "中等",
            "【CH5】从 1-based `pos` 起找模式 T 首次出现位置；否则 0。",
            [{"input": "1 2 3 1 2 3 1 2 3 4\n2 3\n1", "output": "2"}],
            "naiveIndex",
            "(s: List[int], t: List[int], pos: int) -> int",
            "朴素匹配",
            "raw",
            ref_naive_index,
            [
                T("样例", [[1, 2, 3, 1, 2, 3, 1, 2, 3, 4], [2, 3], 1], True),
                T("课件 Index", [[1, 2, 3, 1, 1, 2, 3, 1, 1, 1, 2, 3], [2, 3, 1], 1], True),
                T("无", [[1, 2], [9], 1]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-kmp-next",
            "KMP 的 next 数组",
            "sa_string",
            "困难",
            "【CH5 Get_next】对模式串计算课件 1-based `next`（next[1]=0），按位置 1..m 输出。",
            [{"input": "1 2 1 2 3", "output": "0 1 1 2 3"}],
            "getNext",
            "(pat: List[int]) -> List[int]",
            "next[]",
            "raw",
            ref_kmp_next,
            [
                T("样例", [[1, 2, 1, 2, 3]], True),
                T("全同", [[1, 1, 1]], True),
                T("单", [[7]]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-kmp-index",
            "KMP 匹配 Index",
            "sa_string",
            "困难",
            "【CH5 Index_KMP】用 next 从 `pos` 匹配，返回 1-based 起点或 0。",
            [{"input": "1 2 1 2 1 3\n1 2 1\n1", "output": "1"}],
            "indexKMP",
            "(s: List[int], t: List[int], pos: int) -> int",
            "KMP",
            "raw",
            ref_kmp_index,
            [
                T("样例", [[1, 2, 1, 2, 1, 3], [1, 2, 1], 1], True),
                T("后现", [[1, 1, 2, 1, 2], [1, 2], 2], True),
                T("无", [[1, 2, 3], [4], 1]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-str-replace-first",
            "子串替换（首次）",
            "sa_string",
            "中等",
            "【CH5 Replace】将 S 中首次出现的非重叠 T 换成 V。",
            [{"input": "1 2 3 2 3\n2 3\n9", "output": "1 9 2 3"}],
            "strReplace",
            "(s: List[int], t: List[int], v: List[int]) -> List[int]",
            "Replace",
            "raw",
            ref_replace_once,
            [
                T("样例", [[1, 2, 3, 2, 3], [2, 3], [9]], True),
                T("无", [[1], [2], [3]], True),
                T("整替", [[1, 2], [1, 2], [3]]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-str-insert",
            "串插入",
            "sa_string",
            "简单",
            "【CH5 StrInsert】在 1-based 位置 `pos` 前插入 T。",
            [{"input": "1 2 3\n2\n9 9", "output": "1 9 9 2 3"}],
            "strInsert",
            "(s: List[int], pos: int, t: List[int]) -> List[int]",
            "Insert",
            "raw",
            ref_str_insert,
            [
                T("样例", [[1, 2, 3], 2, [9, 9]], True),
                T("头", [[1], 1, [0]], True),
                T("尾后", [[1], 2, [2]]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-str-equal",
            "串相等",
            "sa_string",
            "简单",
            "【CH5 Equal】判断两串是否相等。",
            [{"input": "1 2\n1 2", "output": "true"}],
            "strEqual",
            "(a: List[int], b: List[int]) -> bool",
            "Equal",
            "raw",
            ref_equal,
            [T("是", [[1, 2], [1, 2]], True), T("否", [[1], [1, 2]], True), T("空", [[], []])],
            constraints=COURSE_CONSTRAINTS,
        ),
    ]

    # ── CH6 tree course-specific ─────────────────────────────────────────────
    def ref_complete_parent(i):
        # 1-based index parent
        return i // 2 if i > 1 else 0

    def ref_complete_left(i, n):
        L = 2 * i
        return L if L <= n else 0

    def ref_bst_insert_seq(vals):
        # return level-order of BST after sequential inserts
        class N:
            __slots__ = ("v", "l", "r")

            def __init__(self, v):
                self.v = v
                self.l = self.r = None

        root = None

        def ins(node, x):
            if not node:
                return N(x)
            if x < node.v:
                node.l = ins(node.l, x)
            elif x > node.v:
                node.r = ins(node.r, x)
            return node

        for x in vals:
            root = ins(root, x)

        if not root:
            return []
        out = []
        q = deque([root])
        while q:
            u = q.popleft()
            out.append(u.v)
            if u.l:
                q.append(u.l)
            if u.r:
                q.append(u.r)
        return out

    def ref_avl_bf(root):
        def height(n):
            if n is None:
                return -1
            return 1 + max(height(n.left), height(n.right))

        if root is None:
            return 0
        return height(root.left) - height(root.right)

    def ref_count_leaves(root):
        if root is None:
            return 0
        if root.left is None and root.right is None:
            return 1
        return ref_count_leaves(root.left) + ref_count_leaves(root.right)

    def ref_huffman_wpl(weights):
        if not weights:
            return 0
        h = list(weights)
        from heapq import heapify

        heapify(h)
        wpl = 0
        while len(h) > 1:
            a = heappop(h)
            b = heappop(h)
            s = a + b
            wpl += s  # each merge adds to WPL for internal
            heappush(h, s)
        return wpl

    def ref_expr_tree_inorder(postfix):
        # operands positive; ops OP_*; build tree and return inorder values (ops as codes)
        st = []
        for t in postfix:
            if t in PREC:
                r = st.pop()
                l = st.pop()
                st.append([t, l, r])
            else:
                st.append([t, None, None])
        if not st:
            return []
        out = []

        def ino(n):
            if not n:
                return
            ino(n[1])
            out.append(n[0])
            ino(n[2])

        ino(st[-1])
        return out

    def ref_bst_height_worst(n):
        return n  # skewed

    def ref_heap_parent(i):
        return (i - 1) // 2 if i > 0 else -1

    def ref_is_max_heap(a):
        n = len(a)
        for i in range(n):
            L, R = 2 * i + 1, 2 * i + 2
            if L < n and a[L] > a[i]:
                return False
            if R < n and a[R] > a[i]:
                return False
        return True

    C += [
        P(
            "sa-complete-parent",
            "完全二叉树双亲下标",
            "sa_tree",
            "简单",
            "【CH6 顺序存储】1-based 下标 `i` 的双亲；根返回 0。",
            [{"input": "5", "output": "2"}],
            "completeParent",
            "(i: int) -> int",
            "下标关系",
            "raw",
            ref_complete_parent,
            [T("5", [5], True), T("1", [1], True), T("2", [2])],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-complete-left-child",
            "完全二叉树左孩子",
            "sa_tree",
            "简单",
            "【CH6】总结点 n、下标 i（1-based），返回左孩子下标；无则 0。",
            [{"input": "3\n7", "output": "6"}],
            "completeLeft",
            "(i: int, n: int) -> int",
            "左孩子",
            "raw",
            ref_complete_left,
            [T("样例", [3, 7], True), T("无", [4, 5], True), T("根", [1, 3])],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-bst-insert-level",
            "BST 依次插入后的层序",
            "sa_tree",
            "中等",
            "【CH6 BST Insert】按输入顺序插入空树，输出层序值（不含 NULL）。",
            [{"input": "5 3 7 2", "output": "5 3 7 2"}],
            "bstInsertLevel",
            "(vals: List[int]) -> List[int]",
            "BST 插入",
            "raw",
            ref_bst_insert_seq,
            [
                T("样例", [[5, 3, 7, 2]], True),
                T("升序链", [[1, 2, 3]], True),
                T("单", [[9]]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-avl-balance-factor",
            "AVL 平衡因子（根）",
            "sa_tree",
            "中等",
            "【CH6 AVL】层序树（含 NULL），空树高度 -1，返回根的平衡因子 hl-hr。",
            [{"input": "1 2 NULL", "output": "1"}],
            "avlBF",
            "(root: Optional[TreeNode]) -> int",
            "平衡因子",
            "value",
            ref_avl_bf,
            [
                T("左倾", [[1, 2, None]], True),
                T("平衡", [[1, 2, 3]], True),
                T("空", [[]]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-huffman-wpl",
            "Huffman 带权路径长 WPL",
            "sa_tree",
            "中等",
            "【CH6 Huffman】给定正权值，按 Huffman 算法构造，返回 WPL（内部结点权值和累加定义）。",
            [{"input": "1 2 3 4", "output": "19"}],
            "huffmanWPL",
            "(weights: List[int]) -> int",
            "WPL",
            "raw",
            ref_huffman_wpl,
            [
                T("样例", [[1, 2, 3, 4]], True),
                T("两叶", [[1, 1]], True),
                T("单", [[5]]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-expr-tree-inorder",
            "后缀建表达式树再中序",
            "sa_tree",
            "困难",
            "【CH6 Expression Tree】后缀 token（运算符编码同栈章）建树，输出中序遍历值序列。",
            [{"input": f"1 2 {OP_ADD} 3 {OP_MUL}", "output": f"1 {OP_ADD} 2 {OP_MUL} 3"}],
            "exprInorder",
            "(postfix: List[int]) -> List[int]",
            "表达式树",
            "raw",
            ref_expr_tree_inorder,
            [
                T("样例", [[1, 2, OP_ADD, 3, OP_MUL]], True),
                T("单", [[5]], True),
                T("减", [[9, 4, OP_SUB]]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-bst-worst-height",
            "BST 最坏高度",
            "sa_tree",
            "简单",
            "【CH6】将 1..n 按升序插入 BST，高度（边数）为 n-1；本题约定返回结点数 n（课件「高度可为 N」量级）。输入 n，输出 n。",
            [{"input": "7", "output": "7"}],
            "bstWorstHeight",
            "(n: int) -> int",
            "最坏形态",
            "raw",
            ref_bst_height_worst,
            [T("7", [7], True), T("1", [1], True), T("2", [2])],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-heap-parent-index",
            "堆的双亲下标（0-based）",
            "sa_tree",
            "简单",
            "【CH6 优先队列/堆】0-based 下标 i 的双亲；根返回 -1。",
            [{"input": "5", "output": "2"}],
            "heapParent",
            "(i: int) -> int",
            "堆下标",
            "raw",
            ref_heap_parent,
            [T("5", [5], True), T("0", [0], True), T("1", [1])],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-is-max-heap",
            "判定最大堆",
            "sa_tree",
            "中等",
            "【CH6】判断数组是否满足最大堆序。",
            [{"input": "10 7 8 3", "output": "true"}],
            "isMaxHeap",
            "(a: List[int]) -> bool",
            "堆序",
            "raw",
            ref_is_max_heap,
            [
                T("是", [[10, 7, 8, 3]], True),
                T("否", [[1, 2, 3]], True),
                T("单", [[1]]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-tree-leaf-count-level",
            "层序树叶子数",
            "sa_tree",
            "简单",
            "【CH6】层序（含 NULL）统计叶子结点数。",
            [{"input": "1 2 3", "output": "2"}],
            "countLeaves",
            "(root: Optional[TreeNode]) -> int",
            "叶子",
            "value",
            ref_count_leaves,
            [
                T("满", [[1, 2, 3]], True),
                T("链", [[1, 2, None, 3]], True),
                T("空", [[]]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
    ]

    # ── CH7 graph ────────────────────────────────────────────────────────────
    def ref_topo(n, edges):
        g = [[] for _ in range(n)]
        indeg = [0] * n
        for a, b in edges:  # edge b->a means b before a? use u->v as prerequisite order u then v
            u, v = a, b
            g[u].append(v)
            indeg[v] += 1
        q = deque(i for i in range(n) if indeg[i] == 0)
        out = []
        while q:
            u = q.popleft()
            out.append(u)
            for v in sorted(g[u]):
                indeg[v] -= 1
                if indeg[v] == 0:
                    q.append(v)
        return out if len(out) == n else []

    def ref_dijkstra(n, edges, s):
        g = [[] for _ in range(n)]
        for u, v, w in edges:
            g[u].append((v, w))
        dist = [10**18] * n
        dist[s] = 0
        h = [(0, s)]
        while h:
            d, u = heappop(h)
            if d != dist[u]:
                continue
            for v, w in g[u]:
                nd = d + w
                if nd < dist[v]:
                    dist[v] = nd
                    heappush(h, (nd, v))
        return [-1 if x >= 10**18 else x for x in dist]

    def ref_prim(n, edges):
        g = [[] for _ in range(n)]
        for u, v, w in edges:
            g[u].append((v, w))
            g[v].append((u, w))
        seen = [False] * n
        h = [(0, 0)]
        total = 0
        cnt = 0
        while h and cnt < n:
            w, u = heappop(h)
            if seen[u]:
                continue
            seen[u] = True
            total += w
            cnt += 1
            for v, ww in g[u]:
                if not seen[v]:
                    heappush(h, (ww, v))
        return total if cnt == n else -1

    def ref_kruskal(n, edges):
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        edges = sorted(edges, key=lambda e: e[2])
        total = 0
        used = 0
        for u, v, w in edges:
            pu, pv = find(u), find(v)
            if pu != pv:
                parent[pu] = pv
                total += w
                used += 1
                if used == n - 1:
                    break
        return total if used == n - 1 else -1

    def ref_adj_matrix_degree(mat):
        # undirected: degree of each vertex
        n = len(mat)
        return [sum(1 for j in range(n) if mat[i][j]) for i in range(n)]

    def ref_bfs_layers(n, start, edges):
        g = [[] for _ in range(n)]
        for u, v in edges:
            g[u].append(v)
            g[v].append(u)
        for adj in g:
            adj.sort()
        dist = [-1] * n
        dist[start] = 0
        q = deque([start])
        while q:
            u = q.popleft()
            for v in g[u]:
                if dist[v] < 0:
                    dist[v] = dist[u] + 1
                    q.append(v)
        return dist

    def ref_has_cycle_undirected(n, edges):
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for u, v in edges:
            pu, pv = find(u), find(v)
            if pu == pv:
                return True
            parent[pu] = pv
        return False

    def ref_dfs_finish_order(n, start, edges):
        g = [[] for _ in range(n)]
        for u, v in edges:
            g[u].append(v)
            g[v].append(u)
        for adj in g:
            adj.sort()
        seen = [False] * n
        order = []

        def dfs(u):
            seen[u] = True
            for v in g[u]:
                if not seen[v]:
                    dfs(v)
            order.append(u)

        dfs(start)
        return order

    C += [
        P(
            "sa-topo-sort",
            "拓扑排序（入度法）",
            "sa_graph",
            "中等",
            "【CH7 Topological Sort】n 点有向边 u→v（u 先于 v）。输出一种拓扑序（同入度时取编号小者）；有环输出空。",
            [{"input": "4\n0 1\n0 2\n1 3\n2 3\n", "output": "0 1 2 3"}],
            "topoSort",
            "(n: int, edges: List[List[int]]) -> List[int]",
            "拓扑",
            "raw",
            ref_topo,
            [
                T("DAG", [4, [[0, 1], [0, 2], [1, 3], [2, 3]]], True),
                T("环", [2, [[0, 1], [1, 0]]], True),
                T("单", [1, []]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-dijkstra-dist",
            "Dijkstra 单源距离",
            "sa_graph",
            "中等",
            "【CH7 Dijkstra】n 点，有向带权边 u v w，源 s。输出到 0..n-1 的距离，不可达 -1。",
            [{"input": "3\n0 1 1\n0 2 4\n1 2 2\n\n0", "output": "0 1 3"}],
            "dijkstra",
            "(n: int, edges: List[List[int]], s: int) -> List[int]",
            "Dijkstra",
            "raw",
            ref_dijkstra,
            [
                T("样例", [3, [[0, 1, 1], [0, 2, 4], [1, 2, 2]], 0], True),
                T("不可达", [2, [[0, 1, 1]], 1], True),
                T("单点", [1, [], 0]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-prim-mst-weight",
            "Prim 最小生成树权",
            "sa_graph",
            "中等",
            "【CH7 Prim】无向带权连通图，从 0 开始 Prim，返回 MST 总权；不连通 -1。",
            [{"input": "4\n0 1 1\n0 2 4\n1 2 2\n1 3 6\n2 3 3\n", "output": "6"}],
            "primMST",
            "(n: int, edges: List[List[int]]) -> int",
            "Prim",
            "raw",
            ref_prim,
            [
                T("样例", [4, [[0, 1, 1], [0, 2, 4], [1, 2, 2], [1, 3, 6], [2, 3, 3]]], True),
                T("三角", [3, [[0, 1, 1], [1, 2, 1], [0, 2, 3]]], True),
                T("不连通", [3, [[0, 1, 1]]]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-kruskal-mst-weight",
            "Kruskal 最小生成树权",
            "sa_graph",
            "中等",
            "【CH7 Kruskal】同上，Kruskal 求 MST 总权。",
            [{"input": "4\n0 1 1\n0 2 4\n1 2 2\n1 3 6\n2 3 3\n", "output": "6"}],
            "kruskalMST",
            "(n: int, edges: List[List[int]]) -> int",
            "Kruskal",
            "raw",
            ref_kruskal,
            [
                T("样例", [4, [[0, 1, 1], [0, 2, 4], [1, 2, 2], [1, 3, 6], [2, 3, 3]]], True),
                T("两边", [3, [[0, 1, 2], [1, 2, 2], [0, 2, 2]]], True),
                T("不连通", [3, [[0, 1, 1]]]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-adj-degree",
            "邻接矩阵求度",
            "sa_graph",
            "简单",
            "【CH7 邻接矩阵】无向图 0/1 矩阵，输出每个顶点的度。",
            [{"input": "0 1 1\n1 0 0\n1 0 0\n", "output": "2 1 1"}],
            "adjDegree",
            "(mat: List[List[int]]) -> List[int]",
            "度",
            "raw",
            ref_adj_matrix_degree,
            [
                T("样例", [[[0, 1, 1], [1, 0, 0], [1, 0, 0]]], True),
                T("空边", [[[0, 0], [0, 0]]], True),
                T("单", [[[0]]]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-bfs-dist-layers",
            "BFS 层次距离",
            "sa_graph",
            "中等",
            "【CH7 BFS】无向图，输出从 start 到各点的层距，不可达 -1。",
            [{"input": "4\n0\n0 1\n0 2\n1 3\n", "output": "0 1 1 2"}],
            "bfsDist",
            "(n: int, start: int, edges: List[List[int]]) -> List[int]",
            "BFS 层",
            "raw",
            ref_bfs_layers,
            [
                T("样例", [4, 0, [[0, 1], [0, 2], [1, 3]]], True),
                T("孤立", [2, 0, []], True),
                T("自", [1, 0, []]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-undirected-cycle",
            "无向图是否有环",
            "sa_graph",
            "中等",
            "【CH7】并查集判定无向图是否含环。",
            [{"input": "3\n0 1\n1 2\n0 2\n", "output": "true"}],
            "hasCycle",
            "(n: int, edges: List[List[int]]) -> bool",
            "环",
            "raw",
            ref_has_cycle_undirected,
            [
                T("有环", [3, [[0, 1], [1, 2], [0, 2]]], True),
                T("树", [3, [[0, 1], [1, 2]]], True),
                T("空", [1, []]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-dfs-postorder",
            "DFS 完成序（后序）",
            "sa_graph",
            "中等",
            "【CH7 DFS】无向图，邻接升序，从 start DFS，输出完成（离开）次序。",
            [{"input": "3\n0\n0 1\n0 2\n", "output": "1 2 0"}],
            "dfsPost",
            "(n: int, start: int, edges: List[List[int]]) -> List[int]",
            "DFS 后序",
            "raw",
            ref_dfs_finish_order,
            [
                T("星", [3, 0, [[0, 1], [0, 2]]], True),
                T("链", [3, 0, [[0, 1], [1, 2]]], True),
                T("单", [1, 0, []]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-edge-count-from-matrix",
            "邻接矩阵边数（无向）",
            "sa_graph",
            "简单",
            "【CH7】无向图 0/1 对称矩阵，返回边数（上三角计数）。",
            [{"input": "0 1 0\n1 0 1\n0 1 0\n", "output": "2"}],
            "edgeCount",
            "(mat: List[List[int]]) -> int",
            "边数",
            "raw",
            lambda mat: sum(mat[i][j] for i in range(len(mat)) for j in range(i + 1, len(mat))),
            [
                T("样例", [[[0, 1, 0], [1, 0, 1], [0, 1, 0]]], True),
                T("无", [[[0]]], True),
                T("完全3", [[[0, 1, 1], [1, 0, 1], [1, 1, 0]]]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-dag-check",
            "是否为 DAG（可拓扑）",
            "sa_graph",
            "中等",
            "【CH7】有向图能否拓扑（无环）——能则 true。边 u→v。",
            [{"input": "3\n0 1\n1 2\n", "output": "true"}],
            "isDAG",
            "(n: int, edges: List[List[int]]) -> bool",
            "DAG",
            "raw",
            lambda n, edges: len(ref_topo(n, edges)) == n,
            [
                T("是", [3, [[0, 1], [1, 2]]], True),
                T("否", [2, [[0, 1], [1, 0]]], True),
                T("空", [1, []]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
    ]

    # ── params / references ──────────────────────────────────────────────────
    def ref_swap_by_value(a, b):
        # after fake swap by value, originals unchanged — return a b
        return [a, b]

    def ref_swap_by_ref(a, b):
        return [b, a]

    def ref_ptr_assign_effect(x, y):
        # *p = y where p=&x → x becomes y
        return y

    def ref_ref_alias_ops(a, delta):
        # ra is alias of a; ra += delta → a+delta
        return a + delta

    def ref_cannot_rebind():
        # pedagogical: return 1 meaning "reference cannot rebind" as true flag
        return 1

    def ref_pass_array_modify(nums, idx, val):
        a = list(nums)
        if 0 <= idx < len(a):
            a[idx] = val
        return a

    C += [
        P(
            "sa-swap-by-value",
            "传值 Swap 后的结果",
            "sa_params",
            "简单",
            "【引用和参数传递】值传递的 Swap 不能改实参。输入 a b，输出仍为 a b。",
            [{"input": "3\n5", "output": "3 5"}],
            "swapByValue",
            "(a: int, b: int) -> List[int]",
            "传值",
            "raw",
            ref_swap_by_value,
            [T("样例", [3, 5], True), T("同", [1, 1], True), T("负", [-1, 2])],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-swap-by-ref",
            "传引用/传址 Swap 结果",
            "sa_params",
            "简单",
            "【引用传递】引用或指针 Swap 成功。输入 a b，输出交换后 b a。",
            [{"input": "3\n5", "output": "5 3"}],
            "swapByRef",
            "(a: int, b: int) -> List[int]",
            "传引用",
            "raw",
            ref_swap_by_ref,
            [T("样例", [3, 5], True), T("同", [2, 2], True), T("0", [0, 9])],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-pointer-write",
            "通过指针写入",
            "sa_params",
            "简单",
            "【指针】`*p=y` 且 `p=&x`。输入 x y，返回写入后的 x。",
            [{"input": "1\n8", "output": "8"}],
            "ptrWrite",
            "(x: int, y: int) -> int",
            "传址写",
            "raw",
            ref_ptr_assign_effect,
            [T("样例", [1, 8], True), T("同", [4, 4], True), T("0", [0, 1])],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-ref-alias-add",
            "引用别名累加",
            "sa_params",
            "简单",
            "【引用】`ra` 是 `a` 的别名，执行 `ra+=delta` 后返回 a。",
            [{"input": "10\n5", "output": "15"}],
            "refAdd",
            "(a: int, delta: int) -> int",
            "别名",
            "raw",
            ref_ref_alias_ops,
            [T("样例", [10, 5], True), T("0", [3, 0], True), T("负", [5, -2])],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-ref-no-rebind-flag",
            "引用不可重绑定（哨兵）",
            "sa_params",
            "简单",
            "【课件】引用初始化后不能改绑。本题无定输出 1 表示该性质成立（无输入）。输入任意一行整数忽略，输出 1。",
            [{"input": "0", "output": "1"}],
            "refNoRebind",
            "(x: int) -> int",
            "不可重绑",
            "raw",
            lambda x: 1,
            [T("0", [0], True), T("9", [9], True), T("-1", [-1])],
            constraints=COURSE_CONSTRAINTS,
        ),
        P(
            "sa-array-param-write",
            "数组参数可被修改",
            "sa_params",
            "简单",
            "【数组名作指针】函数通过下标写 `nums[idx]=val`，返回修改后数组。",
            [{"input": "1 2 3\n1\n9", "output": "1 9 3"}],
            "arrayParamWrite",
            "(nums: List[int], idx: int, val: int) -> List[int]",
            "数组传址",
            "raw",
            ref_pass_array_modify,
            [
                T("样例", [[1, 2, 3], 1, 9], True),
                T("越界忽略", [[1], 5, 2], True),
                T("头", [[4, 5], 0, 0]),
            ],
            constraints=COURSE_CONSTRAINTS,
        ),
    ]

    return C
