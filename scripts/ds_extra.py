#!/usr/bin/env python3
"""Extra data-structure problems (non-tree) for TreePath / 枝径."""
from __future__ import annotations

from collections import Counter, deque
from heapq import heappop, heappush, nlargest, nsmallest
from typing import Any, Callable, Optional

DS_CONSTRAINTS = [
    "请编写完整 C 程序（含 main）；不要依赖判题替你写入口",
    "输入为数字与 NULL 的空格/换行分隔 token（无方括号）",
    "注意空输入与边界；节点/元素规模以题面样例量级为准",
]


def add_ds_problems(P: Callable, T: Callable) -> list[dict]:
    """Return ~80 problems across arrays/stack/queue/list/hash/heap/graph/sorting."""
    C: list[dict] = []

    # ── refs: arrays ─────────────────────────────────────────────────────────
    def ref_two_sum(nums, target):
        seen = {}
        for i, x in enumerate(nums):
            if target - x in seen:
                a, b = seen[target - x], i
                return [a, b] if a < b else [b, a]
            seen[x] = i
        return []

    def ref_max_subarray(nums):
        best = cur = nums[0]
        for x in nums[1:]:
            cur = max(x, cur + x)
            best = max(best, cur)
        return best

    def ref_move_zeroes(nums):
        a = list(nums)
        j = 0
        for x in a:
            if x != 0:
                a[j] = x
                j += 1
        for i in range(j, len(a)):
            a[i] = 0
        return a

    def ref_remove_duplicates(nums):
        if not nums:
            return 0
        # return new length; judge compares length for this problem
        w = 1
        for i in range(1, len(nums)):
            if nums[i] != nums[w - 1]:
                nums[w] = nums[i]
                w += 1
        return w

    def ref_rotate(nums, k):
        a = list(nums)
        n = len(a)
        if n == 0:
            return a
        k %= n
        return a[-k:] + a[:-k] if k else a

    def ref_product_except_self(nums):
        n = len(nums)
        out = [1] * n
        left = 1
        for i in range(n):
            out[i] = left
            left *= nums[i]
        right = 1
        for i in range(n - 1, -1, -1):
            out[i] *= right
            right *= nums[i]
        return out

    def ref_majority(nums):
        cand = None
        cnt = 0
        for x in nums:
            if cnt == 0:
                cand = x
            cnt += 1 if x == cand else -1
        return cand

    def ref_missing_number(nums):
        n = len(nums)
        return n * (n + 1) // 2 - sum(nums)

    def ref_contains_duplicate(nums):
        return len(nums) != len(set(nums))

    def ref_intersect(a, b):
        ca, cb = Counter(a), Counter(b)
        out = []
        for k in ca:
            out.extend([k] * min(ca[k], cb[k]))
        out.sort()
        return out

    # ── refs: stack ──────────────────────────────────────────────────────────
    def ref_is_valid_parens(s_codes):
        # s_codes: list of ints 1='(' 2=')' 3='[' 4=']' 5='{' 6='}'
        mp = {2: 1, 4: 3, 6: 5}
        st = []
        for c in s_codes:
            if c in (1, 3, 5):
                st.append(c)
            else:
                if not st or st[-1] != mp.get(c):
                    return False
                st.pop()
        return not st

    def ref_daily_temperatures(t):
        n = len(t)
        ans = [0] * n
        st = []
        for i, x in enumerate(t):
            while st and t[st[-1]] < x:
                j = st.pop()
                ans[j] = i - j
            st.append(i)
        return ans

    def ref_next_greater(nums):
        n = len(nums)
        ans = [-1] * n
        st = []
        for i in range(2 * n):
            x = nums[i % n]
            while st and nums[st[-1]] < x:
                ans[st.pop()] = x
            if i < n:
                st.append(i)
        return ans

    def ref_eval_rpn(tokens):
        # tokens as ints; operators encoded: -1 +, -2 -, -3 *, -4 /
        st = []
        for t in tokens:
            if t >= 0 or (t < -4):  # operands can be negative numbers >= -1000 except ops
                # Use sentinel: ops are only -1..-4 when preceded... Actually use large sentinels
                pass
        # Better encoding: operands as-is; ops as 10**9+{1,2,3,4}
        st = []
        OP_ADD, OP_SUB, OP_MUL, OP_DIV = 10**9 + 1, 10**9 + 2, 10**9 + 3, 10**9 + 4
        for t in tokens:
            if t in (OP_ADD, OP_SUB, OP_MUL, OP_DIV):
                b, a = st.pop(), st.pop()
                if t == OP_ADD:
                    st.append(a + b)
                elif t == OP_SUB:
                    st.append(a - b)
                elif t == OP_MUL:
                    st.append(a * b)
                else:
                    # truncate toward zero
                    st.append(int(a / b))
            else:
                st.append(t)
        return st[-1]

    def ref_largest_rectangle(heights):
        st = [-1]
        best = 0
        h = list(heights) + [0]
        for i, x in enumerate(h):
            while st[-1] != -1 and h[st[-1]] > x:
                height = h[st.pop()]
                best = max(best, height * (i - st[-1] - 1))
            st.append(i)
        return best

    def ref_simplify_path(parts):
        # parts: tokens where 0=., 1=.., positive = folder id
        st = []
        for p in parts:
            if p == 0:
                continue
            if p == 1:
                if st:
                    st.pop()
            else:
                st.append(p)
        return st

    def ref_asteroid(asts):
        st = []
        for a in asts:
            while st and a < 0 < st[-1]:
                if st[-1] < -a:
                    st.pop()
                    continue
                if st[-1] == -a:
                    st.pop()
                break
            else:
                st.append(a)
        return st

    def ref_decode_count(s_codes):
        # run-length: alternating count, value → expand length
        out = 0
        i = 0
        while i + 1 < len(s_codes):
            out += s_codes[i]
            i += 2
        return out

    def ref_min_remove_valid(s_codes):
        # 1=( 2=) → return remaining sequence after min removal
        st = []
        remove = set()
        for i, c in enumerate(s_codes):
            if c == 1:
                st.append(i)
            elif c == 2:
                if st:
                    st.pop()
                else:
                    remove.add(i)
        remove.update(st)
        return [c for i, c in enumerate(s_codes) if i not in remove]

    def ref_trap_rain(height):
        if not height:
            return 0
        l, r = 0, len(height) - 1
        lm = rm = water = 0
        while l < r:
            if height[l] < height[r]:
                lm = max(lm, height[l])
                water += lm - height[l]
                l += 1
            else:
                rm = max(rm, height[r])
                water += rm - height[r]
                r -= 1
        return water

    # ── refs: queue ──────────────────────────────────────────────────────────
    def ref_recent_counter(times):
        # process queries: for each t, count how many in (t-3000, t]
        q = deque()
        out = []
        for t in times:
            q.append(t)
            while q and q[0] < t - 3000:
                q.popleft()
            out.append(len(q))
        return out

    def ref_moving_avg(size, vals):
        q = deque()
        s = 0
        out = []
        for v in vals:
            q.append(v)
            s += v
            if len(q) > size:
                s -= q.popleft()
            out.append(s // len(q))  # floor avg as int
        return out

    def ref_first_unique(nums):
        # stream: return first unique so far after each insert; -1 if none
        # For simplicity: after processing all, return first unique in order
        cnt = Counter(nums)
        for x in nums:
            if cnt[x] == 1:
                return x
        return -1

    def ref_queue_stack_ops(ops):
        # ops: pairs (op, val) flattened; op 1=push, 2=pop→collect pops
        # Use two queues to simulate stack push/pop; return pop results
        q = deque()
        out = []
        i = 0
        while i < len(ops):
            op = ops[i]
            if op == 1:
                q.append(ops[i + 1])
                # rotate to make back the "top" for stack-from-queue
                for _ in range(len(q) - 1):
                    q.append(q.popleft())
                i += 2
            else:
                out.append(q.popleft() if q else -1)
                i += 1
        return out

    def ref_dota2_senate(senate):
        # 1=R 2=D
        r = deque(i for i, x in enumerate(senate) if x == 1)
        d = deque(i for i, x in enumerate(senate) if x == 2)
        n = len(senate)
        while r and d:
            ri, di = r.popleft(), d.popleft()
            if ri < di:
                r.append(ri + n)
            else:
                d.append(di + n)
        return 1 if r else 2

    def ref_max_sliding_window(nums, k):
        q = deque()
        out = []
        for i, x in enumerate(nums):
            while q and q[0] <= i - k:
                q.popleft()
            while q and nums[q[-1]] <= x:
                q.pop()
            q.append(i)
            if i >= k - 1:
                out.append(nums[q[0]])
        return out

    def ref_time_needed_buy(tickets, k):
        t = 0
        tickets = list(tickets)
        while tickets[k] > 0:
            for i in range(len(tickets)):
                if tickets[i] > 0:
                    tickets[i] -= 1
                    t += 1
                    if i == k and tickets[k] == 0:
                        return t
        return t

    def ref_predict_party(senate):
        return ref_dota2_senate(senate)

    def _circular_sim(k, ops):
        q = deque()
        for x in ops:
            if x == -1:
                if q:
                    q.popleft()
            else:
                if len(q) < k:
                    q.append(x)
        return list(q)

    # ── refs: linked list (as arrays) ────────────────────────────────────────
    def ref_reverse_list(a):
        return list(reversed(a))

    def ref_merge_two(a, b):
        i = j = 0
        out = []
        while i < len(a) and j < len(b):
            if a[i] <= b[j]:
                out.append(a[i])
                i += 1
            else:
                out.append(b[j])
                j += 1
        out.extend(a[i:])
        out.extend(b[j:])
        return out

    def ref_has_cycle_vals(a, pos):
        # If pos>=0, last node connects to index pos — detect cycle conceptually
        # For array I/O we can't return cycle structure; return 1/0 whether pos>=0 and a
        if not a:
            return False
        return pos >= 0

    def ref_middle(a):
        return a[len(a) // 2 :]

    def ref_remove_nth(a, n):
        # remove nth from end
        idx = len(a) - n
        return a[:idx] + a[idx + 1 :]

    def ref_palindrome_list(a):
        return a == a[::-1]

    def ref_get_intersection(a, b, skip_a, skip_b):
        # Classic: two lists with shared suffix starting after skips
        # Build: a[:skipA]+common, b[:skipB]+common — return common start value or -1
        # We pass common as the shared part in tests via constructing expected
        # Simpler problem: given a, b return whether they share any value (multiset) — weak
        # Better: return intersection node value using skip indices into concatenated model
        if skip_a < 0 or skip_b < 0:
            return -1
        # Assume a[skip_a:] should equal b[skip_b:] when intersecting
        if a[skip_a:] == b[skip_b:] and a[skip_a:]:
            return a[skip_a]
        return -1

    def ref_add_two(a, b):
        # digits least-significant first
        i = j = carry = 0
        out = []
        while i < len(a) or j < len(b) or carry:
            x = a[i] if i < len(a) else 0
            y = b[j] if j < len(b) else 0
            s = x + y + carry
            out.append(s % 10)
            carry = s // 10
            i += 1
            j += 1
        return out

    def ref_swap_pairs(a):
        out = list(a)
        for i in range(0, len(out) - 1, 2):
            out[i], out[i + 1] = out[i + 1], out[i]
        return out

    def ref_delete_duplicates(a):
        if not a:
            return []
        out = [a[0]]
        for x in a[1:]:
            if x != out[-1]:
                out.append(x)
        return out

    # ── refs: hash ───────────────────────────────────────────────────────────
    def ref_group_anagram_ids(words):
        # words as list of letter-id sequences flattened with -1 separators → too heavy
        # Instead: each "word" is a sorted fingerprint int list in tests as separate?
        # Simpler: given nums, return frequency of each distinct sorted by key
        cnt = Counter(words)
        keys = sorted(cnt)
        out = []
        for k in keys:
            out.extend([k, cnt[k]])
        return out

    def ref_top_k_frequent(nums, k):
        cnt = Counter(nums)
        return [x for x, _ in cnt.most_common(k)]

    def ref_longest_consecutive(nums):
        s = set(nums)
        best = 0
        for x in s:
            if x - 1 not in s:
                y = x
                while y in s:
                    y += 1
                best = max(best, y - x)
        return best

    def ref_subarray_sum(nums, k):
        pref = 0
        seen = {0: 1}
        ans = 0
        for x in nums:
            pref += x
            ans += seen.get(pref - k, 0)
            seen[pref] = seen.get(pref, 0) + 1
        return ans

    def ref_four_sum_count(a, b, c, d):
        ab = Counter(x + y for x in a for y in b)
        return sum(ab[-u - v] for u in c for v in d)

    def ref_is_isomorphic(a, b):
        if len(a) != len(b):
            return False
        ab, ba = {}, {}
        for x, y in zip(a, b):
            if ab.get(x, y) != y or ba.get(y, x) != x:
                return False
            ab[x] = y
            ba[y] = x
        return True

    def ref_word_pattern(pattern, s):
        # pattern ints, s ints (word ids)
        return ref_is_isomorphic(pattern, s)

    def ref_find_disappeared(nums):
        n = len(nums)
        s = set(nums)
        return [i for i in range(1, n + 1) if i not in s]

    def ref_single_number(nums):
        x = 0
        for v in nums:
            x ^= v
        return x

    def ref_happy_number(n):
        seen = set()
        while n != 1 and n not in seen:
            seen.add(n)
            n = sum(int(d) ** 2 for d in str(n))
        return n == 1

    # ── refs: heap ───────────────────────────────────────────────────────────
    def ref_find_kth_largest(nums, k):
        return nlargest(k, nums)[-1]

    def ref_k_smallest_pairs(a, b, k):
        if not a or not b:
            return []
        h = []
        for i, x in enumerate(a[:k]):
            heappush(h, (x + b[0], i, 0))
        out = []
        while h and len(out) < k:
            s, i, j = heappop(h)
            out.extend([a[i], b[j]])
            if j + 1 < len(b):
                heappush(h, (a[i] + b[j + 1], i, j + 1))
        return out

    def ref_merge_k_lists(lists):
        # lists: matrix of sorted lists
        h = []
        for i, lst in enumerate(lists):
            if lst:
                heappush(h, (lst[0], i, 0))
        out = []
        while h:
            v, i, j = heappop(h)
            out.append(v)
            if j + 1 < len(lists[i]):
                heappush(h, (lists[i][j + 1], i, j + 1))
        return out

    def ref_last_stone(stones):
        h = [-s for s in stones]
        # heapify
        from heapq import heapify

        heapify(h)
        while len(h) > 1:
            a = -heappop(h)
            b = -heappop(h)
            if a != b:
                heappush(h, -(a - b))
        return -h[0] if h else 0

    def ref_k_closest(points, k):
        # points flat x y x y...; return k closest to origin flattened, sorted by dist then x then y
        pts = [(points[i], points[i + 1]) for i in range(0, len(points), 2)]
        pts.sort(key=lambda p: (p[0] * p[0] + p[1] * p[1], p[0], p[1]))
        out = []
        for x, y in pts[:k]:
            out.extend([x, y])
        return out

    def ref_reorganize_possible(nums):
        # Whether nums can be rearranged so no two adjacent are equal.
        if not nums:
            return True
        cnt = Counter(nums)
        return max(cnt.values()) <= (len(nums) + 1) // 2

    def ref_median_stream(nums):
        # after each insert, append floor median
        lo, hi = [], []  # maxheap, minheap
        out = []
        for x in nums:
            heappush(lo, -x)
            heappush(hi, -heappop(lo))
            if len(hi) > len(lo):
                heappush(lo, -heappop(hi))
            if len(lo) == len(hi):
                out.append((-lo[0] + hi[0]) // 2)
            else:
                out.append(-lo[0])
        return out

    def ref_task_idle(tasks, n):
        cnt = Counter(tasks)
        mx = max(cnt.values())
        mx_count = sum(1 for v in cnt.values() if v == mx)
        return max(len(tasks), (mx - 1) * (n + 1) + mx_count)

    # ── refs: graph ──────────────────────────────────────────────────────────
    def ref_bfs_order(n, start, edges):
        g = [[] for _ in range(n)]
        for u, v in edges:
            g[u].append(v)
            g[v].append(u)
        for adj in g:
            adj.sort()
        seen = [False] * n
        q = deque([start])
        seen[start] = True
        order = []
        while q:
            u = q.popleft()
            order.append(u)
            for v in g[u]:
                if not seen[v]:
                    seen[v] = True
                    q.append(v)
        return order

    def ref_dfs_order(n, start, edges):
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
            order.append(u)
            for v in g[u]:
                if not seen[v]:
                    dfs(v)

        dfs(start)
        return order

    def ref_num_islands(grid):
        if not grid:
            return 0
        m, n = len(grid), len(grid[0])
        seen = [[False] * n for _ in range(m)]

        def dfs(i, j):
            if i < 0 or j < 0 or i >= m or j >= n or seen[i][j] or grid[i][j] == 0:
                return
            seen[i][j] = True
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                dfs(i + di, j + dj)

        ans = 0
        for i in range(m):
            for j in range(n):
                if grid[i][j] == 1 and not seen[i][j]:
                    ans += 1
                    dfs(i, j)
        return ans

    def ref_can_finish(n, edges):
        g = [[] for _ in range(n)]
        indeg = [0] * n
        for a, b in edges:  # b -> a (b prerequisite of a) LeetCode style [a,b] means b first
            g[b].append(a)
            indeg[a] += 1
        q = deque(i for i in range(n) if indeg[i] == 0)
        taken = 0
        while q:
            u = q.popleft()
            taken += 1
            for v in g[u]:
                indeg[v] -= 1
                if indeg[v] == 0:
                    q.append(v)
        return taken == n

    def ref_shortest_unweighted(n, start, target, edges):
        g = [[] for _ in range(n)]
        for u, v in edges:
            g[u].append(v)
            g[v].append(u)
        dist = [-1] * n
        dist[start] = 0
        q = deque([start])
        while q:
            u = q.popleft()
            if u == target:
                return dist[u]
            for v in g[u]:
                if dist[v] < 0:
                    dist[v] = dist[u] + 1
                    q.append(v)
        return -1

    def ref_connected_components(n, edges):
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for u, v in edges:
            pu, pv = find(u), find(v)
            if pu != pv:
                parent[pu] = pv
        return len({find(i) for i in range(n)})

    def ref_oranges_rotting(grid):
        if not grid:
            return -1
        m, n = len(grid), len(grid[0])
        q = deque()
        fresh = 0
        for i in range(m):
            for j in range(n):
                if grid[i][j] == 2:
                    q.append((i, j, 0))
                elif grid[i][j] == 1:
                    fresh += 1
        ans = 0
        while q:
            i, j, t = q.popleft()
            ans = t
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ni, nj = i + di, j + dj
                if 0 <= ni < m and 0 <= nj < n and grid[ni][nj] == 1:
                    grid[ni][nj] = 2
                    fresh -= 1
                    q.append((ni, nj, t + 1))
        return ans if fresh == 0 else -1

    def ref_valid_path(n, edges, source, destination):
        g = [[] for _ in range(n)]
        for u, v in edges:
            g[u].append(v)
            g[v].append(u)
        seen = [False] * n
        q = deque([source])
        seen[source] = True
        while q:
            u = q.popleft()
            if u == destination:
                return True
            for v in g[u]:
                if not seen[v]:
                    seen[v] = True
                    q.append(v)
        return False

    def ref_flood_fill(grid, sr, sc, color):
        m, n = len(grid), len(grid[0])
        src = grid[sr][sc]
        if src == color:
            return [row[:] for row in grid]
        q = deque([(sr, sc)])
        grid = [row[:] for row in grid]
        grid[sr][sc] = color
        while q:
            i, j = q.popleft()
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ni, nj = i + di, j + dj
                if 0 <= ni < m and 0 <= nj < n and grid[ni][nj] == src:
                    grid[ni][nj] = color
                    q.append((ni, nj))
        return grid

    def ref_network_delay(n, times, k):
        # Dijkstra; times as [u,v,w] rows (1-indexed nodes)
        g = [[] for _ in range(n + 1)]
        for u, v, w in times:
            g[u].append((v, w))
        dist = [10**18] * (n + 1)
        dist[k] = 0
        h = [(0, k)]
        while h:
            d, u = heappop(h)
            if d != dist[u]:
                continue
            for v, w in g[u]:
                nd = d + w
                if nd < dist[v]:
                    dist[v] = nd
                    heappush(h, (nd, v))
        ans = max(dist[1:])
        return -1 if ans >= 10**18 else ans

    # ── refs: sorting / search ───────────────────────────────────────────────
    def ref_binary_search(nums, target):
        lo, hi = 0, len(nums) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if nums[mid] == target:
                return mid
            if nums[mid] < target:
                lo = mid + 1
            else:
                hi = mid - 1
        return -1

    def ref_search_insert(nums, target):
        lo, hi = 0, len(nums)
        while lo < hi:
            mid = (lo + hi) // 2
            if nums[mid] < target:
                lo = mid + 1
            else:
                hi = mid
        return lo

    def ref_merge_intervals(intervals):
        if not intervals:
            return []
        iv = sorted(intervals)
        out = [list(iv[0])]
        for s, e in iv[1:]:
            if s <= out[-1][1]:
                out[-1][1] = max(out[-1][1], e)
            else:
                out.append([s, e])
        return out

    def ref_sort_colors(nums):
        return sorted(nums)

    def ref_first_bad(n, bad):
        lo, hi = 1, n
        while lo < hi:
            mid = (lo + hi) // 2
            if mid >= bad:
                hi = mid
            else:
                lo = mid + 1
        return lo

    def ref_peak_index(arr):
        lo, hi = 0, len(arr) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if arr[mid] < arr[mid + 1]:
                lo = mid + 1
            else:
                hi = mid
        return lo

    def ref_kth_smallest_matrix(matrix, k):
        flat = [x for row in matrix for x in row]
        return nsmallest(k, flat)[-1]

    def ref_sort_array(nums):
        return sorted(nums)

    # ========== ARRAYS (10) ==========
    C += [
        P(
            "two-sum",
            "两数之和",
            "arrays",
            "简单",
            "给定整数数组 `nums` 与目标 `target`，返回两数下标（**升序**输出两个下标，保证唯一解）。\n"
            "stdin：第 1 行数组；第 2 行 target。",
            [{"input": "2 7 11 15\n9", "output": "0 1"}],
            "twoSum",
            "(nums: List[int], target: int) -> List[int]",
            "哈希找互补",
            "raw",
            ref_two_sum,
            [
                T("样例", [[2, 7, 11, 15], 9], True),
                T("3 2 4 · 6", [[3, 2, 4], 6], True),
                T("3 3 · 6", [[3, 3], 6]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "max-subarray",
            "最大子数组和",
            "arrays",
            "中等",
            "返回数组连续子数组的最大和（Kadane）。",
            [{"input": "-2 1 -3 4 -1 2 1 -5 4", "output": "6"}],
            "maxSubArray",
            "(nums: List[int]) -> int",
            "Kadane",
            "raw",
            ref_max_subarray,
            [
                T("样例", [[-2, 1, -3, 4, -1, 2, 1, -5, 4]], True),
                T("全正", [[1, 2, 3]], True),
                T("单元素", [[-1]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "move-zeroes",
            "移动零",
            "arrays",
            "简单",
            "将所有 0 移到末尾，保持非零相对顺序，返回结果数组。",
            [{"input": "0 1 0 3 12", "output": "1 3 12 0 0"}],
            "moveZeroes",
            "(nums: List[int]) -> List[int]",
            "双指针",
            "raw",
            ref_move_zeroes,
            [
                T("样例", [[0, 1, 0, 3, 12]], True),
                T("无零", [[1, 2]], True),
                T("全零", [[0, 0]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "remove-duplicates-sorted",
            "删除有序数组重复项",
            "arrays",
            "简单",
            "有序数组原地去重，返回新长度（只比较长度）。",
            [{"input": "1 1 2", "output": "2"}],
            "removeDuplicates",
            "(nums: List[int]) -> int",
            "双指针",
            "raw",
            lambda nums: ref_remove_duplicates(list(nums)),
            [
                T("样例", [[1, 1, 2]], True),
                T("1 1 1", [[1, 1, 1]], True),
                T("空", [[]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "rotate-array",
            "轮转数组",
            "arrays",
            "中等",
            "将数组向右轮转 `k` 步，返回结果。",
            [{"input": "1 2 3 4 5 6 7\n3", "output": "5 6 7 1 2 3 4"}],
            "rotate",
            "(nums: List[int], k: int) -> List[int]",
            "轮转",
            "raw",
            ref_rotate,
            [
                T("样例", [[1, 2, 3, 4, 5, 6, 7], 3], True),
                T("-1 -100 3 99 · 2", [[-1, -100, 3, 99], 2], True),
                T("k=0", [[1, 2], 0]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "product-except-self",
            "除自身以外的乘积",
            "arrays",
            "中等",
            "返回数组 `answer`，`answer[i]` 为除 `nums[i]` 外其余元素乘积（O(n) 且勿用除法）。",
            [{"input": "1 2 3 4", "output": "24 12 8 6"}],
            "productExceptSelf",
            "(nums: List[int]) -> List[int]",
            "前后缀乘积",
            "raw",
            ref_product_except_self,
            [
                T("样例", [[1, 2, 3, 4]], True),
                T("含0", [[-1, 1, 0, -3, 3]], True),
                T("两数", [[2, 3]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "majority-element",
            "多数元素",
            "arrays",
            "简单",
            "找出出现次数超过 ⌊n/2⌋ 的元素（保证存在）。",
            [{"input": "3 2 3", "output": "3"}],
            "majorityElement",
            "(nums: List[int]) -> int",
            "Boyer-Moore",
            "raw",
            ref_majority,
            [
                T("样例", [[3, 2, 3]], True),
                T("2 2 1 1 1 2 2", [[2, 2, 1, 1, 1, 2, 2]], True),
                T("单", [[1]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "missing-number",
            "丢失的数字",
            "arrays",
            "简单",
            "`nums` 含 `0..n` 中 n 个数，返回丢失的那个。",
            [{"input": "3 0 1", "output": "2"}],
            "missingNumber",
            "(nums: List[int]) -> int",
            "高斯求和",
            "raw",
            ref_missing_number,
            [
                T("样例", [[3, 0, 1]], True),
                T("0 1", [[0, 1]], True),
                T("9 6 4 2 3 5 7 0 1", [[9, 6, 4, 2, 3, 5, 7, 0, 1]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "contains-duplicate",
            "存在重复元素",
            "arrays",
            "简单",
            "若任一值出现至少两次返回 true，否则 false。",
            [{"input": "1 2 3 1", "output": "true"}],
            "containsDuplicate",
            "(nums: List[int]) -> bool",
            "哈希集合",
            "raw",
            ref_contains_duplicate,
            [
                T("有重复", [[1, 2, 3, 1]], True),
                T("无", [[1, 2, 3, 4]], True),
                T("空", [[]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "intersect-arrays",
            "两个数组的交集 II",
            "arrays",
            "简单",
            "返回两数组交集（含重复），结果按升序输出。",
            [{"input": "1 2 2 1\n2 2", "output": "2 2"}],
            "intersect",
            "(nums1: List[int], nums2: List[int]) -> List[int]",
            "计数哈希",
            "raw",
            ref_intersect,
            [
                T("样例", [[1, 2, 2, 1], [2, 2]], True),
                T("4 9 5 · 9 4 9 8 4", [[4, 9, 5], [9, 4, 9, 8, 4]], True),
                T("无交", [[1], [2]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
    ]

    # ========== STACK (10) ==========
    OP_ADD, OP_SUB, OP_MUL, OP_DIV = 10**9 + 1, 10**9 + 2, 10**9 + 3, 10**9 + 4
    C += [
        P(
            "valid-parentheses-codes",
            "有效的括号（编码）",
            "stack",
            "简单",
            "括号序列用整数编码：1=( 2=) 3=[ 4=] 5={ 6=}。判断是否有效。",
            [{"input": "1 3 4 2", "output": "true"}],
            "isValid",
            "(codes: List[int]) -> bool",
            "栈匹配",
            "raw",
            ref_is_valid_parens,
            [
                T("()[]", [[1, 3, 4, 2]], True),
                T("(]", [[1, 4]], True),
                T("空", [[]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "daily-temperatures",
            "每日温度",
            "stack",
            "中等",
            "对每一天，要等多少天温度才会升高；若不会则 0。",
            [{"input": "73 74 75 71 69 72 76 73", "output": "1 1 4 2 1 1 0 0"}],
            "dailyTemperatures",
            "(temperatures: List[int]) -> List[int]",
            "单调栈",
            "raw",
            ref_daily_temperatures,
            [
                T("样例", [[73, 74, 75, 71, 69, 72, 76, 73]], True),
                T("递减", [[30, 20, 10]], True),
                T("单日", [[50]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "next-greater-elements",
            "下一个更大元素 II",
            "stack",
            "中等",
            "循环数组中每个元素的下一个更大值；不存在则为 -1。",
            [{"input": "1 2 1", "output": "2 -1 2"}],
            "nextGreaterElements",
            "(nums: List[int]) -> List[int]",
            "循环单调栈",
            "raw",
            ref_next_greater,
            [
                T("样例", [[1, 2, 1]], True),
                T("1 2 3 4 3", [[1, 2, 3, 4, 3]], True),
                T("全同", [[5, 5]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "eval-rpn",
            "逆波兰表达式求值",
            "stack",
            "中等",
            "后缀表达式：操作数为普通整数；运算符编码 "
            f"{OP_ADD}=+ {OP_SUB}=- {OP_MUL}=* {OP_DIV}=/（除法向 0 取整）。",
            [{"input": f"2 1 {OP_ADD} 3 {OP_MUL}", "output": "9"}],
            "evalRPN",
            "(tokens: List[int]) -> int",
            "栈求值",
            "raw",
            ref_eval_rpn,
            [
                T("样例", [[2, 1, OP_ADD, 3, OP_MUL]], True),
                T("4 13 5 / +", [[4, 13, 5, OP_DIV, OP_ADD]], True),
                T("单值", [[42]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "largest-rectangle-histogram",
            "柱状图最大矩形",
            "stack",
            "困难",
            "给定非负高度数组，求柱状图中最大矩形面积。",
            [{"input": "2 1 5 6 2 3", "output": "10"}],
            "largestRectangleArea",
            "(heights: List[int]) -> int",
            "单调栈",
            "raw",
            ref_largest_rectangle,
            [
                T("样例", [[2, 1, 5, 6, 2, 3]], True),
                T("2 4", [[2, 4]], True),
                T("单柱", [[5]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "simplify-path-ids",
            "简化路径（目录 id）",
            "stack",
            "中等",
            "Unix 路径组件编码：0=`.`，1=`..`，正整数=目录 id。返回最终栈中的目录序列。",
            [{"input": "1 2 0 3 1", "output": "2"}],
            "simplifyPath",
            "(parts: List[int]) -> List[int]",
            "栈",
            "raw",
            ref_simplify_path,
            [
                T("样例", [[1, 2, 0, 3, 1]], True),
                T("全回退", [[1, 1, 1]], True),
                T("空", [[]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "asteroid-collision",
            "行星碰撞",
            "stack",
            "中等",
            "正数右飞、负数左飞，同向不撞；相撞质量小者爆，相等同毁。返回幸存序列。",
            [{"input": "5 10 -5", "output": "5 10"}],
            "asteroidCollision",
            "(asteroids: List[int]) -> List[int]",
            "栈模拟",
            "raw",
            ref_asteroid,
            [
                T("样例", [[5, 10, -5]], True),
                T("8 -8", [[8, -8]], True),
                T("10 2 -5", [[10, 2, -5]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "min-remove-parens",
            "最少删除有效括号",
            "stack",
            "中等",
            "序列仅含 1=( 与 2=)，删除最少括号使之有效，返回剩余序列。",
            [{"input": "1 2 2 1", "output": "1 2"}],
            "minRemoveToMakeValid",
            "(s: List[int]) -> List[int]",
            "栈标记删除",
            "raw",
            ref_min_remove_valid,
            [
                T("样例", [[1, 2, 2, 1]], True),
                T("))((", [[2, 2, 1, 1]], True),
                T("已有效", [[1, 2]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "trap-rain-water",
            "接雨水",
            "stack",
            "困难",
            "柱高数组，计算能接多少单位雨水。",
            [{"input": "0 1 0 2 1 0 1 3 2 1 2 1", "output": "6"}],
            "trap",
            "(height: List[int]) -> int",
            "双指针",
            "raw",
            ref_trap_rain,
            [
                T("样例", [[0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]], True),
                T("4 2 0 3 2 5", [[4, 2, 0, 3, 2, 5]], True),
                T("平坦", [[1, 1, 1]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "rle-expand-length",
            "行程编码展开长度",
            "stack",
            "简单",
            "交替给出 count value（如 `3 5 2 7` 表示三个 5、两个 7），返回展开后总长度。",
            [{"input": "3 5 2 7", "output": "5"}],
            "rleLength",
            "(codes: List[int]) -> int",
            "遍历累加",
            "raw",
            ref_decode_count,
            [
                T("样例", [[3, 5, 2, 7]], True),
                T("1 9", [[1, 9]], True),
                T("空", [[]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
    ]

    # ========== QUEUE (8) ==========
    C += [
        P(
            "recent-counter",
            "最近请求次数",
            "queue",
            "简单",
            "按时间顺序给出请求时刻，对每个 t 返回 (t-3000, t] 内的请求数。",
            [{"input": "1 100 3001 3002", "output": "1 2 3 3"}],
            "recentCounter",
            "(times: List[int]) -> List[int]",
            "队列滑窗",
            "raw",
            ref_recent_counter,
            [
                T("样例", [[1, 100, 3001, 3002]], True),
                T("密集", [[1, 2, 3]], True),
                T("单", [[10]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "moving-average",
            "数据流移动平均",
            "queue",
            "简单",
            "窗口大小 `size`，对数据流每个新值输出当前窗口整数均值（向下取整）。",
            [{"input": "3\n1 10 3 5", "output": "1 5 4 6"}],
            "movingAverage",
            "(size: int, vals: List[int]) -> List[int]",
            "队列",
            "raw",
            ref_moving_avg,
            [
                T("样例", [3, [1, 10, 3, 5]], True),
                T("size=1", [1, [4, 5]], True),
                T("size大", [10, [1, 2]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "first-unique-stream",
            "数据流第一个独特数",
            "queue",
            "中等",
            "给定一整段流，返回其中第一个只出现一次的数；若无则 -1。",
            [{"input": "2 3 2 4", "output": "3"}],
            "firstUniq",
            "(nums: List[int]) -> int",
            "队列+计数",
            "raw",
            ref_first_unique,
            [
                T("样例", [[2, 3, 2, 4]], True),
                T("全重复", [[1, 1]], True),
                T("单", [[7]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "stack-via-queues-ops",
            "用队列实现栈（操作序列）",
            "queue",
            "中等",
            "操作扁平序列：`1 x` 表示 push(x)，`2` 表示 pop 并记录返回值。返回所有 pop 结果。",
            [{"input": "1 1 1 2 2 2", "output": "2 1"}],
            "stackOps",
            "(ops: List[int]) -> List[int]",
            "双端队列模拟",
            "raw",
            ref_queue_stack_ops,
            [
                T("样例", [[1, 1, 1, 2, 2, 2]], True),
                T("单推弹", [[1, 5, 2]], True),
                T("空弹", [[2]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "dota2-senate",
            "Dota2 参议院",
            "queue",
            "中等",
            "序列中 1=R、2=D，轮流禁止对方下一轮议员。返回胜者阵营编码 1 或 2。",
            [{"input": "1 2", "output": "1"}],
            "predictPartyVictory",
            "(senate: List[int]) -> int",
            "双队列",
            "raw",
            ref_predict_party,
            [
                T("RD", [[1, 2]], True),
                T("RDD", [[1, 2, 2]], True),
                T("DDRRR", [[2, 2, 1, 1, 1]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "sliding-window-max",
            "滑动窗口最大值",
            "queue",
            "困难",
            "窗口大小 `k`，返回每个窗口最大值。",
            [{"input": "1 3 -1 -3 5 3 6 7\n3", "output": "3 3 5 5 6 7"}],
            "maxSlidingWindow",
            "(nums: List[int], k: int) -> List[int]",
            "单调队列",
            "raw",
            ref_max_sliding_window,
            [
                T("样例", [[1, 3, -1, -3, 5, 3, 6, 7], 3], True),
                T("k=1", [[1, 2, 3], 1], True),
                T("k=n", [[4, 2], 2]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "time-to-buy-tickets",
            "买票需要的时间",
            "queue",
            "简单",
            "`tickets[i]` 为第 i 人想买的票数，每次队首买 1 张并可能回到队尾。"
            "返回下标 `k` 的人买完所需秒数。",
            [{"input": "2 3 2\n2", "output": "6"}],
            "timeRequiredToBuy",
            "(tickets: List[int], k: int) -> int",
            "模拟队列",
            "raw",
            ref_time_needed_buy,
            [
                T("样例", [[2, 3, 2], 2], True),
                T("5 1 1 1 · 0", [[5, 1, 1, 1], 0], True),
                T("单人", [[3], 0]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "design-circular-queue-cap",
            "循环队列容量判定",
            "queue",
            "简单",
            "给定容量 `k` 与操作序列（正数=入队，-1=出队）；队满时入队忽略。"
            "返回最终队列从前到后的元素。",
            [{"input": "3\n1 2 3 4 -1 5", "output": "2 3 5"}],
            "circularQueue",
            "(k: int, ops: List[int]) -> List[int]",
            "循环队列模拟",
            "raw",
            _circular_sim,
            [
                T("样例", [3, [1, 2, 3, 4, -1, 5]], True),
                T("仅出队", [2, [-1, -1]], True),
                T("k=1", [1, [7, 8, -1]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
    ]

    # ========== LINKED LIST (10) ==========
    C += [
        P(
            "reverse-linked-list",
            "反转链表",
            "linkedlist",
            "简单",
            "链表用空格分隔的节点值表示。返回反转后的值序列。",
            [{"input": "1 2 3 4 5", "output": "5 4 3 2 1"}],
            "reverseList",
            "(head: List[int]) -> List[int]",
            "迭代反转",
            "raw",
            ref_reverse_list,
            [
                T("样例", [[1, 2, 3, 4, 5]], True),
                T("两节点", [[1, 2]], True),
                T("空", [[]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "merge-two-lists",
            "合并两个有序链表",
            "linkedlist",
            "简单",
            "合并两条升序链表（值序列），返回合并后升序序列。",
            [{"input": "1 2 4\n1 3 4", "output": "1 1 2 3 4 4"}],
            "mergeTwoLists",
            "(l1: List[int], l2: List[int]) -> List[int]",
            "双指针",
            "raw",
            ref_merge_two,
            [
                T("样例", [[1, 2, 4], [1, 3, 4]], True),
                T("空+非空", [[], [0]], True),
                T("都空", [[], []]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "linked-list-cycle-flag",
            "环形链表判定",
            "linkedlist",
            "简单",
            "给定链表值序列与环入口下标 `pos`（-1 表示无环）。返回是否有环。",
            [{"input": "3 2 0 -4\n1", "output": "true"}],
            "hasCycle",
            "(head: List[int], pos: int) -> bool",
            "快慢指针概念 / pos",
            "raw",
            ref_has_cycle_vals,
            [
                T("有环", [[3, 2, 0, -4], 1], True),
                T("无环", [[1, 2], -1], True),
                T("空", [[], -1]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "middle-of-list",
            "链表的中间节点",
            "linkedlist",
            "简单",
            "返回中间节点开始的后半段（偶数取靠后的中间）。",
            [{"input": "1 2 3 4 5", "output": "3 4 5"}],
            "middleNode",
            "(head: List[int]) -> List[int]",
            "快慢指针",
            "raw",
            ref_middle,
            [
                T("奇数", [[1, 2, 3, 4, 5]], True),
                T("偶数", [[1, 2, 3, 4, 5, 6]], True),
                T("单", [[1]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "remove-nth-from-end",
            "删除链表倒数第 N 个",
            "linkedlist",
            "中等",
            "删除倒数第 `n` 个节点，返回新序列。",
            [{"input": "1 2 3 4 5\n2", "output": "1 2 3 5"}],
            "removeNthFromEnd",
            "(head: List[int], n: int) -> List[int]",
            "双指针",
            "raw",
            ref_remove_nth,
            [
                T("样例", [[1, 2, 3, 4, 5], 2], True),
                T("删头", [[1, 2], 2], True),
                T("单节点", [[1], 1]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "palindrome-linked-list",
            "回文链表",
            "linkedlist",
            "简单",
            "判断链表值序列是否回文。",
            [{"input": "1 2 2 1", "output": "true"}],
            "isPalindrome",
            "(head: List[int]) -> bool",
            "数组或快慢指针",
            "raw",
            ref_palindrome_list,
            [
                T("是", [[1, 2, 2, 1]], True),
                T("否", [[1, 2]], True),
                T("单", [[1]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "intersection-of-lists",
            "相交链表",
            "linkedlist",
            "中等",
            "两条链表值序列与跳过长度 `skipA` `skipB`：若 `a[skipA:]` 与 `b[skipB:]` 相同且非空，"
            "返回相交起点值，否则 -1。",
            [{"input": "4 1 8 4 5\n5 6 1 8 4 5\n2\n3", "output": "8"}],
            "getIntersectionNode",
            "(a: List[int], b: List[int], skipA: int, skipB: int) -> int",
            "双指针",
            "raw",
            ref_get_intersection,
            [
                T("相交", [[4, 1, 8, 4, 5], [5, 6, 1, 8, 4, 5], 2, 3], True),
                T("不相交", [[2, 6, 4], [1, 5], 3, 2], True),
                T("同列", [[1, 2], [1, 2], 0, 0]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "add-two-numbers-list",
            "两数相加（链表）",
            "linkedlist",
            "中等",
            "两个非负整数按**逆序**存在链表中，返回和的逆序链表值序列。",
            [{"input": "2 4 3\n5 6 4", "output": "7 0 8"}],
            "addTwoNumbers",
            "(l1: List[int], l2: List[int]) -> List[int]",
            "逐位相加",
            "raw",
            ref_add_two,
            [
                T("样例", [[2, 4, 3], [5, 6, 4]], True),
                T("0+0", [[0], [0]], True),
                T("进位", [[9, 9], [1]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "swap-nodes-in-pairs",
            "两两交换链表节点",
            "linkedlist",
            "中等",
            "两两交换相邻节点，返回新序列。",
            [{"input": "1 2 3 4", "output": "2 1 4 3"}],
            "swapPairs",
            "(head: List[int]) -> List[int]",
            "迭代交换",
            "raw",
            ref_swap_pairs,
            [
                T("样例", [[1, 2, 3, 4]], True),
                T("奇数", [[1, 2, 3]], True),
                T("单", [[1]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "delete-duplicates-sorted-list",
            "删除排序链表重复元素",
            "linkedlist",
            "简单",
            "有序链表删重，使每个元素只出现一次。",
            [{"input": "1 1 2", "output": "1 2"}],
            "deleteDuplicates",
            "(head: List[int]) -> List[int]",
            "单指针",
            "raw",
            ref_delete_duplicates,
            [
                T("样例", [[1, 1, 2]], True),
                T("1 1 2 3 3", [[1, 1, 2, 3, 3]], True),
                T("空", [[]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
    ]

    # ========== HASH (10) ==========
    C += [
        P(
            "frequency-pairs",
            "元素频次对",
            "hash",
            "简单",
            "统计数组中每个不同元素的出现次数，按元素升序输出 `值 次数` 交替序列。",
            [{"input": "1 2 2 3", "output": "1 1 2 2 3 1"}],
            "freqPairs",
            "(nums: List[int]) -> List[int]",
            "哈希计数",
            "raw",
            ref_group_anagram_ids,
            [
                T("样例", [[1, 2, 2, 3]], True),
                T("全同", [[5, 5, 5]], True),
                T("空", [[]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "top-k-frequent",
            "前 K 个高频元素",
            "hash",
            "中等",
            "返回出现频率前 k 高的元素（顺序按频率，频率同按值稳定于 Counter）。",
            [{"input": "1 1 1 2 2 3\n2", "output": "1 2"}],
            "topKFrequent",
            "(nums: List[int], k: int) -> List[int]",
            "堆/桶",
            "raw",
            ref_top_k_frequent,
            [
                T("样例", [[1, 1, 1, 2, 2, 3], 2], True),
                T("单", [[1], 1], True),
                T("平票", [[4, 4, 5, 5, 6], 2]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "longest-consecutive",
            "最长连续序列",
            "hash",
            "中等",
            "未排序数组中最长连续元素序列长度（O(n) 期望）。",
            [{"input": "100 4 200 1 3 2", "output": "4"}],
            "longestConsecutive",
            "(nums: List[int]) -> int",
            "哈希集合",
            "raw",
            ref_longest_consecutive,
            [
                T("样例", [[100, 4, 200, 1, 3, 2]], True),
                T("0 3 7 2 5 8 4 6 0 1", [[0, 3, 7, 2, 5, 8, 4, 6, 0, 1]], True),
                T("空", [[]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "subarray-sum-equals-k",
            "和为 K 的子数组",
            "hash",
            "中等",
            "返回和为 `k` 的连续子数组个数。",
            [{"input": "1 1 1\n2", "output": "2"}],
            "subarraySum",
            "(nums: List[int], k: int) -> int",
            "前缀和哈希",
            "raw",
            ref_subarray_sum,
            [
                T("样例", [[1, 1, 1], 2], True),
                T("1 2 3 · 3", [[1, 2, 3], 3], True),
                T("无", [[1], 0]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "four-sum-ii",
            "四数相加 II",
            "hash",
            "中等",
            "四个数组 A B C D，计算有多少元组满足 A[i]+B[j]+C[k]+D[l]=0。",
            [{"input": "1 2\n-2 -1\n-1 2\n0 2", "output": "2"}],
            "fourSumCount",
            "(a: List[int], b: List[int], c: List[int], d: List[int]) -> int",
            "分组哈希",
            "raw",
            ref_four_sum_count,
            [
                T("样例", [[1, 2], [-2, -1], [-1, 2], [0, 2]], True),
                T("全0", [[0], [0], [0], [0]], True),
                T("无解", [[1], [1], [1], [1]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "isomorphic-arrays",
            "同构序列",
            "hash",
            "简单",
            "判断两等长整数序列是否同构（可建立双射替换）。",
            [{"input": "1 2 2 3\n4 5 5 6", "output": "true"}],
            "isIsomorphic",
            "(a: List[int], b: List[int]) -> bool",
            "双映射",
            "raw",
            ref_is_isomorphic,
            [
                T("是", [[1, 2, 2, 3], [4, 5, 5, 6]], True),
                T("否", [[1, 2, 3], [1, 1, 2]], True),
                T("空", [[], []]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "word-pattern-ids",
            "单词规律（id）",
            "hash",
            "简单",
            "`pattern` 与 `words` 均为整数 id 序列，判断是否满足一一对应规律。",
            [{"input": "1 2 1 2\n3 4 3 4", "output": "true"}],
            "wordPattern",
            "(pattern: List[int], s: List[int]) -> bool",
            "双射",
            "raw",
            ref_word_pattern,
            [
                T("是", [[1, 2, 1, 2], [3, 4, 3, 4]], True),
                T("否", [[1, 2, 1, 2], [3, 4, 3, 3]], True),
                T("长不同", [[1], [1, 2]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "find-disappeared",
            "找到所有消失的数字",
            "hash",
            "简单",
            "`nums` 长度为 n、元素在 [1,n]，返回所有未出现的数（升序）。",
            [{"input": "4 3 2 7 8 2 3 1", "output": "5 6"}],
            "findDisappearedNumbers",
            "(nums: List[int]) -> List[int]",
            "哈希/下标标记",
            "raw",
            ref_find_disappeared,
            [
                T("样例", [[4, 3, 2, 7, 8, 2, 3, 1]], True),
                T("1 1", [[1, 1]], True),
                T("完整", [[1, 2]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "single-number",
            "只出现一次的数字",
            "hash",
            "简单",
            "其余均出现两次，找出只出现一次的元素。",
            [{"input": "2 2 1", "output": "1"}],
            "singleNumber",
            "(nums: List[int]) -> int",
            "异或",
            "raw",
            ref_single_number,
            [
                T("样例", [[2, 2, 1]], True),
                T("4 1 2 1 2", [[4, 1, 2, 1, 2]], True),
                T("单", [[9]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "happy-number",
            "快乐数",
            "hash",
            "简单",
            "判断正整数 n 是否快乐数（平方和迭代出现 1）。",
            [{"input": "19", "output": "true"}],
            "isHappy",
            "(n: int) -> bool",
            "哈希判环",
            "raw",
            ref_happy_number,
            [
                T("19", [19], True),
                T("2", [2], True),
                T("1", [1]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
    ]

    # ========== HEAP (8) ==========
    C += [
        P(
            "kth-largest-array",
            "数组中的第 K 个最大元素",
            "heap",
            "中等",
            "返回第 k 大的元素（1-indexed 从大到小）。",
            [{"input": "3 2 1 5 6 4\n2", "output": "5"}],
            "findKthLargest",
            "(nums: List[int], k: int) -> int",
            "堆 / 快选",
            "raw",
            ref_find_kth_largest,
            [
                T("样例", [[3, 2, 1, 5, 6, 4], 2], True),
                T("3 2 3 1 2 4 5 5 6 · 4", [[3, 2, 3, 1, 2, 4, 5, 5, 6], 4], True),
                T("单", [[1], 1]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "k-smallest-pairs",
            "查找和最小的 K 对数字",
            "heap",
            "中等",
            "两个升序数组，返回 k 个数对 (u,v) 的扁平序列 u v u v…（按和升序）。",
            [{"input": "1 7 11\n2 4 6\n3", "output": "1 2 1 4 1 6"}],
            "kSmallestPairs",
            "(nums1: List[int], nums2: List[int], k: int) -> List[int]",
            "最小堆",
            "raw",
            ref_k_smallest_pairs,
            [
                T("样例", [[1, 7, 11], [2, 4, 6], 3], True),
                T("1 1 2 · 1 2 3 · 2", [[1, 1, 2], [1, 2, 3], 2], True),
                T("空", [[], [1], 1]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "merge-k-sorted-lists",
            "合并 K 个升序链表",
            "heap",
            "困难",
            "二维输入：每行一条升序链表，空行结束。合并为一条升序序列。",
            [{"input": "1 4 5\n1 3 4\n2 6\n", "output": "1 1 2 3 4 4 5 6"}],
            "mergeKLists",
            "(lists: List[List[int]]) -> List[int]",
            "多路归并堆",
            "raw",
            ref_merge_k_lists,
            [
                T("样例", [[[1, 4, 5], [1, 3, 4], [2, 6]]], True),
                T("空", [[[]]], True),
                T("单条", [[[1, 2]]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "last-stone-weight",
            "最后一块石头的重量",
            "heap",
            "简单",
            "每次砸两块最重石头；差若非零放回。返回最后重量（或 0）。",
            [{"input": "2 7 4 1 8 1", "output": "1"}],
            "lastStoneWeight",
            "(stones: List[int]) -> int",
            "最大堆",
            "raw",
            ref_last_stone,
            [
                T("样例", [[2, 7, 4, 1, 8, 1]], True),
                T("全同", [[1, 1]], True),
                T("单", [[5]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "k-closest-points",
            "最接近原点的 K 个点",
            "heap",
            "中等",
            "点坐标扁平为 x y x y…，返回距原点最近的 k 个点（按距离、x、y 排序后扁平输出）。",
            [{"input": "1 3 -2 2\n1", "output": "-2 2"}],
            "kClosest",
            "(points: List[int], k: int) -> List[int]",
            "堆",
            "raw",
            ref_k_closest,
            [
                T("样例", [[1, 3, -2, 2], 1], True),
                T("3 3 5 -1 -2 4 · 2", [[3, 3, 5, -1, -2, 4], 2], True),
                T("单点", [[0, 1], 1]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "reorganize-string-ids",
            "能否重构使相邻不同",
            "heap",
            "中等",
            "判断整数序列能否重排使相邻元素都不同。",
            [{"input": "1 1 1 2 2 3", "output": "true"}],
            "reorganizePossible",
            "(nums: List[int]) -> bool",
            "贪心计数",
            "raw",
            ref_reorganize_possible,
            [
                T("可以", [[1, 1, 1, 2, 2, 3]], True),
                T("不可", [[1, 1, 1, 1]], True),
                T("两色", [[1, 2]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "median-finder-stream",
            "数据流中位数",
            "heap",
            "困难",
            "依次插入数组元素，每插入一次输出当前中位数（偶数个时向下取整）。",
            [{"input": "1 2 3", "output": "1 1 2"}],
            "medianStream",
            "(nums: List[int]) -> List[int]",
            "双堆",
            "raw",
            ref_median_stream,
            [
                T("样例", [[1, 2, 3]], True),
                T("5 2 1 3", [[5, 2, 1, 3]], True),
                T("单", [[7]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "task-scheduler-idle",
            "任务调度器",
            "heap",
            "中等",
            "任务用整数 id 表示，相同任务冷却为 `n`。返回完成所需最短时间单位。",
            [{"input": "1 1 1 2 2 2\n2", "output": "8"}],
            "leastInterval",
            "(tasks: List[int], n: int) -> int",
            "贪心计数",
            "raw",
            ref_task_idle,
            [
                T("样例", [[1, 1, 1, 2, 2, 2], 2], True),
                T("n=0", [[1, 2, 3], 0], True),
                T("单类", [[1, 1], 1]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
    ]

    # ========== GRAPH (10) ==========
    C += [
        P(
            "graph-bfs-order",
            "图的 BFS 序",
            "graph",
            "简单",
            "n 个节点 0..n-1 无向图。stdin：n；start；边列表每行 u v，空行结束。返回 BFS 访问序（邻接排序）。",
            [{"input": "4\n0\n0 1\n0 2\n1 3\n", "output": "0 1 2 3"}],
            "bfsOrder",
            "(n: int, start: int, edges: List[List[int]]) -> List[int]",
            "BFS",
            "raw",
            ref_bfs_order,
            [
                T("样例", [4, 0, [[0, 1], [0, 2], [1, 3]]], True),
                T("链", [3, 2, [[0, 1], [1, 2]]], True),
                T("单点", [1, 0, []]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "graph-dfs-order",
            "图的 DFS 序",
            "graph",
            "简单",
            "同 BFS 输入，返回递归 DFS 序（邻接按升序）。",
            [{"input": "4\n0\n0 1\n0 2\n1 3\n", "output": "0 1 3 2"}],
            "dfsOrder",
            "(n: int, start: int, edges: List[List[int]]) -> List[int]",
            "DFS",
            "raw",
            ref_dfs_order,
            [
                T("样例", [4, 0, [[0, 1], [0, 2], [1, 3]]], True),
                T("星形", [4, 0, [[0, 1], [0, 2], [0, 3]]], True),
                T("单点", [1, 0, []]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "number-of-islands",
            "岛屿数量",
            "graph",
            "中等",
            "二维网格 1=陆地 0=水，返回岛屿数量。",
            [{"input": "1 1 1 1 0\n1 1 0 1 0\n1 1 0 0 0\n0 0 0 0 0\n", "output": "1"}],
            "numIslands",
            "(grid: List[List[int]]) -> int",
            "DFS/BFS 网格",
            "raw",
            lambda grid: ref_num_islands([row[:] for row in grid]),
            [
                T("样例", [[[1, 1, 1, 1, 0], [1, 1, 0, 1, 0], [1, 1, 0, 0, 0], [0, 0, 0, 0, 0]]], True),
                T("三岛", [[[1, 1, 0, 0, 0], [1, 1, 0, 0, 0], [0, 0, 1, 0, 0], [0, 0, 0, 1, 1]]], True),
                T("全水", [[[0, 0], [0, 0]]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "course-schedule",
            "课程表",
            "graph",
            "中等",
            "`n` 门课，边 [a,b] 表示修 a 前须修 b。判断能否修完所有课。",
            [{"input": "2\n1 0\n", "output": "true"}],
            "canFinish",
            "(n: int, edges: List[List[int]]) -> bool",
            "拓扑排序",
            "raw",
            ref_can_finish,
            [
                T("可以", [2, [[1, 0]]], True),
                T("环", [2, [[1, 0], [0, 1]]], True),
                T("无边", [1, []]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "shortest-path-unweighted",
            "无权最短路",
            "graph",
            "中等",
            "无向无权图，求 start 到 target 最短边数；不可达 -1。",
            [{"input": "4\n0\n3\n0 1\n1 2\n2 3\n", "output": "3"}],
            "shortestPath",
            "(n: int, start: int, target: int, edges: List[List[int]]) -> int",
            "BFS 最短路",
            "raw",
            ref_shortest_unweighted,
            [
                T("样例", [4, 0, 3, [[0, 1], [1, 2], [2, 3]]], True),
                T("自达", [2, 1, 1, [[0, 1]]], True),
                T("不可达", [3, 0, 2, [[0, 1]]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "connected-components",
            "连通分量个数",
            "graph",
            "简单",
            "无向图连通分量数量。",
            [{"input": "5\n0 1\n1 2\n3 4\n", "output": "2"}],
            "countComponents",
            "(n: int, edges: List[List[int]]) -> int",
            "并查集/DFS",
            "raw",
            ref_connected_components,
            [
                T("样例", [5, [[0, 1], [1, 2], [3, 4]]], True),
                T("全连", [3, [[0, 1], [1, 2]]], True),
                T("孤立", [3, []]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "rotting-oranges",
            "腐烂的橘子",
            "graph",
            "中等",
            "网格 0 空 1 鲜 2 腐。每分钟腐烂四邻鲜橘。返回全烂分钟数；不可能 -1。",
            [{"input": "2 1 1\n1 1 0\n0 1 1\n", "output": "4"}],
            "orangesRotting",
            "(grid: List[List[int]]) -> int",
            "多源 BFS",
            "raw",
            lambda grid: ref_oranges_rotting([row[:] for row in grid]),
            [
                T("样例", [[[2, 1, 1], [1, 1, 0], [0, 1, 1]]], True),
                T("已无鲜", [[[2, 2], [2, 2]]], True),
                T("困住", [[[1, 0], [0, 2]]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "find-if-path-exists",
            "寻找图中是否存在路径",
            "graph",
            "简单",
            "判断 source 与 destination 是否连通。",
            [{"input": "3\n0\n2\n0 1\n1 2\n", "output": "true"}],
            "validPath",
            "(n: int, edges: List[List[int]], source: int, destination: int) -> bool",
            "BFS/并查集",
            "raw",
            lambda n, edges, s, d: ref_valid_path(n, edges, s, d),
            [
                T("通", [3, [[0, 1], [1, 2]], 0, 2], True),
                T("不通", [6, [[0, 1], [2, 3]], 0, 5], True),
                T("同点", [1, [], 0, 0]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "flood-fill",
            "图像渲染",
            "graph",
            "简单",
            "从 (sr,sc) 出发把连通的同色格子改为 `color`，返回新网格。",
            [{"input": "1 1 1\n1 1 0\n1 0 1\n\n1\n1\n2", "output": "2 2 2\n2 2 0\n2 0 1"}],
            "floodFill",
            "(grid: List[List[int]], sr: int, sc: int, color: int) -> List[List[int]]",
            "DFS/BFS 填充",
            "raw",
            ref_flood_fill,
            [
                T("样例", [[[1, 1, 1], [1, 1, 0], [1, 0, 1]], 1, 1, 2], True),
                T("同色", [[[0, 0], [0, 0]], 0, 0, 0], True),
                T("单格", [[[1]], 0, 0, 2]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "network-delay-time",
            "网络延迟时间",
            "graph",
            "中等",
            "有向带权图，`times` 每行 u v w（节点 1..n）。从节点 k 出发，返回所有节点收到信号的时间；不可达 -1。",
            [{"input": "4\n2 1 1\n2 3 1\n3 4 1\n\n2", "output": "2"}],
            "networkDelayTime",
            "(n: int, times: List[List[int]], k: int) -> int",
            "Dijkstra",
            "raw",
            ref_network_delay,
            [
                T("样例", [4, [[2, 1, 1], [2, 3, 1], [3, 4, 1]], 2], True),
                T("不可达", [2, [[1, 2, 1]], 2], True),
                T("单点", [1, [], 1]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
    ]

    # ========== SORTING / SEARCH (8) ==========
    C += [
        P(
            "binary-search",
            "二分查找",
            "sorting",
            "简单",
            "升序数组中找 target 下标；不存在返回 -1。",
            [{"input": "-1 0 3 5 9 12\n9", "output": "4"}],
            "search",
            "(nums: List[int], target: int) -> int",
            "二分",
            "raw",
            ref_binary_search,
            [
                T("找到", [[-1, 0, 3, 5, 9, 12], 9], True),
                T("没有", [[-1, 0, 3, 5, 9, 12], 2], True),
                T("空", [[], 1]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "search-insert-position",
            "搜索插入位置",
            "sorting",
            "简单",
            "升序数组中找 target，否则返回应插入位置。",
            [{"input": "1 3 5 6\n5", "output": "2"}],
            "searchInsert",
            "(nums: List[int], target: int) -> int",
            "二分下界",
            "raw",
            ref_search_insert,
            [
                T("命中", [[1, 3, 5, 6], 5], True),
                T("插入中", [[1, 3, 5, 6], 2], True),
                T("尾后", [[1, 3], 5]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "merge-intervals",
            "合并区间",
            "sorting",
            "中等",
            "区间列表每行 L R，空行结束；合并重叠区间后按行输出。",
            [{"input": "1 3\n2 6\n8 10\n15 18\n", "output": "1 6\n8 10\n15 18"}],
            "merge",
            "(intervals: List[List[int]]) -> List[List[int]]",
            "排序贪心",
            "raw",
            ref_merge_intervals,
            [
                T("样例", [[[1, 3], [2, 6], [8, 10], [15, 18]]], True),
                T("全并", [[[1, 4], [4, 5]]], True),
                T("空", [[]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "sort-colors",
            "颜色分类",
            "sorting",
            "中等",
            "数组只含 0/1/2，排序后返回。",
            [{"input": "2 0 2 1 1 0", "output": "0 0 1 1 2 2"}],
            "sortColors",
            "(nums: List[int]) -> List[int]",
            "荷兰国旗 / 计数",
            "raw",
            ref_sort_colors,
            [
                T("样例", [[2, 0, 2, 1, 1, 0]], True),
                T("2 0 1", [[2, 0, 1]], True),
                T("已序", [[0, 1, 2]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "first-bad-version",
            "第一个错误的版本",
            "sorting",
            "简单",
            "版本 1..n，从 `bad` 起皆错。返回第一个错误版本（模拟 isBadVersion）。",
            [{"input": "5\n4", "output": "4"}],
            "firstBadVersion",
            "(n: int, bad: int) -> int",
            "二分",
            "raw",
            ref_first_bad,
            [
                T("样例", [5, 4], True),
                T("全错", [1, 1], True),
                T("末错", [3, 3]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "peak-index-mountain",
            "山脉数组峰顶",
            "sorting",
            "中等",
            "严格山脉数组，返回峰顶下标。",
            [{"input": "0 2 1 0", "output": "1"}],
            "peakIndexInMountainArray",
            "(arr: List[int]) -> int",
            "二分",
            "raw",
            ref_peak_index,
            [
                T("样例", [[0, 2, 1, 0]], True),
                T("0 10 5 2", [[0, 10, 5, 2]], True),
                T("1 3 2", [[1, 3, 2]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "kth-smallest-in-matrix",
            "有序矩阵中第 K 小",
            "sorting",
            "中等",
            "每行每列升序的 n×n 矩阵，返回第 k 小元素。",
            [{"input": "1 5 9\n10 11 13\n12 13 15\n\n8", "output": "13"}],
            "kthSmallest",
            "(matrix: List[List[int]], k: int) -> int",
            "堆/二分",
            "raw",
            ref_kth_smallest_matrix,
            [
                T("样例", [[[1, 5, 9], [10, 11, 13], [12, 13, 15]], 8], True),
                T("单", [[[-5]], 1], True),
                T("k=1", [[[1, 2], [3, 4]], 1]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
        P(
            "sort-an-array",
            "排序数组",
            "sorting",
            "中等",
            "返回升序排序后的数组（可实现快排/归并等）。",
            [{"input": "5 2 3 1", "output": "1 2 3 5"}],
            "sortArray",
            "(nums: List[int]) -> List[int]",
            "排序",
            "raw",
            ref_sort_array,
            [
                T("样例", [[5, 2, 3, 1]], True),
                T("已序", [[1, 2, 3]], True),
                T("含负", [[-2, 3, -1]]),
            ],
            constraints=DS_CONSTRAINTS,
        ),
    ]

    return C
