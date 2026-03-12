"""
Few-shot examples for the ACMGO Problem Setter Agent.

These examples demonstrate how to handle various situations during problem setting.
"""

# Example problem statements for different types
EXAMPLE_STATEMENTS = {
    "dynamic_programming": """# 示例题目：最大子段和

## 题目描述

给定一个长度为 N 的整数序列 A_1, A_2, ..., A_N。
求一个连续子段，使其和最大。输出这个最大的和。

## 输入格式

第一行一个整数 T，表示测试用例数量。
对于每个测试用例：
- 第一行一个整数 N (1 <= N <= 2 * 10^5)
- 第二行 N 个整数 A_1, A_2, ..., A_N (-10^9 <= A_i <= 10^9)

## 输出格式

对于每个测试用例，输出一个整数，表示最大子段和。

## 样例

输入：
```
2
5
-2 1 -3 4 -1 4 2 -5
3
1 2 3
```

输出：
```
7
6
```

## 约束条件

- 时间限制：1 秒
- 内存限制：256 MB
- 1 <= T <= 100
- 1 <= N <= 2 * 10^5
- -10^9 <= A_i <= 10^9
""",

    "graph": """# 示例题目：树的直径

## 题目描述

给定一棵 N 个节点的树，求这棵树的最长路径的长度。
树的最长路径称为树的直径。

## 输入格式

第一行一个整数 N (2 <= N <= 2 * 10^5)。
接下来 N - 1 行，每行两个整数 u, v (1 <= u, v <= N)，表示一条边。

## 输出格式

输出一个整数，表示树的直径（最长路径上的边数）。

## 样例

输入：
```
5
1 2
2 3
2 4
4 5
```

输出：
```
3
```

## 约束条件

- 时间限制：1 秒
- 内存限制：256 MB
- 2 <= N <= 2 * 10^5
- 树保证连通
""",
}

# Example solution implementations
EXAMPLE_SOLUTIONS = {
    "sol_template": """#include <bits/stdc++.h>
using namespace std;

void solve() {
    // TODO: 实现标准解法
    // 这里是最优解法（例如 O(N log N) 或 O(N)）
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    solve();

    return 0;
}""",

    "brute_template": """#include <bits/stdc++.h>
using namespace std;

void solve() {
    // TODO: 实现暴力解法
    // 这里是最简单、绝对正确的解法（例如 O(N^2) 或 O(N^3)）
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    solve();

    return 0;
}""",
}

# Example validator
EXAMPLE_VALIDATOR = """#include "testlib.h"
using namespace std;

int main(int argc, char* argv[]) {
    registerValidation(argc, argv);

    int n = inf.readInt(1, 200000, "n");
    inf.readEoln();

    for (int i = 0; i < n; i++) {
        inf.readInt(-1000000000, 1000000000, "a_i");
        if (i < n - 1) inf.readSpace();
    }
    inf.readEoln();

    inf.readEof();

    return 0;
}"""

# Example generator
EXAMPLE_GENERATOR = """#include "testlib.h"
using namespace std;

int main(int argc, char* argv[]) {
    registerGen(argc, argv, 1);

    int seed = opt<int>(1);
    int type = opt<int>(2);
    int n_min = opt<int>(3);
    int n_max = opt<int>(4);
    int t_min = opt<int>(5);
    int t_max = opt<int>(6);

    rnd.setSeed(seed);

    int n = rnd.next(n_min, n_max);
    int t = rnd.next(t_min, t_max);

    cout << n << endl;

    // 根据 type 生成不同类型的数据
    switch (type) {
        case 1: // Tiny data
            n = min(n, 10);
            break;
        case 2: // Random data
            // 随机数据
            break;
        case 3: // Max data
            n = n_max;
            break;
        case 4: // Corner cases
            // 边界情况
            break;
        case 5: // Anti-hack
            // 反hack 数据
            break;
    }

    // 生成数据
    for (int i = 0; i < n; i++) {
        int value = rnd.next(-1000000000, 1000000000);
        cout << value;
        if (i < n - 1) cout << " ";
    }
    cout << endl;

    return 0;
}"""


def get_example_statement(problem_type: str) -> str:
    """Get an example problem statement."""
    return EXAMPLE_STATEMENTS.get(problem_type, "")


def get_example_solution(template_name: str) -> str:
    """Get an example solution template."""
    return EXAMPLE_SOLUTIONS.get(template_name, "")


def get_all_example_types() -> list[str]:
    """Get all available example types."""
    return list(EXAMPLE_STATEMENTS.keys())
