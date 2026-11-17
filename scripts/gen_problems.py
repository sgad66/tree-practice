#!/usr/bin/env python3
"""Generate 100 tree practice problems as TypeScript modules."""
from __future__ import annotations

import json
import os
import re
from collections import deque
from pathlib import Path
from typing import Any, Callable, Optional

OUT = Path(__file__).resolve().parents[1] / "src" / "data"


# ── Tree helpers (same semantics as in-browser judge) ─────────────────────────
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def build_tree(arr):
    if not arr:
        return None
    nodes = [None if v is None else TreeNode(v) for v in arr]
    kids = 1
    for node in nodes:
        if node is None:
            continue
        if kids < len(nodes):
            node.left = nodes[kids]
            kids += 1
        if kids < len(nodes):
            node.right = nodes[kids]
            kids += 1
    return nodes[0]


def tree_to_list(root):
    if root is None:
        return []
    out, q = [], [root]
    while q:
        node = q.pop(0)
        if node is None:
            out.append(None)
        else:
            out.append(node.val)
            q.append(node.left)
            q.append(node.right)
    while out and out[-1] is None:
        out.pop()
    return out


def find_node(root, val):
    if root is None:
        return None
    if root.val == val:
        return root
    return find_node(root.left, val) or find_node(root.right, val)


def dumps_ts(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


# ── C signature helpers ───────────────────────────────────────────────────────
_TYPE_MAP = {
    "Optional[TreeNode]": ("struct TreeNode*", "tree"),
    "TreeNode": ("struct TreeNode*", "tree"),
    "int": ("int", "int"),
    "float": ("double", "float"),
    "bool": ("bool", "bool"),
    "str": ("char*", "string"),
    "Optional[int]": ("int*", "optional_int"),
    "List[int]": ("int*", "int_array"),
    "List[float]": ("double*", "double_array"),
    "List[str]": ("char**", "string_array"),
    "List[List[int]]": ("int**", "int_matrix"),
    "List[List[str]]": ("char***", "string_matrix"),
}


def _parse_sig(sig: str) -> tuple[list[tuple[str, str, str]], str, str]:
    """Return (params as (name, c_type, kind), return_c_type, return_kind)."""
    sig = sig.strip()
    m = re.match(r"^\((.*)\)\s*->\s*(.+)$", sig)
    if not m:
        raise ValueError(f"bad sig: {sig}")
    params_s, ret_s = m.group(1).strip(), m.group(2).strip()
    params: list[tuple[str, str, str]] = []
    if params_s:
        # split on commas not inside brackets
        parts: list[str] = []
        depth = 0
        cur = []
        for ch in params_s:
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
            if ch == "," and depth == 0:
                parts.append("".join(cur).strip())
                cur = []
                continue
            cur.append(ch)
        if cur:
            parts.append("".join(cur).strip())
        for part in parts:
            name, typ = [x.strip() for x in part.split(":", 1)]
            if typ not in _TYPE_MAP:
                raise ValueError(f"unknown type {typ} in {sig}")
            c_ty, kind = _TYPE_MAP[typ]
            params.append((name, c_ty, kind))
    if ret_s not in _TYPE_MAP:
        raise ValueError(f"unknown return type {ret_s} in {sig}")
    ret_c, ret_kind = _TYPE_MAP[ret_s]
    return params, ret_c, ret_kind


def analyze_c_abi(sig: str) -> dict:
    params, _ret_c, ret_kind = _parse_sig(sig)
    return {
        "params": [{"name": n, "kind": k} for n, _c, k in params],
        "returnKind": ret_kind,
    }


def starter(fn: str, sig: str, comment: str) -> str:
    """Emit a LeetCode-style C starter from a Python-like signature string."""
    if fn == "serialize":
        # special-cased in extend_catalog; fallback prototype pair
        return (
            "/* TreeNode 由判题环境提供 */\n"
            "char* serialize(struct TreeNode* root) {\n"
            "    // 序列化\n"
            "    return NULL;\n"
            "}\n\n"
            "struct TreeNode* deserialize(char* data) {\n"
            "    // 反序列化\n"
            "    return NULL;\n"
            "}\n"
        )

    params, ret_c, ret_kind = _parse_sig(sig)
    c_params: list[str] = []
    for name, c_ty, kind in params:
        c_params.append(f"{c_ty} {name}")
        if kind in ("int_array", "double_array", "string_array"):
            c_params.append(f"int {name}Size")
        elif kind in ("int_matrix", "string_matrix"):
            c_params.append(f"int {name}Size")
            c_params.append(f"int* {name}ColSize")

    out_notes: list[str] = []
    if ret_kind in ("int_array", "double_array", "string_array"):
        c_params.append("int* returnSize")
        out_notes.append("返回的数组需 malloc；通过 returnSize 写出长度。")
    elif ret_kind in ("int_matrix", "string_matrix"):
        c_params.append("int* returnSize")
        c_params.append("int** returnColumnSizes")
        out_notes.append("返回的二维数组需 malloc；returnSize 为行数，returnColumnSizes 为每行长度。")
    elif ret_kind == "optional_int":
        out_notes.append("无结果时返回 NULL；有结果时返回 malloc 的单个 int。")
    elif ret_kind == "string":
        out_notes.append("返回的字符串需 malloc（或返回静态/字面量时请确保生命周期足够）。")

    needs_stdbool = ret_kind == "bool" or any(k == "bool" for _n, _c, k in params)
    headers = ["/* TreeNode 由判题环境提供：", " * struct TreeNode { int val; struct TreeNode *left; struct TreeNode *right; };", " */"]
    if needs_stdbool:
        headers.insert(0, "#include <stdbool.h>")
    for note in out_notes:
        headers.append(f"/* {note} */")

    body_lines = [f"    // {comment}"]
    if ret_kind == "bool":
        body_lines.append("    return false;")
    elif ret_kind in ("int", "float"):
        body_lines.append("    return 0;")
    elif ret_kind == "tree":
        body_lines.append("    return NULL;")
    elif ret_kind == "optional_int":
        body_lines.append("    return NULL;")
    elif ret_kind == "string":
        body_lines.append("    return NULL;")
    elif ret_kind in ("int_array", "double_array", "string_array"):
        body_lines.append("    *returnSize = 0;")
        body_lines.append("    return NULL;")
    elif ret_kind in ("int_matrix", "string_matrix"):
        body_lines.append("    *returnSize = 0;")
        body_lines.append("    return NULL;")
    else:
        body_lines.append("    return 0;")

    proto = f"{ret_c} {fn}({', '.join(c_params)})"
    return "\n".join(headers) + "\n" + proto + " {\n" + "\n".join(body_lines) + "\n}\n"


DEFAULT_CONSTRAINTS = [
    "节点数目范围见题面；请注意空树与单节点边界",
    "如无特别说明，节点值范围为合理整数",
]


# ── Reference solutions ───────────────────────────────────────────────────────
def ref_preorder(root):
    if not root:
        return []
    return [root.val] + ref_preorder(root.left) + ref_preorder(root.right)


def ref_inorder(root):
    if not root:
        return []
    return ref_inorder(root.left) + [root.val] + ref_inorder(root.right)


def ref_postorder(root):
    if not root:
        return []
    return ref_postorder(root.left) + ref_postorder(root.right) + [root.val]


def ref_level_order(root):
    if not root:
        return []
    res, q = [], deque([root])
    while q:
        n = len(q)
        level = []
        for _ in range(n):
            node = q.popleft()
            level.append(node.val)
            if node.left:
                q.append(node.left)
            if node.right:
                q.append(node.right)
        res.append(level)
    return res


def ref_level_order_bottom(root):
    return list(reversed(ref_level_order(root)))


def ref_zigzag(root):
    levels = ref_level_order(root)
    for i, lv in enumerate(levels):
        if i % 2 == 1:
            lv.reverse()
    return levels


def ref_right_side(root):
    return [lv[-1] for lv in ref_level_order(root)]


def ref_left_side(root):
    return [lv[0] for lv in ref_level_order(root)]


def ref_avg_levels(root):
    return [sum(lv) / len(lv) for lv in ref_level_order(root)]


def ref_max_depth(root):
    if not root:
        return 0
    return 1 + max(ref_max_depth(root.left), ref_max_depth(root.right))


def ref_min_depth(root):
    if not root:
        return 0
    if not root.left and not root.right:
        return 1
    if not root.left:
        return 1 + ref_min_depth(root.right)
    if not root.right:
        return 1 + ref_min_depth(root.left)
    return 1 + min(ref_min_depth(root.left), ref_min_depth(root.right))


def ref_is_symmetric(root):
    def mir(a, b):
        if not a and not b:
            return True
        if not a or not b or a.val != b.val:
            return False
        return mir(a.left, b.right) and mir(a.right, b.left)

    return mir(root, root) if root else True


def ref_invert(root):
    if not root:
        return None
    root.left, root.right = ref_invert(root.right), ref_invert(root.left)
    return root


def ref_same_tree(p, q):
    if not p and not q:
        return True
    if not p or not q or p.val != q.val:
        return False
    return ref_same_tree(p.left, q.left) and ref_same_tree(p.right, q.right)


def ref_is_balanced(root):
    def h(n):
        if not n:
            return 0
        lh, rh = h(n.left), h(n.right)
        if lh < 0 or rh < 0 or abs(lh - rh) > 1:
            return -1
        return 1 + max(lh, rh)

    return h(root) >= 0


def ref_diameter(root):
    best = [0]

    def dfs(n):
        if not n:
            return 0
        L, R = dfs(n.left), dfs(n.right)
        best[0] = max(best[0], L + R)
        return 1 + max(L, R)

    dfs(root)
    return best[0]


def ref_count_nodes(root):
    if not root:
        return 0
    return 1 + ref_count_nodes(root.left) + ref_count_nodes(root.right)


def ref_sum_nodes(root):
    if not root:
        return 0
    return root.val + ref_sum_nodes(root.left) + ref_sum_nodes(root.right)


def ref_leaf_count(root):
    if not root:
        return 0
    if not root.left and not root.right:
        return 1
    return ref_leaf_count(root.left) + ref_leaf_count(root.right)


def ref_is_unival(root):
    if not root:
        return True

    def ok(n, v):
        if not n:
            return True
        return n.val == v and ok(n.left, v) and ok(n.right, v)

    return ok(root, root.val)


def ref_merge_trees(t1, t2):
    if not t1:
        return t2
    if not t2:
        return t1
    n = TreeNode(t1.val + t2.val)
    n.left = ref_merge_trees(t1.left, t2.left)
    n.right = ref_merge_trees(t1.right, t2.right)
    return n


def ref_has_path_sum(root, target):
    if not root:
        return False
    if not root.left and not root.right:
        return root.val == target
    return ref_has_path_sum(root.left, target - root.val) or ref_has_path_sum(
        root.right, target - root.val
    )


def ref_path_sum_all(root, target):
    res = []

    def dfs(n, remain, path):
        if not n:
            return
        path.append(n.val)
        if not n.left and not n.right and remain == n.val:
            res.append(path[:])
        else:
            dfs(n.left, remain - n.val, path)
            dfs(n.right, remain - n.val, path)
        path.pop()

    dfs(root, target, [])
    return res


def ref_sum_root_to_leaf_numbers(root):
    def dfs(n, cur):
        if not n:
            return 0
        cur = cur * 10 + n.val
        if not n.left and not n.right:
            return cur
        return dfs(n.left, cur) + dfs(n.right, cur)

    return dfs(root, 0)


def ref_binary_tree_paths(root):
    res = []

    def dfs(n, path):
        if not n:
            return
        path.append(str(n.val))
        if not n.left and not n.right:
            res.append("->".join(path))
        else:
            dfs(n.left, path)
            dfs(n.right, path)
        path.pop()

    dfs(root, [])
    return res


def ref_max_path_sum(root):
    best = [float("-inf")]

    def dfs(n):
        if not n:
            return 0
        L = max(dfs(n.left), 0)
        R = max(dfs(n.right), 0)
        best[0] = max(best[0], n.val + L + R)
        return n.val + max(L, R)

    dfs(root)
    return best[0]


def ref_path_sum_iii(root, target):
    def dfs(n, prefix, cur):
        if not n:
            return 0
        cur += n.val
        ans = prefix.get(cur - target, 0)
        prefix[cur] = prefix.get(cur, 0) + 1
        ans += dfs(n.left, prefix, cur) + dfs(n.right, prefix, cur)
        prefix[cur] -= 1
        return ans

    return dfs(root, {0: 1}, 0)


def ref_is_valid_bst(root):
    def ok(n, lo, hi):
        if not n:
            return True
        if n.val <= lo or n.val >= hi:
            return False
        return ok(n.left, lo, n.val) and ok(n.right, n.val, hi)

    return ok(root, float("-inf"), float("inf"))


def ref_search_bst(root, val):
    while root and root.val != val:
        root = root.left if val < root.val else root.right
    return root


def ref_insert_bst(root, val):
    if not root:
        return TreeNode(val)
    if val < root.val:
        root.left = ref_insert_bst(root.left, val)
    else:
        root.right = ref_insert_bst(root.right, val)
    return root


def ref_bst_min(root):
    while root and root.left:
        root = root.left
    return root.val if root else None


def ref_bst_max(root):
    while root and root.right:
        root = root.right
    return root.val if root else None


def ref_kth_smallest(root, k):
    stack = []
    while True:
        while root:
            stack.append(root)
            root = root.left
        root = stack.pop()
        k -= 1
        if k == 0:
            return root.val
        root = root.right


def ref_kth_largest(root, k):
    stack = []
    while True:
        while root:
            stack.append(root)
            root = root.right
        root = stack.pop()
        k -= 1
        if k == 0:
            return root.val
        root = root.left


def ref_lowest_common_ancestor(root, p, q):
    if not root or root is p or root is q:
        return root
    L = ref_lowest_common_ancestor(root.left, p, q)
    R = ref_lowest_common_ancestor(root.right, p, q)
    if L and R:
        return root
    return L or R


def ref_lca_bst(root, p, q):
    while root:
        if p.val < root.val and q.val < root.val:
            root = root.left
        elif p.val > root.val and q.val > root.val:
            root = root.right
        else:
            return root
    return None


def ref_build_tree_pre_in(preorder, inorder):
    idx = {v: i for i, v in enumerate(inorder)}

    def build(pl, pr, il, ir):
        if pl > pr:
            return None
        root = TreeNode(preorder[pl])
        mid = idx[preorder[pl]]
        left_sz = mid - il
        root.left = build(pl + 1, pl + left_sz, il, mid - 1)
        root.right = build(pl + left_sz + 1, pr, mid + 1, ir)
        return root

    return build(0, len(preorder) - 1, 0, len(inorder) - 1)


def ref_build_tree_in_post(inorder, postorder):
    idx = {v: i for i, v in enumerate(inorder)}

    def build(il, ir, pl, pr):
        if il > ir:
            return None
        root = TreeNode(postorder[pr])
        mid = idx[postorder[pr]]
        left_sz = mid - il
        root.left = build(il, mid - 1, pl, pl + left_sz - 1)
        root.right = build(mid + 1, ir, pl + left_sz, pr - 1)
        return root

    return build(0, len(inorder) - 1, 0, len(postorder) - 1)


def ref_sorted_array_to_bst(nums):
    def build(l, r):
        if l > r:
            return None
        m = (l + r) // 2
        n = TreeNode(nums[m])
        n.left = build(l, m - 1)
        n.right = build(m + 1, r)
        return n

    return build(0, len(nums) - 1)


def ref_serialize_roundtrip(root):
    # identity via list encoding for expected
    return tree_to_list(root)


def ref_flatten_preorder_links(root):
    """Flatten to right-skewed list in preorder; return list of vals along right chain."""
    if not root:
        return []
    nodes = []

    def dfs(n):
        if not n:
            return
        nodes.append(n)
        dfs(n.left)
        dfs(n.right)

    dfs(root)
    for i, n in enumerate(nodes):
        n.left = None
        n.right = nodes[i + 1] if i + 1 < len(nodes) else None
    return tree_to_list(nodes[0]) if nodes else []


def ref_is_subtree(root, sub):
    if not sub:
        return True
    if not root:
        return False
    return ref_same_tree(root, sub) or ref_is_subtree(root.left, sub) or ref_is_subtree(
        root.right, sub
    )


def ref_range_sum_bst(root, low, high):
    if not root:
        return 0
    if root.val < low:
        return ref_range_sum_bst(root.right, low, high)
    if root.val > high:
        return ref_range_sum_bst(root.left, low, high)
    return (
        root.val
        + ref_range_sum_bst(root.left, low, high)
        + ref_range_sum_bst(root.right, low, high)
    )


def ref_trim_bst(root, low, high):
    if not root:
        return None
    if root.val < low:
        return ref_trim_bst(root.right, low, high)
    if root.val > high:
        return ref_trim_bst(root.left, low, high)
    root.left = ref_trim_bst(root.left, low, high)
    root.right = ref_trim_bst(root.right, low, high)
    return root


def ref_increasing_bst(root):
    vals = ref_inorder(root)
    dummy = TreeNode(0)
    cur = dummy
    for v in vals:
        cur.right = TreeNode(v)
        cur = cur.right
    return dummy.right


def ref_find_mode_bst(root):
    # modes of multiset of values (works for any tree; name says BST)
    from collections import Counter

    def collect(n, acc):
        if not n:
            return
        acc.append(n.val)
        collect(n.left, acc)
        collect(n.right, acc)

    vals = []
    collect(root, vals)
    c = Counter(vals)
    mx = max(c.values()) if c else 0
    return sorted([k for k, v in c.items() if v == mx])


def ref_closest_bst(root, target):
    best = root.val
    while root:
        if abs(root.val - target) < abs(best - target):
            best = root.val
        root = root.left if target < root.val else root.right
    return best


def ref_two_sum_bst(root, k):
    s = set()

    def dfs(n):
        if not n:
            return False
        if k - n.val in s:
            return True
        s.add(n.val)
        return dfs(n.left) or dfs(n.right)

    return dfs(root)


def ref_width_of_binary_tree(root):
    if not root:
        return 0
    best = 0
    q = deque([(root, 0)])
    while q:
        left = q[0][1]
        for _ in range(len(q)):
            node, idx = q.popleft()
            best = max(best, idx - left + 1)
            if node.left:
                q.append((node.left, 2 * idx))
            if node.right:
                q.append((node.right, 2 * idx + 1))
    return best


def ref_complete_tree_nodes(root):
    return ref_count_nodes(root)


def ref_add_one_row(root, val, depth):
    if depth == 1:
        return TreeNode(val, root, None)

    def dfs(n, d):
        if not n:
            return
        if d == depth - 1:
            n.left = TreeNode(val, n.left, None)
            n.right = TreeNode(val, None, n.right)
            return
        dfs(n.left, d + 1)
        dfs(n.right, d + 1)

    dfs(root, 1)
    return root


def ref_prune_zero(root):
    if not root:
        return None
    root.left = ref_prune_zero(root.left)
    root.right = ref_prune_zero(root.right)
    if root.val == 0 and not root.left and not root.right:
        return None
    return root


def ref_good_nodes(root):
    def dfs(n, mx):
        if not n:
            return 0
        good = 1 if n.val >= mx else 0
        nmx = max(mx, n.val)
        return good + dfs(n.left, nmx) + dfs(n.right, nmx)

    return dfs(root, float("-inf")) if root else 0


def ref_deepest_leaves_sum(root):
    if not root:
        return 0
    levels = ref_level_order(root)
    return sum(levels[-1])


def ref_subtree_with_all_deepest(root):
    def dfs(n):
        if not n:
            return 0, None
        lh, ln = dfs(n.left)
        rh, rn = dfs(n.right)
        if lh == rh:
            return lh + 1, n
        return (lh + 1, ln) if lh > rh else (rh + 1, rn)

    return dfs(root)[1]


def ref_vertical_order(root):
    if not root:
        return []
    from collections import defaultdict

    cols = defaultdict(list)
    q = deque([(root, 0)])
    while q:
        n, c = q.popleft()
        cols[c].append(n.val)
        if n.left:
            q.append((n.left, c - 1))
        if n.right:
            q.append((n.right, c + 1))
    return [cols[k] for k in sorted(cols)]


def ref_boundary(root):
    if not root:
        return []
    if not root.left and not root.right:
        return [root.val]

    def is_leaf(n):
        return n and not n.left and not n.right

    left_b, leaves, right_b = [], [], []

    def go_left(n):
        while n:
            if not is_leaf(n):
                left_b.append(n.val)
            n = n.left if n.left else n.right

    def go_right(n):
        while n:
            if not is_leaf(n):
                right_b.append(n.val)
            n = n.right if n.right else n.left

    def go_leaves(n):
        if not n:
            return
        if is_leaf(n):
            leaves.append(n.val)
            return
        go_leaves(n.left)
        go_leaves(n.right)

    go_left(root.left)
    go_leaves(root)
    go_right(root.right)
    return [root.val] + left_b + leaves + list(reversed(right_b))


def ref_cousin_values(root, x, y):
    # return True if x,y are cousins (same depth, different parent)
    def find(n, target, parent, depth):
        if not n:
            return None
        if n.val == target:
            return parent, depth
        return find(n.left, target, n, depth + 1) or find(n.right, target, n, depth + 1)

    a = find(root, x, None, 0)
    b = find(root, y, None, 0)
    if not a or not b:
        return False
    return a[1] == b[1] and a[0] is not b[0]


def ref_distance_k(root, target_val, k):
    # build parent links
    parent = {}

    def link(n, p):
        if not n:
            return
        parent[n] = p
        link(n.left, n)
        link(n.right, n)

    link(root, None)
    target = find_node(root, target_val)
    res = []
    seen = {target}

    def dfs(n, dist):
        if not n:
            return
        if dist == k:
            res.append(n.val)
            return
        for nxt in (n.left, n.right, parent.get(n)):
            if nxt and nxt not in seen:
                seen.add(nxt)
                dfs(nxt, dist + 1)

    dfs(target, 0)
    return sorted(res)


def ref_house_robber_iii(root):
    def dfs(n):
        if not n:
            return (0, 0)  # rob, skip
        lr, ls = dfs(n.left)
        rr, rs = dfs(n.right)
        rob = n.val + ls + rs
        skip = max(lr, ls) + max(rr, rs)
        return rob, skip

    return max(dfs(root))


def ref_longest_univalue_path(root):
    best = [0]

    def dfs(n):
        if not n:
            return 0
        L, R = dfs(n.left), dfs(n.right)
        left = L + 1 if n.left and n.left.val == n.val else 0
        right = R + 1 if n.right and n.right.val == n.val else 0
        best[0] = max(best[0], left + right)
        return max(left, right)

    dfs(root)
    return best[0]


def ref_sum_of_left_leaves(root):
    if not root:
        return 0
    ans = 0
    if root.left and not root.left.left and not root.left.right:
        ans += root.left.val
    return ans + ref_sum_of_left_leaves(root.left) + ref_sum_of_left_leaves(root.right)


def ref_find_bottom_left(root):
    levels = ref_level_order(root)
    return levels[-1][0] if levels else None


def ref_largest_values(root):
    return [max(lv) for lv in ref_level_order(root)]


def ref_find_target_leaf(root, target):
    # whether any root-to-leaf path equals target (alias hasPathSum)
    return ref_has_path_sum(root, target)


def ref_construct_from_pre_post(pre, post):
    # unique when full binary tree; general: take first as root
    if not pre:
        return None
    root = TreeNode(pre[0])
    if len(pre) == 1:
        return root
    # left root is pre[1]; find in post
    left_root = pre[1]
    idx = post.index(left_root)
    left_sz = idx + 1
    root.left = ref_construct_from_pre_post(pre[1 : 1 + left_sz], post[:left_sz])
    root.right = ref_construct_from_pre_post(pre[1 + left_sz :], post[left_sz:-1])
    return root


def ref_bst_from_preorder(preorder):
    if not preorder:
        return None
    root = TreeNode(preorder[0])
    i = 1
    while i < len(preorder) and preorder[i] < preorder[0]:
        i += 1
    root.left = ref_bst_from_preorder(preorder[1:i])
    root.right = ref_bst_from_preorder(preorder[i:])
    return root


def ref_recover_bst_vals(root):
    # return inorder after recover (swap two nodes) — for expected we return sorted inorder of values as tree list via rebuilding
    vals = ref_inorder(root)
    fixed = sorted(vals)
    # rebuild BST from fixed sorted array for a canonical expected tree
    return tree_to_list(ref_sorted_array_to_bst(fixed))


def ref_delete_node_bst(root, key):
    if not root:
        return None
    if key < root.val:
        root.left = ref_delete_node_bst(root.left, key)
    elif key > root.val:
        root.right = ref_delete_node_bst(root.right, key)
    else:
        if not root.left:
            return root.right
        if not root.right:
            return root.left
        succ = root.right
        while succ.left:
            succ = succ.left
        root.val = succ.val
        root.right = ref_delete_node_bst(root.right, succ.val)
    return root


def ref_is_even_odd_tree(root):
    levels = ref_level_order(root)
    for i, lv in enumerate(levels):
        if i % 2 == 0:
            # even: odd vals, strictly increasing
            prev = float("-inf")
            for v in lv:
                if v % 2 == 0 or v <= prev:
                    return False
                prev = v
        else:
            prev = float("inf")
            for v in lv:
                if v % 2 == 1 or v >= prev:
                    return False
                prev = v
    return True


def ref_pseudo_palindromic_paths(root):
    def dfs(n, mask):
        if not n:
            return 0
        mask ^= 1 << (n.val)
        if not n.left and not n.right:
            return 1 if mask & (mask - 1) == 0 else 0
        return dfs(n.left, mask) + dfs(n.right, mask)

    return dfs(root, 0)


def ref_max_level_sum(root):
    levels = ref_level_order(root)
    best_i, best_s = 1, float("-inf")
    for i, lv in enumerate(levels, 1):
        s = sum(lv)
        if s > best_s:
            best_s, best_i = s, i
    return best_i


def ref_all_possible_fbt_count(n):
    # return count of full binary trees with n nodes (vals all 0) — for tests return number
    memo = {0: 0, 1: 1}

    def count(k):
        if k in memo:
            return memo[k]
        if k % 2 == 0:
            memo[k] = 0
            return 0
        ans = 0
        for L in range(1, k, 2):
            R = k - 1 - L
            ans += count(L) * count(R)
        memo[k] = ans
        return ans

    return count(n)


def ref_distribute_coins(root):
    moves = [0]

    def dfs(n):
        if not n:
            return 0
        L, R = dfs(n.left), dfs(n.right)
        moves[0] += abs(L) + abs(R)
        return n.val + L + R - 1

    dfs(root)
    return moves[0]


def ref_tilt(root):
    total = [0]

    def dfs(n):
        if not n:
            return 0
        L, R = dfs(n.left), dfs(n.right)
        total[0] += abs(L - R)
        return n.val + L + R

    dfs(root)
    return total[0]


def ref_find_duplicate_subtrees(root):
    from collections import defaultdict

    seen = defaultdict(int)
    res = []

    def dfs(n):
        if not n:
            return "#"
        key = f"{n.val},{dfs(n.left)},{dfs(n.right)}"
        seen[key] += 1
        if seen[key] == 2:
            res.append(n.val)  # store root vals of duplicate subtrees for simple compare
        return key

    dfs(root)
    return sorted(res)


def ref_linked_list_in_tree(head_list, root):
    # head given as array of values
    def match(node, arr, i):
        if i == len(arr):
            return True
        if not node or node.val != arr[i]:
            return False
        return match(node.left, arr, i + 1) or match(node.right, arr, i + 1)

    def dfs(node):
        if not node:
            return False
        return match(node, head_list, 0) or dfs(node.left) or dfs(node.right)

    return dfs(root)


def ref_sufficient_subset(root, limit):
    def dfs(n, acc):
        if not n:
            return None
        acc += n.val
        if not n.left and not n.right:
            return n if acc >= limit else None
        n.left = dfs(n.left, acc)
        n.right = dfs(n.right, acc)
        if not n.left and not n.right:
            return None
        return n

    return dfs(root, 0)


def ref_bst_to_gst(root):
    s = [0]

    def dfs(n):
        if not n:
            return
        dfs(n.right)
        s[0] += n.val
        n.val = s[0]
        dfs(n.left)

    dfs(root)
    return root


def ref_balance_bst(root):
    vals = ref_inorder(root)
    return ref_sorted_array_to_bst(vals)


def ref_max_ancestor_diff(root):
    best = [0]

    def dfs(n, mn, mx):
        if not n:
            return
        best[0] = max(best[0], abs(n.val - mn), abs(n.val - mx))
        nmn, nmx = min(mn, n.val), max(mx, n.val)
        dfs(n.left, nmn, nmx)
        dfs(n.right, nmn, nmx)

    if root:
        dfs(root, root.val, root.val)
    return best[0]


def ref_smallest_from_leaf(root):
    best = [None]

    def dfs(n, path):
        if not n:
            return
        path.append(chr(ord("a") + n.val))
        if not n.left and not n.right:
            s = "".join(reversed(path))
            if best[0] is None or s < best[0]:
                best[0] = s
        dfs(n.left, path)
        dfs(n.right, path)
        path.pop()

    dfs(root, [])
    return best[0] or ""


def ref_flip_equiv(root1, root2):
    if not root1 and not root2:
        return True
    if not root1 or not root2 or root1.val != root2.val:
        return False
    return (
        ref_flip_equiv(root1.left, root2.left) and ref_flip_equiv(root1.right, root2.right)
    ) or (
        ref_flip_equiv(root1.left, root2.right) and ref_flip_equiv(root1.right, root2.left)
    )


def ref_del_nodes(root, to_delete):
    delete = set(to_delete)
    forest = []

    def dfs(n, is_root):
        if not n:
            return None
        deleted = n.val in delete
        if is_root and not deleted:
            forest.append(n.val)  # collect root vals of remaining trees
        n.left = dfs(n.left, deleted)
        n.right = dfs(n.right, deleted)
        return None if deleted else n

    dfs(root, True)
    return sorted(forest)


def ref_is_complete(root):
    if not root:
        return True
    q = deque([root])
    seen_null = False
    while q:
        n = q.popleft()
        if not n:
            seen_null = True
            continue
        if seen_null:
            return False
        q.append(n.left)
        q.append(n.right)
    return True


def ref_populate_next_right_vals(root):
    # perfect tree next pointers — return level-order with '#' separators as list of vals per level joined
    levels = ref_level_order(root)
    out = []
    for lv in levels:
        out.extend(lv)
        out.append("#")
    return out


def ref_sum_numbers_alt(root):
    return ref_sum_root_to_leaf_numbers(root)


def ref_get_directions(root, start, dest):
    def path(n, target, acc):
        if not n:
            return False
        if n.val == target:
            return True
        acc.append("L")
        if path(n.left, target, acc):
            return True
        acc.pop()
        acc.append("R")
        if path(n.right, target, acc):
            return True
        acc.pop()
        return False

    ps, pd = [], []
    path(root, start, ps)
    path(root, dest, pd)
    i = 0
    while i < len(ps) and i < len(pd) and ps[i] == pd[i]:
        i += 1
    return "U" * (len(ps) - i) + "".join(pd[i:])


def ref_amount_of_time(root, start):
    parent = {}

    def link(n, p):
        if not n:
            return
        parent[n] = p
        link(n.left, n)
        link(n.right, n)

    link(root, None)
    start_n = find_node(root, start)
    seen = {start_n}
    q = deque([(start_n, 0)])
    ans = 0
    while q:
        n, d = q.popleft()
        ans = d
        for nxt in (n.left, n.right, parent.get(n)):
            if nxt and nxt not in seen:
                seen.add(nxt)
                q.append((nxt, d + 1))
    return ans


def ref_evaluate_boolean(root):
    # Leaf 0/1; 2=OR 3=AND
    if not root:
        return False
    if root.val in (0, 1):
        return bool(root.val)
    L = ref_evaluate_boolean(root.left)
    R = ref_evaluate_boolean(root.right)
    return (L or R) if root.val == 2 else (L and R)


def ref_check_tree_eq_children(root):
    # root.val == left+right for every non-leaf? LeetCode 2236 only root
    if not root or (not root.left and not root.right):
        return True
    s = 0
    if root.left:
        s += root.left.val
    if root.right:
        s += root.right.val
    return root.val == s


def ref_count_good_nodes(root):
    return ref_good_nodes(root)


def ref_min_diff_bst(root):
    vals = ref_inorder(root)
    return min(vals[i + 1] - vals[i] for i in range(len(vals) - 1)) if len(vals) > 1 else 0


def ref_get_all_elements(root1, root2):
    return sorted(ref_inorder(root1) + ref_inorder(root2))


def ref_btree_game_winning_move(root, n, x):
    # whether second player can win choosing parent/left/right of x
    cnt = [0]

    def size(node):
        if not node:
            return 0
        return 1 + size(node.left) + size(node.right)

    def find(node):
        if not node:
            return None
        if node.val == x:
            return node
        return find(node.left) or find(node.right)

    xn = find(root)
    left = size(xn.left)
    right = size(xn.right)
    parent = n - left - right - 1
    return max(left, right, parent) > n // 2


def ref_longest_zigzag(root):
    best = [0]

    def dfs(n, left, length):
        if not n:
            return
        best[0] = max(best[0], length)
        if left:
            dfs(n.left, False, length + 1)
            dfs(n.right, True, 1)
        else:
            dfs(n.right, True, length + 1)
            dfs(n.left, False, 1)

    dfs(root, True, 0)
    dfs(root, False, 0)
    return best[0]


def ref_lowest_common_ancestor_iii_vals(root, p, q):
    # same as binary tree LCA returning val
    pn, qn = find_node(root, p), find_node(root, q)
    node = ref_lowest_common_ancestor(root, pn, qn)
    return node.val if node else None


def ref_distance_between_nodes(root, p, q):
    lca = ref_lowest_common_ancestor(root, find_node(root, p), find_node(root, q))

    def dist(n, t, d):
        if not n:
            return -1
        if n.val == t:
            return d
        L = dist(n.left, t, d + 1)
        if L >= 0:
            return L
        return dist(n.right, t, d + 1)

    return dist(lca, p, 0) + dist(lca, q, 0)


def ref_inorder_successor(root, p_val):
    p = find_node(root, p_val)
    succ = None
    while root:
        if p.val < root.val:
            succ = root
            root = root.left
        else:
            root = root.right
    return succ.val if succ else None


def ref_inorder_predecessor(root, p_val):
    p = find_node(root, p_val)
    pred = None
    while root:
        if p.val > root.val:
            pred = root
            root = root.right
        else:
            root = root.left
    return pred.val if pred else None


def ref_verify_preorder_bst(preorder):
    stack = []
    lower = float("-inf")
    for v in preorder:
        if v < lower:
            return False
        while stack and v > stack[-1]:
            lower = stack.pop()
        stack.append(v)
    return True


def ref_postorder_iterative_vals(root):
    return ref_postorder(root)


def ref_nary_like_children_sum(root):
    # every non-leaf: val == sum(children) — binary version
    def ok(n):
        if not n or (not n.left and not n.right):
            return True
        s = 0
        if n.left:
            s += n.left.val
        if n.right:
            s += n.right.val
        return n.val == s and ok(n.left) and ok(n.right)

    return ok(root)


def ref_convert_bi_node(root):
    # inorder to right-linked list
    vals = ref_inorder(root)
    dummy = TreeNode(0)
    cur = dummy
    for v in vals:
        cur.right = TreeNode(v)
        cur = cur.right
    return dummy.right


def ref_print_tree(root):
    h = ref_max_depth(root)
    m, n = h, (1 << h) - 1
    res = [[""] * n for _ in range(m)]

    def fill(node, r, c):
        if not node:
            return
        res[r][c] = str(node.val)
        if r + 1 < m:
            fill(node.left, r + 1, c - (1 << (h - r - 2)))
            fill(node.right, r + 1, c + (1 << (h - r - 2)))

    fill(root, 0, (n - 1) // 2)
    return res


def ref_leaf_similar(root1, root2):
    def leaves(n, acc):
        if not n:
            return
        if not n.left and not n.right:
            acc.append(n.val)
            return
        leaves(n.left, acc)
        leaves(n.right, acc)

    a, b = [], []
    leaves(root1, a)
    leaves(root2, b)
    return a == b


def ref_max_product_split(root):
    MOD = 10**9 + 7
    total = ref_sum_nodes(root)
    best = [0]

    def dfs(n):
        if not n:
            return 0
        s = n.val + dfs(n.left) + dfs(n.right)
        best[0] = max(best[0], s * (total - s))
        return s

    dfs(root)
    return best[0] % MOD


def ref_create_binary_tree_from_desc(descriptions):
    nodes = {}
    children = set()
    for p, c, is_left in descriptions:
        if p not in nodes:
            nodes[p] = TreeNode(p)
        if c not in nodes:
            nodes[c] = TreeNode(c)
        if is_left:
            nodes[p].left = nodes[c]
        else:
            nodes[p].right = nodes[c]
        children.add(c)
    root_val = next(v for v in nodes if v not in children)
    return nodes[root_val]


def ref_reverse_odd_levels(root):
    if not root:
        return None
    q = deque([root])
    level = 0
    while q:
        nodes = list(q)
        if level % 2 == 1:
            i, j = 0, len(nodes) - 1
            while i < j:
                nodes[i].val, nodes[j].val = nodes[j].val, nodes[i].val
                i += 1
                j -= 1
        for _ in range(len(q)):
            n = q.popleft()
            if n.left:
                q.append(n.left)
            if n.right:
                q.append(n.right)
        level += 1
    return root


def ref_count_pairs_distance(root, distance):
    # number of leaf pairs with distance <= distance
    count = [0]

    def dfs(n):
        if not n:
            return []
        if not n.left and not n.right:
            return [1]
        L, R = dfs(n.left), dfs(n.right)
        for a in L:
            for b in R:
                if a + b <= distance:
                    count[0] += 1
        return [d + 1 for d in L + R if d + 1 < distance]

    dfs(root)
    return count[0]


# ── Problem catalog builder ───────────────────────────────────────────────────
ProblemDef = dict


def T(label, args, sample=False, hint=None):
    return {"inputLabel": label, "args": args, "sample": sample, "hint": hint}


def compute_expected(mode: str, fn: Callable, args: list) -> Any:
    if mode == "serialize":
        root = build_tree(args[0])
        return tree_to_list(root)
    if mode == "lca":
        root = build_tree(args[0])
        p, q = find_node(root, args[1]), find_node(root, args[2])
        node = fn(root, p, q)
        return None if node is None else node.val
    if mode in ("tree_return", "value"):
        prepared = []
        for i, a in enumerate(args):
            if isinstance(a, list) and (
                len(a) == 0 or all(x is None or isinstance(x, (int, float)) for x in a)
            ):
                if i == 0:
                    prepared.append(build_tree(a))
                else:
                    prepared.append(a)
            else:
                prepared.append(a)
        res = fn(*prepared)
        if mode == "tree_return":
            return tree_to_list(res)
        return res
    if mode == "trees":
        prepared = []
        for a in args:
            if isinstance(a, list) and (
                len(a) == 0 or all(x is None or isinstance(x, (int, float)) for x in a)
            ):
                prepared.append(build_tree(a))
            else:
                prepared.append(a)
        return fn(*prepared)
    if mode == "trees_return":
        prepared = []
        for a in args:
            if isinstance(a, list) and (
                len(a) == 0 or all(x is None or isinstance(x, (int, float)) for x in a)
            ):
                prepared.append(build_tree(a))
            else:
                prepared.append(a)
        return tree_to_list(fn(*prepared))
    if mode == "raw":
        return fn(*args)
    if mode == "raw_tree_return":
        return tree_to_list(fn(*args))
    raise ValueError(mode)


def P(
    id_,
    title,
    topic,
    difficulty,
    statement,
    examples,
    fn_name,
    sig,
    comment,
    mode,
    ref,
    tests,
    constraints=None,
    harness=None,
):
    return {
        "id": id_,
        "title": title,
        "topic": topic,
        "difficulty": difficulty,
        "statement": statement,
        "examples": examples,
        "constraints": constraints or DEFAULT_CONSTRAINTS,
        "functionName": fn_name,
        "starterCode": starter(fn_name, sig, comment),
        "judgeMode": mode,
        "cAbi": (
            {"params": [], "returnKind": "serialize"}
            if mode == "serialize"
            else analyze_c_abi(sig)
        ),
        "harnessExtras": harness,
        "ref": ref,
        "tests_raw": tests,
    }


def build_catalog() -> list[ProblemDef]:
    C: list[ProblemDef] = []

    # ========== 1. 遍历与序列 (13) ==========
    C += [
        P(
            "preorder",
            "二叉树的前序遍历",
            "traversal",
            "简单",
            "给定二叉树根节点 `root`，返回前序遍历（根→左→右）。",
            [{"input": "root = [1,null,2,3]", "output": "[1,2,3]"}],
            "preorderTraversal",
            "(root: Optional[TreeNode]) -> List[int]",
            "返回前序序列",
            "value",
            ref_preorder,
            [
                T("root = [1,null,2,3]", [[1, None, 2, 3]], True),
                T("root = []", [[]], True),
                T("root = [1]", [[1]], True),
                T("root = [1,2,3,4,5]", [[1, 2, 3, 4, 5]], hint="顺序不对：前序是根→左→右"),
                T("root = [3,1,null,null,2]", [[3, 1, None, None, 2]]),
            ],
        ),
        P(
            "inorder",
            "二叉树的中序遍历",
            "traversal",
            "简单",
            "给定根节点 `root`，返回中序遍历（左→根→右）。",
            [{"input": "root = [1,null,2,3]", "output": "[1,3,2]"}],
            "inorderTraversal",
            "(root: Optional[TreeNode]) -> List[int]",
            "返回中序序列",
            "value",
            ref_inorder,
            [
                T("root = [1,null,2,3]", [[1, None, 2, 3]], True),
                T("root = []", [[]], True),
                T("root = [1,2,3,4,5]", [[1, 2, 3, 4, 5]], hint="中序是左→根→右"),
                T("root = [2,1,3]", [[2, 1, 3]]),
            ],
        ),
        P(
            "postorder",
            "二叉树的后序遍历",
            "traversal",
            "简单",
            "给定根节点 `root`，返回后序遍历（左→右→根）。",
            [{"input": "root = [1,null,2,3]", "output": "[3,2,1]"}],
            "postorderTraversal",
            "(root: Optional[TreeNode]) -> List[int]",
            "返回后序序列",
            "value",
            ref_postorder,
            [
                T("root = [1,null,2,3]", [[1, None, 2, 3]], True),
                T("root = []", [[]], True),
                T("root = [1,2,3]", [[1, 2, 3]], hint="后序最后才访问根"),
                T("root = [1,2,null,3]", [[1, 2, None, 3]]),
            ],
        ),
        P(
            "preorder-iterative-check",
            "前序遍历（勿用递归也可）",
            "traversal",
            "中等",
            "再次实现前序遍历。可用栈模拟递归。",
            [{"input": "root = [1,2,3]", "output": "[1,2,3]"}],
            "preorderTraversal",
            "(root: Optional[TreeNode]) -> List[int]",
            "可用迭代栈",
            "value",
            ref_preorder,
            [
                T("root = [1,2,3]", [[1, 2, 3]], True),
                T("root = [1,null,2,3]", [[1, None, 2, 3]]),
                T("root = []", [[]]),
            ],
        ),
        P(
            "inorder-iterative-check",
            "中序遍历（迭代友好）",
            "traversal",
            "中等",
            "实现中序遍历；经典写法是用栈一路向左。",
            [{"input": "root = [2,1,3]", "output": "[1,2,3]"}],
            "inorderTraversal",
            "(root: Optional[TreeNode]) -> List[int]",
            "中序迭代",
            "value",
            ref_inorder,
            [
                T("root = [2,1,3]", [[2, 1, 3]], True),
                T("root = [1,null,2,3]", [[1, None, 2, 3]]),
                T("root = [1,2,3,4,5,6,7]", [[1, 2, 3, 4, 5, 6, 7]]),
            ],
        ),
        P(
            "postorder-two-stack",
            "后序遍历再练",
            "traversal",
            "中等",
            "实现后序遍历（左→右→根）。",
            [{"input": "root = [1,2,3]", "output": "[2,3,1]"}],
            "postorderTraversal",
            "(root: Optional[TreeNode]) -> List[int]",
            "后序",
            "value",
            ref_postorder,
            [
                T("root = [1,2,3]", [[1, 2, 3]], True),
                T("root = [1,null,2,3]", [[1, None, 2, 3]]),
                T("root = [3,1,2]", [[3, 1, 2]]),
            ],
        ),
        P(
            "nary-preorder-binary-sim",
            "先根序列一致性检查",
            "traversal",
            "简单",
            "对给定二叉树返回前序序列（用于巩固根优先访问）。",
            [{"input": "root = [5,3,8]", "output": "[5,3,8]"}],
            "preorderTraversal",
            "(root: Optional[TreeNode]) -> List[int]",
            "前序",
            "value",
            ref_preorder,
            [
                T("root = [5,3,8]", [[5, 3, 8]], True),
                T("root = [1]", [[1]]),
                T("root = [4,2,6,1,3,5,7]", [[4, 2, 6, 1, 3, 5, 7]]),
            ],
        ),
        P(
            "tree-to-inorder-list",
            "输出中序值列表",
            "traversal",
            "简单",
            "返回中序遍历得到的节点值列表。",
            [{"input": "root = [4,2,6,1,3,5,7]", "output": "[1,2,3,4,5,6,7]"}],
            "inorderTraversal",
            "(root: Optional[TreeNode]) -> List[int]",
            "中序列表",
            "value",
            ref_inorder,
            [
                T("root = [4,2,6,1,3,5,7]", [[4, 2, 6, 1, 3, 5, 7]], True),
                T("root = [1,null,2]", [[1, None, 2]]),
                T("root = []", [[]]),
            ],
        ),
        P(
            "postorder-leaves-last",
            "后序中叶子更早出现",
            "traversal",
            "简单",
            "返回后序遍历序列，观察叶子相对根的位置。",
            [{"input": "root = [1,2,3,4,5]", "output": "[4,5,2,3,1]"}],
            "postorderTraversal",
            "(root: Optional[TreeNode]) -> List[int]",
            "后序",
            "value",
            ref_postorder,
            [
                T("root = [1,2,3,4,5]", [[1, 2, 3, 4, 5]], True),
                T("root = [1,2]", [[1, 2]]),
                T("root = [2,1,3,null,null,null,4]", [[2, 1, 3, None, None, None, 4]]),
            ],
        ),
        P(
            "morris-inorder-result",
            "中序结果（可 Morris）",
            "traversal",
            "困难",
            "返回中序遍历结果。进阶可用 Morris 遍历做到 O(1) 额外空间。",
            [{"input": "root = [3,1,4,null,2]", "output": "[1,2,3,4]"}],
            "inorderTraversal",
            "(root: Optional[TreeNode]) -> List[int]",
            "中序（可 Morris）",
            "value",
            ref_inorder,
            [
                T("root = [3,1,4,null,2]", [[3, 1, 4, None, 2]], True),
                T("root = [1,2,3]", [[1, 2, 3]]),
                T("root = [5,3,7,2,4,6,8]", [[5, 3, 7, 2, 4, 6, 8]]),
            ],
        ),
        P(
            "preorder-only-values",
            "只要前序值",
            "traversal",
            "简单",
            "实现 `preorderTraversal`。",
            [{"input": "root = [8,4,12]", "output": "[8,4,12]"}],
            "preorderTraversal",
            "(root: Optional[TreeNode]) -> List[int]",
            "前序",
            "value",
            ref_preorder,
            [
                T("root = [8,4,12]", [[8, 4, 12]], True),
                T("root = [8,4,12,2,6]", [[8, 4, 12, 2, 6]]),
                T("root = []", [[]]),
            ],
        ),
        P(
            "traversal-empty-and-single",
            "空树与单节点前序",
            "traversal",
            "简单",
            "处理空树与单节点时的前序遍历。",
            [{"input": "root = []", "output": "[]"}],
            "preorderTraversal",
            "(root: Optional[TreeNode]) -> List[int]",
            "注意空树",
            "value",
            ref_preorder,
            [
                T("root = []", [[]], True, hint="空树应返回 [] 而非 [None] 或报错"),
                T("root = [0]", [[0]], True),
                T("root = [1,0,2]", [[1, 0, 2]]),
            ],
        ),
        P(
            "inorder-bst-sorted",
            "BST 中序有序性",
            "traversal",
            "简单",
            "对一棵 BST 做中序遍历，结果应为升序。",
            [{"input": "root = [2,1,3]", "output": "[1,2,3]"}],
            "inorderTraversal",
            "(root: Optional[TreeNode]) -> List[int]",
            "BST 中序",
            "value",
            ref_inorder,
            [
                T("root = [2,1,3]", [[2, 1, 3]], True),
                T("root = [5,3,7,2,4,6,8]", [[5, 3, 7, 2, 4, 6, 8]]),
                T("root = [1]", [[1]]),
            ],
        ),
    ]

    # ========== 2. 基础属性 (13) ==========
    C += [
        P(
            "max-depth",
            "二叉树的最大深度",
            "basics",
            "简单",
            "返回二叉树最大深度（根到最远叶子的节点数）。",
            [{"input": "root = [3,9,20,null,null,15,7]", "output": "3"}],
            "maxDepth",
            "(root: Optional[TreeNode]) -> int",
            "最大深度",
            "value",
            ref_max_depth,
            [
                T("root = [3,9,20,null,null,15,7]", [[3, 9, 20, None, None, 15, 7]], True),
                T("root = [1,null,2]", [[1, None, 2]], True),
                T("root = []", [[]], hint="空树深度为 0"),
                T("root = [1,2,null,3,null,4]", [[1, 2, None, 3, None, 4]], hint="可能 off-by-one"),
            ],
        ),
        P(
            "min-depth",
            "二叉树的最小深度",
            "basics",
            "简单",
            "最小深度是根到最近叶子的节点数。注意只有一边子树时不能取 0。",
            [{"input": "root = [3,9,20,null,null,15,7]", "output": "2"}],
            "minDepth",
            "(root: Optional[TreeNode]) -> int",
            "最小深度",
            "value",
            ref_min_depth,
            [
                T("root = [3,9,20,null,null,15,7]", [[3, 9, 20, None, None, 15, 7]], True),
                T("root = [2,null,3,null,4,null,5,null,6]", [[2, None, 3, None, 4, None, 5, None, 6]], True, hint="单侧链时最小深度等于节点数"),
                T("root = []", [[]]),
                T("root = [1]", [[1]]),
            ],
        ),
        P(
            "symmetric",
            "对称二叉树",
            "basics",
            "简单",
            "判断二叉树是否镜像对称。",
            [{"input": "root = [1,2,2,3,4,4,3]", "output": "true"}],
            "isSymmetric",
            "(root: Optional[TreeNode]) -> bool",
            "是否对称",
            "value",
            ref_is_symmetric,
            [
                T("root = [1,2,2,3,4,4,3]", [[1, 2, 2, 3, 4, 4, 3]], True),
                T("root = [1,2,2,null,3,null,3]", [[1, 2, 2, None, 3, None, 3]], True, hint="比较外侧与外侧、内侧与内侧"),
                T("root = [1]", [[1]]),
                T("root = [1,2,2,2,null,2]", [[1, 2, 2, 2, None, 2]]),
            ],
        ),
        P(
            "invert-tree",
            "翻转二叉树",
            "basics",
            "简单",
            "翻转一棵二叉树（左右子树交换），返回新根。",
            [{"input": "root = [4,2,7,1,3,6,9]", "output": "[4,7,2,9,6,3,1]"}],
            "invertTree",
            "(root: Optional[TreeNode]) -> Optional[TreeNode]",
            "翻转后返回根",
            "tree_return",
            ref_invert,
            [
                T("root = [4,2,7,1,3,6,9]", [[4, 2, 7, 1, 3, 6, 9]], True),
                T("root = [2,1,3]", [[2, 1, 3]], True),
                T("root = []", [[]]),
            ],
        ),
        P(
            "same-tree",
            "相同的树",
            "basics",
            "简单",
            "判断两棵树 `p` 与 `q` 是否完全相同。",
            [{"input": "p = [1,2,3], q = [1,2,3]", "output": "true"}],
            "isSameTree",
            "(p: Optional[TreeNode], q: Optional[TreeNode]) -> bool",
            "结构与值均相同",
            "trees",
            ref_same_tree,
            [
                T("p = [1,2,3], q = [1,2,3]", [[1, 2, 3], [1, 2, 3]], True),
                T("p = [1,2], q = [1,null,2]", [[1, 2], [1, None, 2]], True),
                T("p = [1,2,1], q = [1,1,2]", [[1, 2, 1], [1, 1, 2]]),
            ],
        ),
        P(
            "balanced",
            "平衡二叉树",
            "basics",
            "简单",
            "判断是否高度平衡：每个节点左右子树高度差不超过 1。",
            [{"input": "root = [3,9,20,null,null,15,7]", "output": "true"}],
            "isBalanced",
            "(root: Optional[TreeNode]) -> bool",
            "是否平衡",
            "value",
            ref_is_balanced,
            [
                T("root = [3,9,20,null,null,15,7]", [[3, 9, 20, None, None, 15, 7]], True),
                T("root = [1,2,2,3,3,null,null,4,4]", [[1, 2, 2, 3, 3, None, None, 4, 4]], True),
                T("root = []", [[]]),
            ],
        ),
        P(
            "diameter",
            "二叉树的直径",
            "basics",
            "简单",
            "直径是任意两节点间最长路径的**边数**。",
            [{"input": "root = [1,2,3,4,5]", "output": "3"}],
            "diameterOfBinaryTree",
            "(root: Optional[TreeNode]) -> int",
            "返回边数",
            "value",
            ref_diameter,
            [
                T("root = [1,2,3,4,5]", [[1, 2, 3, 4, 5]], True),
                T("root = [1,2]", [[1, 2]], True),
                T("root = [1]", [[1]], hint="单节点直径为 0"),
            ],
        ),
        P(
            "count-nodes",
            "统计节点个数",
            "basics",
            "简单",
            "返回二叉树节点总数。",
            [{"input": "root = [1,2,3]", "output": "3"}],
            "countNodes",
            "(root: Optional[TreeNode]) -> int",
            "节点个数",
            "value",
            ref_count_nodes,
            [
                T("root = [1,2,3]", [[1, 2, 3]], True),
                T("root = []", [[]], True),
                T("root = [1,2,3,4,5,6]", [[1, 2, 3, 4, 5, 6]]),
            ],
        ),
        P(
            "sum-nodes",
            "节点值之和",
            "basics",
            "简单",
            "返回所有节点值之和。",
            [{"input": "root = [1,2,3]", "output": "6"}],
            "sumNodes",
            "(root: Optional[TreeNode]) -> int",
            "求和",
            "value",
            ref_sum_nodes,
            [
                T("root = [1,2,3]", [[1, 2, 3]], True),
                T("root = [-1,2]", [[-1, 2]]),
                T("root = []", [[]], True),
            ],
        ),
        P(
            "leaf-count",
            "叶子节点个数",
            "basics",
            "简单",
            "统计叶子节点个数。",
            [{"input": "root = [1,2,3,4]", "output": "2"}],
            "countLeaves",
            "(root: Optional[TreeNode]) -> int",
            "叶子数",
            "value",
            ref_leaf_count,
            [
                T("root = [1,2,3,4]", [[1, 2, 3, 4]], True),
                T("root = [1]", [[1]], True),
                T("root = []", [[]]),
            ],
        ),
        P(
            "univalued",
            "单值二叉树",
            "basics",
            "简单",
            "若所有节点值相同返回 true。",
            [{"input": "root = [1,1,1,1,1,null,1]", "output": "true"}],
            "isUnivalTree",
            "(root: Optional[TreeNode]) -> bool",
            "是否单值",
            "value",
            ref_is_unival,
            [
                T("root = [1,1,1,1,1,null,1]", [[1, 1, 1, 1, 1, None, 1]], True),
                T("root = [2,2,2,5,2]", [[2, 2, 2, 5, 2]], True),
                T("root = [1]", [[1]]),
            ],
        ),
        P(
            "merge-trees",
            "合并二叉树",
            "basics",
            "简单",
            "将两棵树合并：重叠节点值相加，返回新树根。",
            [{"input": "t1 = [1,3,2,5], t2 = [2,1,3,null,4,null,7]", "output": "[3,4,5,5,4,null,7]"}],
            "mergeTrees",
            "(t1: Optional[TreeNode], t2: Optional[TreeNode]) -> Optional[TreeNode]",
            "合并两树",
            "trees_return",
            ref_merge_trees,
            [
                T("t1=[1,3,2,5], t2=[2,1,3,null,4,null,7]", [[1, 3, 2, 5], [2, 1, 3, None, 4, None, 7]], True),
                T("t1=[1], t2=[1,2]", [[1], [1, 2]]),
                T("t1=[], t2=[1]", [[], [1]]),
            ],
        ),
        P(
            "is-complete-tree",
            "完全二叉树判定",
            "basics",
            "中等",
            "判断是否为完全二叉树（层序中 null 后不能再有节点）。",
            [{"input": "root = [1,2,3,4,5,6]", "output": "true"}],
            "isCompleteTree",
            "(root: Optional[TreeNode]) -> bool",
            "是否完全",
            "value",
            ref_is_complete,
            [
                T("root = [1,2,3,4,5,6]", [[1, 2, 3, 4, 5, 6]], True),
                T("root = [1,2,3,4,5,null,7]", [[1, 2, 3, 4, 5, None, 7]], True),
                T("root = [1]", [[1]]),
            ],
        ),
    ]

    # Continue in next chunk due to size - I'll append more categories in the same file via a second write or keep going...
    # Actually continue here - path, bst, etc.

    # ========== 3. 路径与递归 (13) ==========
    C += [
        P(
            "path-sum",
            "路径总和",
            "path",
            "简单",
            "判断是否存在根到叶子路径和等于 `targetSum`。",
            [{"input": "root = [5,4,8,11,null,13,4,7,2,null,null,null,1], targetSum = 22", "output": "true"}],
            "hasPathSum",
            "(root: Optional[TreeNode], targetSum: int) -> bool",
            "根到叶路径和",
            "value",
            ref_has_path_sum,
            [
                T("root=[5,4,8,11,null,13,4,7,2,null,null,null,1], target=22", [[5, 4, 8, 11, None, 13, 4, 7, 2, None, None, None, 1], 22], True),
                T("root=[1,2,3], target=5", [[1, 2, 3], 5], True),
                T("root=[], target=0", [[], 0], hint="空树无路径"),
                T("root=[1,2], target=1", [[1, 2], 1], hint="必须到叶子"),
            ],
        ),
        P(
            "path-sum-ii",
            "路径总和 II",
            "path",
            "中等",
            "返回所有根到叶子路径和为 `targetSum` 的路径列表。",
            [{"input": "root = [5,4,8,11,null,13,4,7,2,null,null,5,1], targetSum = 22", "output": "[[5,4,11,2],[5,8,4,5]]"}],
            "pathSum",
            "(root: Optional[TreeNode], targetSum: int) -> List[List[int]]",
            "列出所有路径",
            "value",
            ref_path_sum_all,
            [
                T("经典样例 target=22", [[5, 4, 8, 11, None, 13, 4, 7, 2, None, None, 5, 1], 22], True),
                T("root=[1,2,3], target=5", [[1, 2, 3], 5], True),
                T("root=[1,2], target=0", [[1, 2], 0]),
            ],
        ),
        P(
            "sum-root-to-leaf",
            "求根到叶数字之和",
            "path",
            "中等",
            "根到叶路径表示一个整数（高位在根），返回所有路径数字之和。",
            [{"input": "root = [1,2,3]", "output": "25", "explanation": "12+13=25"}],
            "sumNumbers",
            "(root: Optional[TreeNode]) -> int",
            "数字路径和",
            "value",
            ref_sum_root_to_leaf_numbers,
            [
                T("root = [1,2,3]", [[1, 2, 3]], True),
                T("root = [4,9,0,5,1]", [[4, 9, 0, 5, 1]], True),
                T("root = [1]", [[1]]),
            ],
        ),
        P(
            "binary-tree-paths",
            "二叉树的所有路径",
            "path",
            "简单",
            "返回所有根到叶子路径字符串，格式 `1->2->3`。",
            [{"input": "root = [1,2,3,null,5]", "output": '["1->2->5","1->3"]'}],
            "binaryTreePaths",
            "(root: Optional[TreeNode]) -> List[str]",
            "路径字符串",
            "value",
            ref_binary_tree_paths,
            [
                T("root = [1,2,3,null,5]", [[1, 2, 3, None, 5]], True),
                T("root = [1]", [[1]], True),
                T("root = [1,2,3]", [[1, 2, 3]]),
            ],
        ),
        P(
            "path-sum-iii",
            "路径总和 III",
            "path",
            "中等",
            "统计路径和等于 `targetSum` 的路径条数（路径向下，不必从根开始/到叶结束）。",
            [{"input": "root = [10,5,-3,3,2,null,11,3,-2,null,1], targetSum = 8", "output": "3"}],
            "pathSum",
            "(root: Optional[TreeNode], targetSum: int) -> int",
            "任意向下路径计数",
            "value",
            ref_path_sum_iii,
            [
                T("经典样例 target=8", [[10, 5, -3, 3, 2, None, 11, 3, -2, None, 1], 8], True),
                T("root=[5,4,8,11,null,13,4,7,2,null,null,5,1], target=22", [[5, 4, 8, 11, None, 13, 4, 7, 2, None, None, 5, 1], 22]),
                T("root=[1], target=1", [[1], 1]),
            ],
        ),
        P(
            "sum-of-left-leaves",
            "左叶子之和",
            "path",
            "简单",
            "返回所有左叶子节点值之和。",
            [{"input": "root = [3,9,20,null,null,15,7]", "output": "24"}],
            "sumOfLeftLeaves",
            "(root: Optional[TreeNode]) -> int",
            "左叶子和",
            "value",
            ref_sum_of_left_leaves,
            [
                T("root = [3,9,20,null,null,15,7]", [[3, 9, 20, None, None, 15, 7]], True),
                T("root = [1]", [[1]], True, hint="根不是左叶子"),
                T("root = [1,2,3,4,5]", [[1, 2, 3, 4, 5]]),
            ],
        ),
        P(
            "good-nodes",
            "统计好节点",
            "path",
            "中等",
            "根到该节点路径上所有值都 ≤ 该节点值，则称为好节点。返回好节点个数。",
            [{"input": "root = [3,1,4,3,null,1,5]", "output": "4"}],
            "goodNodes",
            "(root: Optional[TreeNode]) -> int",
            "好节点数",
            "value",
            ref_good_nodes,
            [
                T("root = [3,1,4,3,null,1,5]", [[3, 1, 4, 3, None, 1, 5]], True),
                T("root = [3,3,null,4,2]", [[3, 3, None, 4, 2]], True),
                T("root = [1]", [[1]]),
            ],
        ),
        P(
            "max-ancestor-diff",
            "节点与其祖先的最大差值",
            "path",
            "中等",
            "返回树中「节点与祖先」差的绝对值的最大值。",
            [{"input": "root = [8,3,10,1,6,null,14,null,null,4,7,13]", "output": "7"}],
            "maxAncestorDiff",
            "(root: Optional[TreeNode]) -> int",
            "最大祖先差",
            "value",
            ref_max_ancestor_diff,
            [
                T("root = [8,3,10,1,6,null,14,null,null,4,7,13]", [[8, 3, 10, 1, 6, None, 14, None, None, 4, 7, 13]], True),
                T("root = [1,null,2,null,0,3]", [[1, None, 2, None, 0, 3]]),
                T("root = [2,null,3]", [[2, None, 3]]),
            ],
        ),
        P(
            "longest-univalue-path",
            "最长同值路径",
            "path",
            "中等",
            "同值路径上节点值相同，返回边数最大的同值路径长度。",
            [{"input": "root = [5,4,5,1,1,null,5]", "output": "2"}],
            "longestUnivaluePath",
            "(root: Optional[TreeNode]) -> int",
            "同值路径边数",
            "value",
            ref_longest_univalue_path,
            [
                T("root = [5,4,5,1,1,null,5]", [[5, 4, 5, 1, 1, None, 5]], True),
                T("root = [1,4,5,4,4,null,5]", [[1, 4, 5, 4, 4, None, 5]], True),
                T("root = [1]", [[1]]),
            ],
        ),
        P(
            "pseudo-palindromic-paths",
            "伪回文路径",
            "path",
            "中等",
            "节点值 1–9。统计根到叶路径中，节点值可重排为回文的路径数。",
            [{"input": "root = [2,3,1,3,1,null,1]", "output": "2"}],
            "pseudoPalindromicPaths",
            "(root: Optional[TreeNode]) -> int",
            "伪回文路径数",
            "value",
            ref_pseudo_palindromic_paths,
            [
                T("root = [2,3,1,3,1,null,1]", [[2, 3, 1, 3, 1, None, 1]], True),
                T("root = [2,1,1,1,3,null,null,null,null,null,1]", [[2, 1, 1, 1, 3, None, None, None, None, None, 1]]),
                T("root = [9]", [[9]]),
            ],
        ),
        P(
            "smallest-string-leaf",
            "从叶到根的最小字符串",
            "path",
            "中等",
            "节点值 0–25 映射 a–z。从任意叶子到根拼出字符串，返回字典序最小者。",
            [{"input": "root = [0,1,2,3,4,3,4]", "output": '"dba"'}],
            "smallestFromLeaf",
            "(root: Optional[TreeNode]) -> str",
            "最小叶到根串",
            "value",
            ref_smallest_from_leaf,
            [
                T("root = [0,1,2,3,4,3,4]", [[0, 1, 2, 3, 4, 3, 4]], True),
                T("root = [25,1,3,1,3,0,2]", [[25, 1, 3, 1, 3, 0, 2]], True),
                T("root = [2,2,1,null,1,0,null,0]", [[2, 2, 1, None, 1, 0, None, 0]]),
            ],
        ),
        P(
            "sufficient-subset",
            "不足节点删减",
            "path",
            "中等",
            "若根到叶路径和严格小于 `limit`，删除该路径上的不足节点（见题面惯例），返回处理后的树。",
            [{"input": "root = [1,2,3,4,-99,-99,7,8,9,-99,-99,12,13,-99,14], limit = 1", "output": "[1,2,3,4,null,null,7,8,9,null,14]"}],
            "sufficientSubset",
            "(root: Optional[TreeNode], limit: int) -> Optional[TreeNode]",
            "删不足路径",
            "tree_return",
            ref_sufficient_subset,
            [
                T("limit=1 样例", [[1, 2, 3, 4, -99, -99, 7, 8, 9, -99, -99, 12, 13, -99, 14], 1], True),
                T("root=[1,2,-3,-5,null,4,null], limit=-1", [[1, 2, -3, -5, None, 4], -1]),
                T("root=[5,2], limit=10", [[5, 2], 10]),
            ],
        ),
        P(
            "path-exists-sum",
            "是否存在目标和路径",
            "path",
            "简单",
            "同「路径总和」：是否存在根到叶路径和为 target。",
            [{"input": "root = [1,2], targetSum = 3", "output": "true"}],
            "hasPathSum",
            "(root: Optional[TreeNode], targetSum: int) -> bool",
            "路径存在性",
            "value",
            ref_find_target_leaf,
            [
                T("root=[1,2], target=3", [[1, 2], 3], True),
                T("root=[1,2], target=1", [[1, 2], 1]),
                T("root=[1], target=1", [[1], 1]),
            ],
        ),
    ]

    return C  # temporary - will extend below


def extend_catalog(C: list[ProblemDef]) -> list[ProblemDef]:
    # ========== 4. BST (13) ==========
    C += [
        P(
            "validate-bst",
            "验证二叉搜索树",
            "bst",
            "中等",
            "判断是否为严格 BST（左<根<右，整棵子树）。",
            [{"input": "root = [2,1,3]", "output": "true"}],
            "isValidBST",
            "(root: Optional[TreeNode]) -> bool",
            "验证 BST",
            "value",
            ref_is_valid_bst,
            [
                T("root = [2,1,3]", [[2, 1, 3]], True),
                T("root = [5,1,4,null,null,3,6]", [[5, 1, 4, None, None, 3, 6]], True),
                T("root = [5,4,6,null,null,3,7]", [[5, 4, 6, None, None, 3, 7]], hint="需要上下界"),
                T("root = [1,1]", [[1, 1]], hint="相等不合法"),
            ],
        ),
        P(
            "search-bst",
            "二叉搜索树中的搜索",
            "bst",
            "简单",
            "在 BST 中找值为 `val` 的节点，返回该子树；否则空。",
            [{"input": "root = [4,2,7,1,3], val = 2", "output": "[2,1,3]"}],
            "searchBST",
            "(root: Optional[TreeNode], val: int) -> Optional[TreeNode]",
            "搜索并返回子树",
            "tree_return",
            ref_search_bst,
            [
                T("root=[4,2,7,1,3], val=2", [[4, 2, 7, 1, 3], 2], True),
                T("root=[4,2,7,1,3], val=5", [[4, 2, 7, 1, 3], 5], True),
                T("root=[4,2,7,1,3], val=4", [[4, 2, 7, 1, 3], 4]),
            ],
        ),
        P(
            "insert-bst",
            "二叉搜索树中的插入",
            "bst",
            "中等",
            "向 BST 插入值 `val`，返回新树根（保证原先不存在该值）。",
            [{"input": "root = [4,2,7,1,3], val = 5", "output": "[4,2,7,1,3,5]"}],
            "insertIntoBST",
            "(root: Optional[TreeNode], val: int) -> Optional[TreeNode]",
            "插入",
            "tree_return",
            ref_insert_bst,
            [
                T("root=[4,2,7,1,3], val=5", [[4, 2, 7, 1, 3], 5], True),
                T("root=[40,20,60,10,30,50,70], val=25", [[40, 20, 60, 10, 30, 50, 70], 25]),
                T("root=[], val=1", [[], 1]),
            ],
        ),
        P(
            "delete-bst",
            "删除二叉搜索树中的节点",
            "bst",
            "中等",
            "删除 BST 中值为 `key` 的节点并保持 BST 性质，返回根。",
            [{"input": "root = [5,3,6,2,4,null,7], key = 3", "output": "[5,4,6,2,null,null,7] 或等价 BST"}],
            "deleteNode",
            "(root: Optional[TreeNode], key: int) -> Optional[TreeNode]",
            "删除节点",
            "tree_return",
            ref_delete_node_bst,
            [
                T("root=[5,3,6,2,4,null,7], key=3", [[5, 3, 6, 2, 4, None, 7], 3], True),
                T("root=[5,3,6,2,4,null,7], key=0", [[5, 3, 6, 2, 4, None, 7], 0]),
                T("root=[5,3,6,2,4,null,7], key=5", [[5, 3, 6, 2, 4, None, 7], 5]),
            ],
        ),
        P(
            "kth-smallest",
            "BST 中第 K 小",
            "bst",
            "中等",
            "返回 BST 中第 `k` 小的元素（1-indexed）。",
            [{"input": "root = [3,1,4,null,2], k = 1", "output": "1"}],
            "kthSmallest",
            "(root: Optional[TreeNode], k: int) -> int",
            "第 k 小",
            "value",
            ref_kth_smallest,
            [
                T("root=[3,1,4,null,2], k=1", [[3, 1, 4, None, 2], 1], True),
                T("root=[5,3,6,2,4,null,null,1], k=3", [[5, 3, 6, 2, 4, None, None, 1], 3], True),
                T("root=[1], k=1", [[1], 1]),
            ],
        ),
        P(
            "kth-largest",
            "BST 中第 K 大",
            "bst",
            "中等",
            "返回 BST 中第 `k` 大的元素。",
            [{"input": "root = [3,1,4,null,2], k = 1", "output": "4"}],
            "kthLargest",
            "(root: Optional[TreeNode], k: int) -> int",
            "第 k 大",
            "value",
            ref_kth_largest,
            [
                T("root=[3,1,4,null,2], k=1", [[3, 1, 4, None, 2], 1], True),
                T("root=[5,3,6,2,4], k=2", [[5, 3, 6, 2, 4], 2]),
                T("root=[2,1], k=2", [[2, 1], 2]),
            ],
        ),
        P(
            "range-sum-bst",
            "BST 范围和",
            "bst",
            "简单",
            "返回 BST 中所有满足 `low ≤ val ≤ high` 的节点值之和。",
            [{"input": "root = [10,5,15,3,7,null,18], low = 7, high = 15", "output": "32"}],
            "rangeSumBST",
            "(root: Optional[TreeNode], low: int, high: int) -> int",
            "范围和",
            "value",
            ref_range_sum_bst,
            [
                T("low=7,high=15", [[10, 5, 15, 3, 7, None, 18], 7, 15], True),
                T("low=6,high=10", [[10, 5, 15, 3, 7, 13, 18, 1, None, 6], 6, 10], True),
                T("low=1,high=1", [[1], 1, 1]),
            ],
        ),
        P(
            "trim-bst",
            "修剪二叉搜索树",
            "bst",
            "中等",
            "使所有节点值位于 `[low, high]`，返回修剪后的根。",
            [{"input": "root = [1,0,2], low = 1, high = 2", "output": "[1,null,2]"}],
            "trimBST",
            "(root: Optional[TreeNode], low: int, high: int) -> Optional[TreeNode]",
            "修剪",
            "tree_return",
            ref_trim_bst,
            [
                T("root=[1,0,2], low=1, high=2", [[1, 0, 2], 1, 2], True),
                T("root=[3,0,4,null,2,null,null,1], low=1, high=3", [[3, 0, 4, None, 2, None, None, 1], 1, 3], True),
                T("root=[1], low=1, high=2", [[1], 1, 2]),
            ],
        ),
        P(
            "increasing-bst",
            "递增顺序搜索树",
            "bst",
            "简单",
            "把 BST 重排为只有右孩子的递增链，返回新根。",
            [{"input": "root = [5,3,6,2,4,null,8,1,null,null,null,7,9]", "output": "[1,null,2,null,3,null,4,null,5,null,6,null,7,null,8,null,9]"}],
            "increasingBST",
            "(root: Optional[TreeNode]) -> Optional[TreeNode]",
            "改成右链",
            "tree_return",
            ref_increasing_bst,
            [
                T("样例", [[5, 3, 6, 2, 4, None, 8, 1, None, None, None, 7, 9]], True),
                T("root=[5,1,7]", [[5, 1, 7]]),
                T("root=[2,1]", [[2, 1]]),
            ],
        ),
        P(
            "bst-min-max",
            "BST 的最小值",
            "bst",
            "简单",
            "返回 BST 中的最小节点值。",
            [{"input": "root = [4,2,7,1,3]", "output": "1"}],
            "bstMinValue",
            "(root: Optional[TreeNode]) -> int",
            "最小值",
            "value",
            ref_bst_min,
            [
                T("root=[4,2,7,1,3]", [[4, 2, 7, 1, 3]], True),
                T("root=[2,null,3]", [[2, None, 3]]),
                T("root=[5]", [[5]]),
            ],
        ),
        P(
            "bst-max-value",
            "BST 的最大值",
            "bst",
            "简单",
            "返回 BST 中的最大节点值。",
            [{"input": "root = [4,2,7,1,3]", "output": "7"}],
            "bstMaxValue",
            "(root: Optional[TreeNode]) -> int",
            "最大值",
            "value",
            ref_bst_max,
            [
                T("root=[4,2,7,1,3]", [[4, 2, 7, 1, 3]], True),
                T("root=[2,1]", [[2, 1]]),
                T("root=[5]", [[5]]),
            ],
        ),
        P(
            "closest-bst-value",
            "最接近的 BST 值",
            "bst",
            "简单",
            "在 BST 中找与 `target` 最接近的节点值（并列时返回任一较近者；本题数据保证唯一）。",
            [{"input": "root = [4,2,5,1,3], target = 3.714286", "output": "4"}],
            "closestValue",
            "(root: Optional[TreeNode], target: float) -> int",
            "最接近值",
            "value",
            ref_closest_bst,
            [
                T("target=3.714286", [[4, 2, 5, 1, 3], 3.714286], True),
                T("target=2.1", [[1, None, 2], 2.1]),
                T("target=1.0", [[1], 1.0]),
            ],
        ),
        P(
            "two-sum-bst",
            "两数之和 IV - 输入 BST",
            "bst",
            "简单",
            "判断 BST 中是否存在两个节点值之和为 `k`。",
            [{"input": "root = [5,3,6,2,4,null,7], k = 9", "output": "true"}],
            "findTarget",
            "(root: Optional[TreeNode], k: int) -> bool",
            "两数之和",
            "value",
            ref_two_sum_bst,
            [
                T("k=9", [[5, 3, 6, 2, 4, None, 7], 9], True),
                T("k=28", [[5, 3, 6, 2, 4, None, 7], 28], True),
                T("k=2", [[2, 1, 3], 4]),
            ],
        ),
    ]

    # ========== 5. construct (12) ==========
    C += [
        P(
            "build-tree-pre-in",
            "从前序与中序构造二叉树",
            "construct",
            "中等",
            "根据前序 `preorder` 与中序 `inorder` 构造二叉树（无重复值）。",
            [{"input": "preorder = [3,9,20,15,7], inorder = [9,3,15,20,7]", "output": "[3,9,20,null,null,15,7]"}],
            "buildTree",
            "(preorder: List[int], inorder: List[int]) -> Optional[TreeNode]",
            "前序+中序构造",
            "raw_tree_return",
            ref_build_tree_pre_in,
            [
                T("经典样例", [[3, 9, 20, 15, 7], [9, 3, 15, 20, 7]], True),
                T("单节点", [[-1], [-1]], True),
                T("pre=[1,2,3], in=[2,1,3]", [[1, 2, 3], [2, 1, 3]]),
            ],
        ),
        P(
            "build-tree-in-post",
            "从中序与后序构造二叉树",
            "construct",
            "中等",
            "根据中序与后序构造二叉树。",
            [{"input": "inorder = [9,3,15,20,7], postorder = [9,15,7,20,3]", "output": "[3,9,20,null,null,15,7]"}],
            "buildTree",
            "(inorder: List[int], postorder: List[int]) -> Optional[TreeNode]",
            "中序+后序构造",
            "raw_tree_return",
            ref_build_tree_in_post,
            [
                T("经典样例", [[9, 3, 15, 20, 7], [9, 15, 7, 20, 3]], True),
                T("单节点", [[-1], [-1]]),
                T("in=[2,1], post=[2,1]", [[2, 1], [2, 1]]),
            ],
        ),
        P(
            "sorted-array-to-bst",
            "将有序数组转换为 BST",
            "construct",
            "简单",
            "将升序数组转为高度平衡 BST。",
            [{"input": "nums = [-10,-3,0,5,9]", "output": "[0,-3,9,-10,null,5] 等平衡形态之一"}],
            "sortedArrayToBST",
            "(nums: List[int]) -> Optional[TreeNode]",
            "有序数组转 BST",
            "raw_tree_return",
            ref_sorted_array_to_bst,
            [
                T("nums=[-10,-3,0,5,9]", [[-10, -3, 0, 5, 9]], True),
                T("nums=[1,3]", [[1, 3]], True),
                T("nums=[1]", [[1]]),
            ],
        ),
        P(
            "serialize",
            "二叉树的序列化与反序列化",
            "construct",
            "困难",
            "实现 `serialize` / `deserialize` 互逆。判题对树做 round-trip。",
            [{"input": "root = [1,2,3,null,null,4,5]", "output": "[1,2,3,null,null,4,5]"}],
            "serialize",
            "  # see starter",
            "编解码",
            "serialize",
            ref_serialize_roundtrip,
            [
                T("root=[1,2,3,null,null,4,5]", [[1, 2, 3, None, None, 4, 5]], True),
                T("root=[]", [[]], True, hint="空树也要能编解码"),
                T("root=[1,null,2,null,3]", [[1, None, 2, None, 3]], hint="保留 null"),
            ],
            harness=None,
        ),
        P(
            "bst-from-preorder",
            "先序遍历构造 BST",
            "construct",
            "中等",
            "根据 BST 的先序遍历构造树。",
            [{"input": "preorder = [8,5,1,7,10,12]", "output": "[8,5,10,1,7,null,12]"}],
            "bstFromPreorder",
            "(preorder: List[int]) -> Optional[TreeNode]",
            "先序构 BST",
            "raw_tree_return",
            ref_bst_from_preorder,
            [
                T("preorder=[8,5,1,7,10,12]", [[8, 5, 1, 7, 10, 12]], True),
                T("preorder=[1,3]", [[1, 3]]),
                T("preorder=[3,1,2]", [[3, 1, 2]]),
            ],
        ),
        P(
            "construct-pre-post",
            "根据前序和后序遍历构造二叉树",
            "construct",
            "中等",
            "由前序与后序构造（若有多个答案返回其一；本题数据对应左子树优先划分）。",
            [{"input": "pre = [1,2,4,5,3,6,7], post = [4,5,2,6,7,3,1]", "output": "[1,2,3,4,5,6,7]"}],
            "constructFromPrePost",
            "(pre: List[int], post: List[int]) -> Optional[TreeNode]",
            "前序+后序",
            "raw_tree_return",
            ref_construct_from_pre_post,
            [
                T("样例", [[1, 2, 4, 5, 3, 6, 7], [4, 5, 2, 6, 7, 3, 1]], True),
                T("pre=[1], post=[1]", [[1], [1]]),
                T("pre=[1,2,3], post=[3,2,1]", [[1, 2, 3], [3, 2, 1]]),
            ],
        ),
        P(
            "flatten-tree",
            "二叉树展开为链表",
            "construct",
            "中等",
            "原地展开为先序的右链（左指针全空），返回展开后的根。",
            [{"input": "root = [1,2,5,3,4,null,6]", "output": "[1,null,2,null,3,null,4,null,5,null,6]"}],
            "flatten",
            "(root: Optional[TreeNode]) -> Optional[TreeNode]",
            "展开为右链并返回根",
            "tree_return",
            lambda root: (lambda r: (ref_flatten_preorder_links(r), build_tree(ref_flatten_preorder_links(build_tree(tree_to_list(root))) if False else None))[0] if False else build_tree(ref_flatten_preorder_links(root)))(root),
            [
                T("root=[1,2,5,3,4,null,6]", [[1, 2, 5, 3, 4, None, 6]], True),
                T("root=[]", [[]]),
                T("root=[0]", [[0]]),
            ],
        ),
        P(
            "create-from-descriptions",
            "从描述中创建二叉树",
            "construct",
            "中等",
            "`descriptions[i] = [parent, child, isLeft]`，构造并返回根。",
            [{"input": "descriptions = [[20,15,1],[20,17,0],[50,20,1],[50,80,0],[80,19,1]]", "output": "[50,20,80,15,17,19]"}],
            "createBinaryTree",
            "(descriptions: List[List[int]]) -> Optional[TreeNode]",
            "从描述建树",
            "raw_tree_return",
            ref_create_binary_tree_from_desc,
            [
                T("样例1", [[[20, 15, 1], [20, 17, 0], [50, 20, 1], [50, 80, 0], [80, 19, 1]]], True),
                T("样例2", [[[1, 2, 1], [2, 3, 0], [3, 4, 1]]], True),
                T("单边", [[[1, 2, 0]]]),
            ],
        ),
        P(
            "balance-bst",
            "将 BST 变平衡",
            "construct",
            "中等",
            "把任意 BST 变成平衡 BST，返回新根。",
            [{"input": "root = [1,null,2,null,3,null,4]", "output": "平衡 BST，如 [2,1,3,null,null,null,4]"}],
            "balanceBST",
            "(root: Optional[TreeNode]) -> Optional[TreeNode]",
            "平衡化",
            "tree_return",
            ref_balance_bst,
            [
                T("右链", [[1, None, 2, None, 3, None, 4]], True),
                T("root=[2,1,3]", [[2, 1, 3]]),
                T("root=[1]", [[1]]),
            ],
        ),
        P(
            "convert-binode",
            "二叉搜索树转双向右链",
            "construct",
            "中等",
            "将 BST 转为只有 right 指针的递增链表（本题用右链表示），返回头结点。",
            [{"input": "root = [4,2,5,1,3]", "output": "[1,null,2,null,3,null,4,null,5]"}],
            "convertBiNode",
            "(root: Optional[TreeNode]) -> Optional[TreeNode]",
            "转右链",
            "tree_return",
            ref_convert_bi_node,
            [
                T("root=[4,2,5,1,3]", [[4, 2, 5, 1, 3]], True),
                T("root=[2,1,3]", [[2, 1, 3]]),
                T("root=[1]", [[1]]),
            ],
        ),
        P(
            "recover-bst-canonical",
            "恢复 BST（返回规范树）",
            "construct",
            "困难",
            "有两个节点被错误交换。恢复后返回一棵由排序中序重建的规范平衡 BST（用于判题）。",
            [{"input": "root = [1,3,null,null,2]", "output": "[2,1,3]"}],
            "recoverTree",
            "(root: Optional[TreeNode]) -> Optional[TreeNode]",
            "恢复并返回规范树",
            "tree_return",
            lambda root: ref_sorted_array_to_bst(sorted(ref_inorder(root))),
            [
                T("root=[1,3,null,null,2]", [[1, 3, None, None, 2]], True),
                T("root=[3,1,4,null,null,2]", [[3, 1, 4, None, None, 2]], True),
                T("root=[2,3,1]", [[2, 3, 1]]),
            ],
        ),
        P(
            "print-tree-matrix",
            "输出二叉树矩阵",
            "construct",
            "中等",
            "按题意把树填进 m×n 字符矩阵并返回（空位为 \"\"）。",
            [{"input": "root = [1,2]", "output": '[["","1",""],["2","",""]]'}],
            "printTree",
            "(root: Optional[TreeNode]) -> List[List[str]]",
            "打印矩阵",
            "value",
            ref_print_tree,
            [
                T("root=[1,2]", [[1, 2]], True),
                T("root=[1,2,3,null,4]", [[1, 2, 3, None, 4]], True),
                T("root=[1]", [[1]]),
            ],
        ),
    ]

    # Fix flatten - my lambda was broken. Use a clean wrapper:
    for p in C:
        if p["id"] == "flatten-tree":
            def flatten_ref(root):
                arr = ref_flatten_preorder_links(root)
                return build_tree(arr)

            p["ref"] = flatten_ref

    # Fix serialize starter (C codec pair)
    for p in C:
        if p["id"] == "serialize":
            p["cAbi"] = {"params": [{"name": "root", "kind": "tree"}], "returnKind": "serialize"}
            p["starterCode"] = (
                "/* TreeNode 由判题环境提供 */\n"
                "char* serialize(struct TreeNode* root) {\n"
                "    // 序列化为字符串\n"
                "    return NULL;\n"
                "}\n\n"
                "struct TreeNode* deserialize(char* data) {\n"
                "    // 从字符串还原\n"
                "    return NULL;\n"
                "}\n"
            )

    # ========== 6. LCA (12) ==========
    C += [
        P(
            "lca",
            "二叉树的最近公共祖先",
            "lca",
            "中等",
            "找节点值 `p` 与 `q` 的最近公共祖先，返回其值。树中值唯一且 p、q 均存在。",
            [{"input": "root = [3,5,1,6,2,0,8,null,null,7,4], p = 5, q = 1", "output": "3"}],
            "lowestCommonAncestor",
            "(root: Optional[TreeNode], p: TreeNode, q: TreeNode) -> Optional[TreeNode]",
            "返回 LCA 节点",
            "lca",
            ref_lowest_common_ancestor,
            [
                T("p=5,q=1", [[3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 5, 1], True),
                T("p=5,q=4", [[3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 5, 4], True, hint="节点可以是自己的祖先"),
                T("p=6,q=4", [[3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 6, 4]),
                T("p=1,q=2", [[1, 2], 1, 2]),
            ],
        ),
        P(
            "lca-bst",
            "二叉搜索树的最近公共祖先",
            "lca",
            "中等",
            "在 BST 中找 p、q 的 LCA（利用有序性）。返回值。",
            [{"input": "root = [6,2,8,0,4,7,9,null,null,3,5], p = 2, q = 8", "output": "6"}],
            "lowestCommonAncestor",
            "(root: Optional[TreeNode], p: TreeNode, q: TreeNode) -> Optional[TreeNode]",
            "BST 的 LCA",
            "lca",
            ref_lca_bst,
            [
                T("p=2,q=8", [[6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 2, 8], True),
                T("p=2,q=4", [[6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 2, 4], True),
                T("p=3,q=5", [[6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 3, 5]),
            ],
        ),
        P(
            "lca-deepest-leaves",
            "最深叶节点的 LCA",
            "lca",
            "中等",
            "返回包含所有最深叶子的最小子树根（层序数组）。",
            [{"input": "root = [3,5,1,6,2,0,8,null,null,7,4]", "output": "[2,7,4]"}],
            "subtreeWithAllDeepest",
            "(root: Optional[TreeNode]) -> Optional[TreeNode]",
            "最深叶 LCA 子树",
            "tree_return",
            ref_subtree_with_all_deepest,
            [
                T("经典", [[3, 5, 1, 6, 2, 0, 8, None, None, 7, 4]], True),
                T("root=[1]", [[1]], True),
                T("root=[0,1,3,null,2]", [[0, 1, 3, None, 2]]),
            ],
        ),
        P(
            "distance-k",
            "到目标节点距离为 K 的节点",
            "lca",
            "中等",
            "返回与值为 `target` 的节点距离为 `k` 的所有节点值（排序后比较）。",
            [{"input": "root = [3,5,1,6,2,0,8,null,null,7,4], target = 5, k = 2", "output": "[1,4,7]"}],
            "distanceK",
            "(root: Optional[TreeNode], target: int, k: int) -> List[int]",
            "距离为 k 的节点",
            "value",
            ref_distance_k,
            [
                T("target=5,k=2", [[3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 5, 2], True),
                T("target=5,k=0", [[3, 5, 1], 5, 0]),
                T("target=1,k=1", [[1, 2, 3], 1, 1]),
            ],
        ),
        P(
            "amount-of-time",
            "二叉树中的感染时间",
            "lca",
            "中等",
            "从值为 `start` 的节点开始「感染」整棵树，返回分钟数（边权 1）。",
            [{"input": "root = [1,5,3,null,4,10,6,9,2], start = 3", "output": "4"}],
            "amountOfTime",
            "(root: Optional[TreeNode], start: int) -> int",
            "感染耗时",
            "value",
            ref_amount_of_time,
            [
                T("start=3", [[1, 5, 3, None, 4, 10, 6, 9, 2], 3], True),
                T("start=1", [[1], 1], True),
                T("start=2", [[1, 2, None, 3], 2]),
            ],
        ),
        P(
            "get-directions",
            "从 start 到 dest 的方向字符串",
            "lca",
            "中等",
            "返回从 start 到 dest 仅含 'L','R','U' 的最短路径指令。",
            [{"input": "root = [5,1,2,3,null,6,4], startValue = 3, destValue = 6", "output": '"UURL"'}],
            "getDirections",
            "(root: Optional[TreeNode], startValue: int, destValue: int) -> str",
            "方向串",
            "value",
            ref_get_directions,
            [
                T("3→6", [[5, 1, 2, 3, None, 6, 4], 3, 6], True),
                T("1→2", [[2, 1], 1, 2]),
                T("2→1", [[2, 1], 2, 1]),
            ],
        ),
        P(
            "distance-between",
            "两节点距离",
            "lca",
            "中等",
            "返回树中值为 p、q 的两节点之间的距离（边数）。",
            [{"input": "root = [3,5,1,6,2,0,8,null,null,7,4], p = 5, q = 0", "output": "3"}],
            "distanceBetween",
            "(root: Optional[TreeNode], p: int, q: int) -> int",
            "节点距离",
            "value",
            ref_distance_between_nodes,
            [
                T("5与0", [[3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 5, 0], True),
                T("5与4", [[3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 5, 4]),
                T("1与2", [[1, 2], 1, 2]),
            ],
        ),
        P(
            "is-cousins",
            "堂兄弟节点",
            "lca",
            "简单",
            "判断值 x、y 是否为堂兄弟（深度相同、父节点不同）。",
            [{"input": "root = [1,2,3,4], x = 4, y = 3", "output": "false"}],
            "isCousins",
            "(root: Optional[TreeNode], x: int, y: int) -> bool",
            "是否堂兄弟",
            "value",
            ref_cousin_values,
            [
                T("x=4,y=3", [[1, 2, 3, 4], 4, 3], True),
                T("x=5,y=4", [[1, 2, 3, null := None, 4, null, 5], 5, 4] if False else [[1, 2, 3, None, 4, None, 5], 5, 4], True),
                T("x=2,y=3", [[1, 2, 3], 2, 3]),
            ],
        ),
        P(
            "inorder-successor",
            "中序后继",
            "lca",
            "中等",
            "在 BST 中找值为 `p` 的节点的中序后继值；若无则返回 null（JSON 中为 null）。",
            [{"input": "root = [2,1,3], p = 1", "output": "2"}],
            "inorderSuccessor",
            "(root: Optional[TreeNode], p: int) -> Optional[int]",
            "中序后继值",
            "value",
            ref_inorder_successor,
            [
                T("p=1", [[2, 1, 3], 1], True),
                T("p=2", [[2, 1, 3], 2], True, hint="最大节点无后继"),
                T("p=1", [[5, 3, 6, 2, 4, None, None, 1], 1]),
            ],
        ),
        P(
            "inorder-predecessor",
            "中序前驱",
            "lca",
            "中等",
            "在 BST 中找 `p` 的中序前驱值。",
            [{"input": "root = [2,1,3], p = 2", "output": "1"}],
            "inorderPredecessor",
            "(root: Optional[TreeNode], p: int) -> Optional[int]",
            "中序前驱值",
            "value",
            ref_inorder_predecessor,
            [
                T("p=2", [[2, 1, 3], 2], True),
                T("p=1", [[2, 1, 3], 1], True, hint="最小节点无前驱"),
                T("p=5", [[5, 3, 6, 2, 4], 5]),
            ],
        ),
        P(
            "lca-of-leaves-pair",
            "任意两叶距离相关的 LCA 练习",
            "lca",
            "中等",
            "再次实现通用二叉树 LCA（返回值）。",
            [{"input": "root = [1,2,3], p = 2, q = 3", "output": "1"}],
            "lowestCommonAncestor",
            "(root: Optional[TreeNode], p: TreeNode, q: TreeNode) -> Optional[TreeNode]",
            "LCA",
            "lca",
            ref_lowest_common_ancestor,
            [
                T("p=2,q=3", [[1, 2, 3], 2, 3], True),
                T("p=2,q=1", [[1, 2], 2, 1]),
                T("p=4,q=5", [[1, 2, 3, 4, 5], 4, 5]),
            ],
        ),
        P(
            "find-ancestor-chain-lca",
            "祖先链上的 LCA",
            "lca",
            "简单",
            "当 q 在 p 子树中时 LCA 为 p。实现通用 LCA。",
            [{"input": "root = [1,2,null,3], p = 2, q = 3", "output": "2"}],
            "lowestCommonAncestor",
            "(root: Optional[TreeNode], p: TreeNode, q: TreeNode) -> Optional[TreeNode]",
            "祖先情形",
            "lca",
            ref_lowest_common_ancestor,
            [
                T("p=2,q=3", [[1, 2, None, 3], 2, 3], True),
                T("p=1,q=3", [[1, 2, None, 3], 1, 3]),
                T("p=3,q=2", [[1, 2, None, 3], 3, 2]),
            ],
        ),
    ]

    # ========== 7. levelview (12) ==========
    C += [
        P(
            "level-order",
            "二叉树的层序遍历",
            "levelview",
            "中等",
            "返回逐层节点值（每层一个列表）。",
            [{"input": "root = [3,9,20,null,null,15,7]", "output": "[[3],[9,20],[15,7]]"}],
            "levelOrder",
            "(root: Optional[TreeNode]) -> List[List[int]]",
            "层序",
            "value",
            ref_level_order,
            [
                T("经典", [[3, 9, 20, None, None, 15, 7]], True),
                T("root=[1]", [[1]], True),
                T("root=[]", [[]], True),
                T("root=[1,2,3,4,null,null,5]", [[1, 2, 3, 4, None, None, 5]], hint="按层分包"),
            ],
        ),
        P(
            "level-order-bottom",
            "层序遍历自底向上",
            "levelview",
            "中等",
            "自底向上层序遍历。",
            [{"input": "root = [3,9,20,null,null,15,7]", "output": "[[15,7],[9,20],[3]]"}],
            "levelOrderBottom",
            "(root: Optional[TreeNode]) -> List[List[int]]",
            "自底向上",
            "value",
            ref_level_order_bottom,
            [
                T("经典", [[3, 9, 20, None, None, 15, 7]], True),
                T("root=[1,2,3]", [[1, 2, 3]]),
                T("root=[]", [[]]),
            ],
        ),
        P(
            "zigzag",
            "锯齿形层序遍历",
            "levelview",
            "中等",
            "偶数层左→右，奇数层右→左。",
            [{"input": "root = [3,9,20,null,null,15,7]", "output": "[[3],[20,9],[15,7]]"}],
            "zigzagLevelOrder",
            "(root: Optional[TreeNode]) -> List[List[int]]",
            "锯齿层序",
            "value",
            ref_zigzag,
            [
                T("经典", [[3, 9, 20, None, None, 15, 7]], True),
                T("root=[1]", [[1]], True),
                T("root=[1,2,3,4,5,6,7]", [[1, 2, 3, 4, 5, 6, 7]]),
            ],
        ),
        P(
            "right-side-view",
            "二叉树的右视图",
            "levelview",
            "中等",
            "返回从右侧可见的节点值（自上而下）。",
            [{"input": "root = [1,2,3,null,5,null,4]", "output": "[1,3,4]"}],
            "rightSideView",
            "(root: Optional[TreeNode]) -> List[int]",
            "右视图",
            "value",
            ref_right_side,
            [
                T("样例", [[1, 2, 3, None, 5, None, 4]], True),
                T("root=[1,null,3]", [[1, None, 3]], True),
                T("root=[]", [[]]),
            ],
        ),
        P(
            "left-side-view",
            "二叉树的左视图",
            "levelview",
            "中等",
            "返回从左侧可见的节点值。",
            [{"input": "root = [1,2,3,null,5,null,4]", "output": "[1,2,5]"}],
            "leftSideView",
            "(root: Optional[TreeNode]) -> List[int]",
            "左视图",
            "value",
            ref_left_side,
            [
                T("样例", [[1, 2, 3, None, 5, None, 4]], True),
                T("root=[1,2,3]", [[1, 2, 3]]),
                T("root=[1]", [[1]]),
            ],
        ),
        P(
            "average-of-levels",
            "层平均值",
            "levelview",
            "简单",
            "返回每一层节点值的平均值（浮点）。",
            [{"input": "root = [3,9,20,null,null,15,7]", "output": "[3.0,14.5,11.0]"}],
            "averageOfLevels",
            "(root: Optional[TreeNode]) -> List[float]",
            "层均值",
            "value",
            ref_avg_levels,
            [
                T("经典", [[3, 9, 20, None, None, 15, 7]], True),
                T("root=[3,9,20,15,7]", [[3, 9, 20, 15, 7]], True),
                T("root=[1]", [[1]]),
            ],
        ),
        P(
            "find-bottom-left",
            "找树左下角的值",
            "levelview",
            "中等",
            "返回最后一行最左边的值。",
            [{"input": "root = [2,1,3]", "output": "1"}],
            "findBottomLeftValue",
            "(root: Optional[TreeNode]) -> int",
            "左下角",
            "value",
            ref_find_bottom_left,
            [
                T("root=[2,1,3]", [[2, 1, 3]], True),
                T("root=[1,2,3,4,null,5,6,null,null,7]", [[1, 2, 3, 4, None, 5, 6, None, None, 7]], True),
                T("root=[1]", [[1]]),
            ],
        ),
        P(
            "largest-values",
            "每层最大值",
            "levelview",
            "中等",
            "返回每一层的最大值列表。",
            [{"input": "root = [1,3,2,5,3,null,9]", "output": "[1,3,9]"}],
            "largestValues",
            "(root: Optional[TreeNode]) -> List[int]",
            "层最大值",
            "value",
            ref_largest_values,
            [
                T("样例", [[1, 3, 2, 5, 3, None, 9]], True),
                T("root=[1,2,3]", [[1, 2, 3]]),
                T("root=[1]", [[1]]),
            ],
        ),
        P(
            "max-level-sum",
            "最大层和的级别",
            "levelview",
            "中等",
            "返回层和最大的最小层号（根为第 1 层）。",
            [{"input": "root = [1,7,0,7,-8,null,null]", "output": "2"}],
            "maxLevelSum",
            "(root: Optional[TreeNode]) -> int",
            "最大层和层号",
            "value",
            ref_max_level_sum,
            [
                T("样例", [[1, 7, 0, 7, -8, None, None]], True),
                T("root=[989,null,10250,98693,-89388,null,null,null,-32127]", [[989, None, 10250, 98693, -89388, None, None, None, -32127]]),
                T("root=[1]", [[1]]),
            ],
        ),
        P(
            "width-of-tree",
            "二叉树最大宽度",
            "levelview",
            "中等",
            "各层两端非空节点间的宽度最大值（按满二叉树编号）。",
            [{"input": "root = [1,3,2,5,3,null,9]", "output": "4"}],
            "widthOfBinaryTree",
            "(root: Optional[TreeNode]) -> int",
            "最大宽度",
            "value",
            ref_width_of_binary_tree,
            [
                T("样例", [[1, 3, 2, 5, 3, None, 9]], True),
                T("root=[1,3,2,5,null,null,9,6,null,7]", [[1, 3, 2, 5, None, None, 9, 6, None, 7]]),
                T("root=[1]", [[1]]),
            ],
        ),
        P(
            "vertical-order",
            "垂直遍历",
            "levelview",
            "中等",
            "按列号从左到右、列内从上到下返回垂直遍历。",
            [{"input": "root = [3,9,20,null,null,15,7]", "output": "[[9],[3,15],[20],[7]]"}],
            "verticalOrder",
            "(root: Optional[TreeNode]) -> List[List[int]]",
            "垂直顺序",
            "value",
            ref_vertical_order,
            [
                T("经典", [[3, 9, 20, None, None, 15, 7]], True),
                T("root=[1,2,3,4,5,6,7]", [[1, 2, 3, 4, 5, 6, 7]]),
                T("root=[1]", [[1]]),
            ],
        ),
        P(
            "deepest-leaves-sum",
            "最深叶子之和",
            "levelview",
            "中等",
            "返回最深层叶子节点值之和。",
            [{"input": "root = [1,2,3,4,5,null,6,7,null,null,null,null,8]", "output": "15"}],
            "deepestLeavesSum",
            "(root: Optional[TreeNode]) -> int",
            "最深叶之和",
            "value",
            ref_deepest_leaves_sum,
            [
                T("样例", [[1, 2, 3, 4, 5, None, 6, 7, None, None, None, None, 8]], True),
                T("root=[6,7,8,2,7,1,3,9,null,1,4,null,null,null,5]", [[6, 7, 8, 2, 7, 1, 3, 9, None, 1, 4, None, None, None, 5]]),
                T("root=[1]", [[1]]),
            ],
        ),
    ]

    # ========== 8. advanced (12) ==========
    C += [
        P(
            "max-path-sum",
            "二叉树中的最大路径和",
            "advanced",
            "困难",
            "任意节点到任意节点的路径（至少一节点）的最大权和。",
            [{"input": "root = [1,2,3]", "output": "6"}],
            "maxPathSum",
            "(root: Optional[TreeNode]) -> int",
            "最大路径和",
            "value",
            ref_max_path_sum,
            [
                T("root=[1,2,3]", [[1, 2, 3]], True),
                T("root=[-10,9,20,null,null,15,7]", [[-10, 9, 20, None, None, 15, 7]], True),
                T("root=[-3]", [[-3]], hint="全负时取最大单节点"),
                T("root=[2,-1]", [[2, -1]]),
            ],
        ),
        P(
            "house-robber-iii",
            "打家劫舍 III",
            "advanced",
            "中等",
            "树形打家劫舍：相邻不能同时偷，返回最大金额。",
            [{"input": "root = [3,2,3,null,3,null,1]", "output": "7"}],
            "rob",
            "(root: Optional[TreeNode]) -> int",
            "树形 DP",
            "value",
            ref_house_robber_iii,
            [
                T("样例1", [[3, 2, 3, None, 3, None, 1]], True),
                T("样例2", [[3, 4, 5, 1, 3, None, 1]], True),
                T("root=[1]", [[1]]),
            ],
        ),
        P(
            "distribute-coins",
            "在二叉树中分配硬币",
            "advanced",
            "中等",
            "每个节点最终恰好 1 枚硬币，返回最少移动次数。",
            [{"input": "root = [3,0,0]", "output": "2"}],
            "distributeCoins",
            "(root: Optional[TreeNode]) -> int",
            "分配硬币",
            "value",
            ref_distribute_coins,
            [
                T("root=[3,0,0]", [[3, 0, 0]], True),
                T("root=[0,3,0]", [[0, 3, 0]], True),
                T("root=[1,0,2]", [[1, 0, 2]]),
            ],
        ),
        P(
            "find-tilt",
            "二叉树的坡度",
            "advanced",
            "简单",
            "坡度=|左子树和-右子树和|，返回整棵树坡度之和。",
            [{"input": "root = [1,2,3]", "output": "1"}],
            "findTilt",
            "(root: Optional[TreeNode]) -> int",
            "坡度和",
            "value",
            ref_tilt,
            [
                T("root=[1,2,3]", [[1, 2, 3]], True),
                T("root=[4,2,9,3,5,null,7]", [[4, 2, 9, 3, 5, None, 7]], True),
                T("root=[21,7,14,1,1,2,2,3,3]", [[21, 7, 14, 1, 1, 2, 2, 3, 3]]),
            ],
        ),
        P(
            "is-subtree",
            "另一棵树的子树",
            "advanced",
            "简单",
            "判断 `subRoot` 是否为 `root` 的子树。",
            [{"input": "root = [3,4,5,1,2], subRoot = [4,1,2]", "output": "true"}],
            "isSubtree",
            "(root: Optional[TreeNode], subRoot: Optional[TreeNode]) -> bool",
            "子树判定",
            "trees",
            ref_is_subtree,
            [
                T("true 样例", [[3, 4, 5, 1, 2], [4, 1, 2]], True),
                T("false 样例", [[3, 4, 5, 1, 2, None, None, None, None, 0], [4, 1, 2]], True),
                T("单节点", [[1], [1]]),
            ],
        ),
        P(
            "flip-equiv",
            "翻转等价二叉树",
            "advanced",
            "中等",
            "通过若干次左右翻转能否使两树等价。",
            [{"input": "root1 = [1,2,3,4,5,6,null,null,null,7,8], root2 = [1,3,2,null,6,4,5,null,null,null,null,8,7]", "output": "true"}],
            "flipEquiv",
            "(root1: Optional[TreeNode], root2: Optional[TreeNode]) -> bool",
            "翻转等价",
            "trees",
            ref_flip_equiv,
            [
                T("样例 true", [[1, 2, 3, 4, 5, 6, None, None, None, 7, 8], [1, 3, 2, None, 6, 4, 5, None, None, None, None, 8, 7]], True),
                T("都空", [[], []]),
                T("root1=[1,2], root2=[1,null,2]", [[1, 2], [1, None, 2]]),
            ],
        ),
        P(
            "leaf-similar",
            "叶子相似的树",
            "advanced",
            "简单",
            "若两树叶值序列相同则相似。",
            [{"input": "root1 = [3,5,1,6,2,9,8,null,null,7,4], root2 = [3,5,1,6,7,4,2,null,null,null,null,null,null,9,8]", "output": "true"}],
            "leafSimilar",
            "(root1: Optional[TreeNode], root2: Optional[TreeNode]) -> bool",
            "叶序列相同",
            "trees",
            ref_leaf_similar,
            [
                T("相似", [[3, 5, 1, 6, 2, 9, 8, None, None, 7, 4], [3, 5, 1, 6, 7, 4, 2, None, None, None, None, None, None, 9, 8]], True),
                T("不相似", [[1, 2, 3], [1, 3, 2]], True),
                T("单叶", [[1], [1]]),
            ],
        ),
        P(
            "evaluate-boolean-tree",
            "计算布尔二叉树",
            "advanced",
            "简单",
            "叶为 0/1；非叶 2=OR、3=AND。求根表达式值。",
            [{"input": "root = [2,1,3,null,null,0,1]", "output": "true"}],
            "evaluateTree",
            "(root: Optional[TreeNode]) -> bool",
            "布尔树求值",
            "value",
            ref_evaluate_boolean,
            [
                T("OR 样例", [[2, 1, 3, None, None, 0, 1]], True),
                T("root=[0]", [[0]], True),
                T("AND", [[3, 1, 1]],),
            ],
        ),
        P(
            "longest-zigzag",
            "二叉树中的最长交错路径",
            "advanced",
            "中等",
            "交错路径边数最大值。",
            [{"input": "root = [1,null,1,1,1,null,null,1,1,null,1,null,null,null,1]", "output": "3"}],
            "longestZigZag",
            "(root: Optional[TreeNode]) -> int",
            "最长交错",
            "value",
            ref_longest_zigzag,
            [
                T("样例", [[1, None, 1, 1, 1, None, None, 1, 1, None, 1, None, None, None, 1]], True),
                T("root=[1,1,1,null,1,null,null,1,1,null,1]", [[1, 1, 1, None, 1, None, None, 1, 1, None, 1]]),
                T("root=[1]", [[1]]),
            ],
        ),
        P(
            "max-product-split",
            "分裂二叉树的最大乘积",
            "advanced",
            "中等",
            "删除一条边分成两棵非空树，返回两树节点和乘积的最大值（对 1e9+7 取模）。",
            [{"input": "root = [1,2,3,4,5,6]", "output": "110"}],
            "maxProduct",
            "(root: Optional[TreeNode]) -> int",
            "最大乘积",
            "value",
            ref_max_product_split,
            [
                T("样例", [[1, 2, 3, 4, 5, 6]], True),
                T("root=[1,null,2,3,4,null,null,5,6]", [[1, None, 2, 3, 4, None, None, 5, 6]]),
                T("root=[2,3,9,10,7,8,6,5,4,11,1]", [[2, 3, 9, 10, 7, 8, 6, 5, 4, 11, 1]]),
            ],
        ),
        P(
            "count-pairs-distance",
            "距离小于等于 distance 的叶对数量",
            "advanced",
            "中等",
            "统计叶对距离 ≤ `distance` 的数量。",
            [{"input": "root = [1,2,3,null,4], distance = 3", "output": "1"}],
            "countPairs",
            "(root: Optional[TreeNode], distance: int) -> int",
            "叶对计数",
            "value",
            ref_count_pairs_distance,
            [
                T("样例", [[1, 2, 3, None, 4], 3], True),
                T("root=[1,2,3,4,5,6,7], distance=3", [[1, 2, 3, 4, 5, 6, 7], 3], True),
                T("root=[7,1,4,6,null,5,3,null,null,null,null,null,2], distance=3", [[7, 1, 4, 6, None, 5, 3, None, None, None, None, None, 2], 3]),
            ],
        ),
        P(
            "reverse-odd-levels",
            "反转奇偶层节点值",
            "advanced",
            "中等",
            "反转每个奇数层的节点值（完美二叉树），返回根。",
            [{"input": "root = [2,3,5,8,13,21,34]", "output": "[2,5,3,8,13,21,34]"}],
            "reverseOddLevels",
            "(root: Optional[TreeNode]) -> Optional[TreeNode]",
            "反转奇数层",
            "tree_return",
            ref_reverse_odd_levels,
            [
                T("样例", [[2, 3, 5, 8, 13, 21, 34]], True),
                T("root=[7,13,11]", [[7, 13, 11]], True),
                T("root=[0,1,2,0,0,0,0,1,1,1,1,2,2,2,2]", [[0, 1, 2, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2]]),
            ],
        ),
    ]

    return C


def materialize(prob: ProblemDef) -> dict:
    tests = []
    for t in prob["tests_raw"]:
        exp = compute_expected(prob["judgeMode"], prob["ref"], t["args"])
        # normalize floats for JSON
        if isinstance(exp, float):
            exp = float(exp)
        entry = {
            "inputLabel": t["inputLabel"],
            "args": t["args"],
            "expected": exp,
        }
        if t.get("sample"):
            entry["sample"] = True
        if t.get("hint"):
            entry["hint"] = t["hint"]
        tests.append(entry)

    # refresh example outputs from first sample when possible
    examples = prob["examples"]
    out = {
        "id": prob["id"],
        "title": prob["title"],
        "topic": prob["topic"],
        "difficulty": prob["difficulty"],
        "statement": prob["statement"],
        "examples": examples,
        "constraints": prob["constraints"],
        "functionName": prob["functionName"],
        "starterCode": prob["starterCode"],
        "judgeMode": prob["judgeMode"],
        "cAbi": prob.get("cAbi")
        or (
            {"params": [], "returnKind": "serialize"}
            if prob["judgeMode"] == "serialize"
            else {"params": [{"name": "root", "kind": "tree"}], "returnKind": "int"}
        ),
        "tests": tests,
    }
    if prob.get("harnessExtras"):
        out["harnessExtras"] = prob["harnessExtras"]
    return out


TOPICS = [
    ("traversal", "遍历与序列", "前序 / 中序 / 后序与序列巩固"),
    ("basics", "二叉树基础属性", "深度、对称、翻转、合并等"),
    ("path", "路径与递归", "路径和、好节点、祖先差等"),
    ("bst", "二叉搜索树 BST", "验证、搜索、插入删除、第 K 等"),
    ("construct", "构造与序列化", "由遍历还原、编解码、展开"),
    ("lca", "最近公共祖先与祖先关系", "LCA、距离、方向、堂兄弟"),
    ("levelview", "层序与视图", "层序、锯齿、左右视图、垂直"),
    ("advanced", "进阶 / 综合", "最大路径和、树 DP、翻转等价等"),
]


def emit_ts_module(topic_id: str, problems: list[dict]) -> str:
    lines = ["import type { Problem } from '../../types'", "", f"export const PROBLEMS_{topic_id.upper()}: Problem[] = ["]
    for p in problems:
        lines.append("  {")
        for key in [
            "id",
            "title",
            "topic",
            "difficulty",
            "statement",
            "examples",
            "constraints",
            "functionName",
            "starterCode",
            "judgeMode",
            "cAbi",
            "harnessExtras",
            "tests",
        ]:
            if key not in p:
                continue
            if key in ("starterCode", "harnessExtras", "statement"):
                lines.append(f"    {key}: {json.dumps(p[key], ensure_ascii=False)},")
            else:
                lines.append(f"    {key}: {json.dumps(p[key], ensure_ascii=False)},")
        lines.append("  },")
    lines.append("]")
    lines.append("")
    return "\n".join(lines)


def main():
    catalog = extend_catalog(build_catalog())
    # dedupe by id
    seen = set()
    unique = []
    for p in catalog:
        if p["id"] in seen:
            raise SystemExit(f"duplicate id {p['id']}")
        seen.add(p["id"])
        unique.append(p)

    materialized = [materialize(p) for p in unique]
    by_topic: dict[str, list] = {t[0]: [] for t in TOPICS}
    for p in materialized:
        by_topic[p["topic"]].append(p)

    total = sum(len(v) for v in by_topic.values())
    print("counts:")
    for tid, name, _ in TOPICS:
        print(f"  {tid} ({name}): {len(by_topic[tid])}")
    print("total", total)
    if total != 100:
        raise SystemExit(f"expected 100 problems, got {total}")

    cat_dir = OUT / "categories"
    cat_dir.mkdir(parents=True, exist_ok=True)
    imports = []
    names = []
    for tid, _, _ in TOPICS:
        fname = f"{tid}.ts"
        (cat_dir / fname).write_text(emit_ts_module(tid, by_topic[tid]), encoding="utf-8")
        imp = f"PROBLEMS_{tid.upper()}"
        imports.append(f"import {{ {imp} }} from './categories/{tid}'")
        names.append(imp)

    index = []
    index.append("import type { Problem, Topic } from '../types'")
    index.extend(imports)
    index.append("")
    index.append("export const TOPICS: Topic[] = [")
    for tid, name, blurb in TOPICS:
        index.append(
            f"  {{ id: '{tid}', name: {json.dumps(name, ensure_ascii=False)}, blurb: {json.dumps(blurb, ensure_ascii=False)} }},"
        )
    index.append("]")
    index.append("")
    index.append("export const PROBLEMS: Problem[] = [")
    for n in names:
        index.append(f"  ...{n},")
    index.append("]")
    index.append("")
    index.append("export function getProblem(id: string): Problem | undefined {")
    index.append("  return PROBLEMS.find((p) => p.id === id)")
    index.append("}")
    index.append("")
    index.append("export function problemsByTopic(topic: Topic['id']): Problem[] {")
    index.append("  return PROBLEMS.filter((p) => p.topic === topic)")
    index.append("}")
    index.append("")
    index.append("export function topicCounts(): Record<string, number> {")
    index.append("  const counts: Record<string, number> = {}")
    index.append("  for (const t of TOPICS) counts[t.id] = 0")
    index.append("  for (const p of PROBLEMS) counts[p.topic] = (counts[p.topic] ?? 0) + 1")
    index.append("  return counts")
    index.append("}")
    index.append("")

    (OUT / "problems.ts").write_text("\n".join(index), encoding="utf-8")
    print("wrote", OUT / "problems.ts", "and", cat_dir)


if __name__ == "__main__":
    main()
