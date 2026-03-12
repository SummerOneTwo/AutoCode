"""
Stage-specific prompts for the ACMGO Problem Setter Agent.
"""

# Stage 1: Statement Design
STAGE_STATEMENT_PROMPT = """
## 步骤一：题面设计 (Statement)

请设计题面，包括：
1. **题目名称**：简洁且有吸引力的名称
2. **题目描述**：清晰的问题背景和任务描述
3. **输入格式**：
   - 输入数据范围和约束
   - 多组测试用例的格式
4. **输出格式**：每个测试用例的输出格式
5. **样例**：至少 1-2 个样例，展示输入输出
6. **约束条件**：
   - 时间限制（建议 1-2 秒）
   - 内存限制（建议 256MB）
   - 数据范围（N, M, T 等的取值范围）

请将题面以 Markdown 格式保存为 README.md。
完成后使用 save_file("README.md", content) 保存文件。
"""

# Stage 2: Dual Solutions
STAGE_SOLUTIONS_PROMPT = """
## 步骤二：双解法实现 (Dual Solutions)

请实现两份解法：

### 1. 标准解法 (sol.cpp)
- 时间复杂度最优（例如 O(N log N), O(M sqrt(N)) 等）
- 使用 C++2C 标准
- 添加快速 IO（如有大量输入输出）
- 考虑边界情况

### 2. 暴力解法 (brute.cpp)
- 逻辑简单、绝对正确
- 时间复杂度可以较大（例如 O(N^2), O(N^3)）
- 用于验证标程的正确性
- 在小数据上（N <= 100）应该能快速运行

### 代码要求
1. 使用 `#include <bits/stdc++.h>` 和 `using namespace std;`
2. 主函数使用 `void solve()` 模式或直接 `int main()`
3. 处理多组测试用例（如有）
4. 输出格式必须与题面一致

请分别使用 save_file("sol.cpp", content) 和 save_file("brute.cpp", content) 保存文件。
"""

# Stage 3: Validator
STAGE_VALIDATOR_PROMPT = """
## 步骤三：数据校验器 (val.cpp)

请编写基于 testlib.h 的数据校验器。校验器负责：

1. **验证输入格式**：确保输入数据符合题面格式
2. **验证数据范围**：检查数值是否在约束范围内
3. **验证数据合法性**：例如图连通性、树的性质等

### 代码结构
```cpp
#include "testlib.h"
using namespace std;

int main(int argc, char* argv[]) {
    registerValidation(argc, argv);

    // 读取输入并验证
    // 使用 inf.readInt(min, max, "variable_name") 读取整数
    // 使用 inf.readLong(min, max, "variable_name") 读取长整数
    // 使用 inf.readStrictDouble(min, max, "variable_name") 读取浮点数
    // 使用 inf.readToken(regex, "variable_name") 读取匹配正则的字符串

    return 0;
}
```

### testlib 常用函数
- `registerValidation(argc, argv)`: 初始化校验器
- `inf.readInt(l, r, "name")`: 读取范围 [l, r] 的整数
- `inf.readLong(l, r, "name")`: 读取范围 [l, r] 的长整数
- `inf.readDouble(l, r, "name")`: 读取范围 [l, r] 的浮点数
- `inf.readToken(regex, "name")`: 读取匹配正则的字符串
- `inf.readEoln()`: 读取并验证行尾
- `inf.readEof()`: 读取并验证文件末尾

请使用 save_file("val.cpp", content) 保存文件。
"""

# Stage 4: Generator
STAGE_GENERATOR_PROMPT = """
## 步骤四：数据生成器 (gen.cpp)

请编写基于 testlib.h 的数据生成器。生成器需要支持多种数据类型。

### 程序参数
`gen.exe <seed> <type> <n_min> <n_max> <t_min> <t_max>`

- `seed`: 随机种子
- `type`: 数据类型
  - 1 = 小数据 (Tiny, N <= 10)
  - 2 = 随机数据 (Random)
  - 3 = 大数据 (Max, N 接近上限)
  - 4 = 边界数据 (Corner Cases)
  - 5 = 反hack 数据 (Anti-Hack)
- `n_min`, `n_max`: N 的范围
- `t_min`, `t_max`: 测试用例数量 T 的范围

### 代码结构
```cpp
#include "testlib.h"
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

    // 根据 type 生成不同类型的数据
    // 使用 rnd.next(min, max) 生成随机整数
    // 使用 rnd.next(min, max, "tag") 生成带权重的随机数
    // 使用 rnd.perm(size) 生成排列
    // 使用 rnd.shuffle(vector) 随机打乱数组

    return 0;
}
```

### 数据类型实现建议
1. **Tiny**: N <= 10，便于人眼观察
2. **Random**: N 在 [n_min, n_max] 范围内随机
3. **Max**: N = n_max 或接近 n_max
4. **Corner Cases**:
   - 链、菊花树、星形图
   - 数组全相同、单调递增/递减、波浪形
   - 字符串全 'a'、周期串
5. **Anti-Hack**:
   - 针对常见错误的反例
   - 例如：质数、斐波那契数列等特殊序列

请使用 save_file("gen.cpp", content) 保存文件。
"""

# Stage 5: Stress Test
STAGE_STRESS_TEST_PROMPT = """
## 步骤五：自动化对拍 (Stress Test)

运行对拍测试以验证代码正确性：

1. 首先编译所有文件：使用 compile_all()
2. 然后运行测试：使用 run_stress_test(trials=1000, n_max=100, t_max=3)

### 如果测试失败：
1. 查看失败的输入数据：result["input_data"]
2. 比较两个解法的输出：result["sol_output"] vs result["brute_output"]
3. 分析错误原因：
   - 是否是标程逻辑错误？
   - 是否是边界情况未处理？
   - 是否是数据范围溢出？
4. 修改代码（通常需要修改 sol.cpp）：
   - 使用 save_file("sol.cpp", new_content) 保存修改后的代码
   - 使用 compile_cpp("sol.cpp") 重新编译
   - 使用 run_stress_test() 重新测试
5. 最多重试 3 次

### 如果测试成功：
报告 "步骤五完成，对拍测试通过"，然后进入下一步。
"""

# Stage 6: Package
STAGE_PACKAGE_PROMPT = """
## 步骤六：最终打包 (Final Package)

将文件打包成 Polygon 标准格式：

1. 使用 pack_polygon_to_format() 整理文件结构
   - 创建 files/, solutions/, statements/, scripts/ 目录
   - 复制相应文件
   - 清理根目录的开发文件
   - 自动生成 problem.xml 模板

2. 使用 generate_tests(test_count=20) 生成测试数据
   - 生成 20 组测试数据（01.in ~ 20.in）
   - 自动生成对应的答案文件（01.ans ~ 20.ans）

完成后报告 "步骤六完成，打包成功，出题完成"。
"""

# Error recovery prompts
STRESS_TEST_FAILURE_PROMPT = """
## 对拍测试失败

对拍测试在第 {round} 轮失败。

### 失败信息
- 错误：{error}
- 输入数据：
{input_data}
- 标程输出：{sol_output}
- 暴力解法输出：{brute_output}

### 请分析错误并修正：
1. 确定错误原因
2. 修改 sol.cpp
3. 使用 save_file("sol.cpp", new_content) 保存修改
4. 使用 compile_cpp("sol.cpp") 重新编译
5. 使用 run_stress_test() 重新测试

这是第 {retry_count} 次重试（最多 3 次）。
"""


def get_stage_prompt(stage: str, **kwargs) -> str:
    """Get prompt for a specific stage."""
    prompts = {
        "statement": STAGE_STATEMENT_PROMPT,
        "solutions": STAGE_SOLUTIONS_PROMPT,
        "validator": STAGE_VALIDATOR_PROMPT,
        "generator": STAGE_GENERATOR_PROMPT,
        "stress_test": STAGE_STRESS_TEST_PROMPT,
        "package": STAGE_PACKAGE_PROMPT,
    }

    prompt = prompts.get(stage, "")
    if kwargs:
        try:
            prompt = prompt.format(**kwargs)
        except KeyError as e:
            pass

    return prompt


def get_stress_test_failure_prompt(error_info: dict, retry_count: int) -> str:
    """Get prompt for stress test failure."""
    return STRESS_TEST_FAILURE_PROMPT.format(
        round=error_info.get("round", "?"),
        error=error_info.get("error", "未知错误"),
        input_data=error_info.get("input_data", "无"),
        sol_output=error_info.get("sol_output", "无"),
        brute_output=error_info.get("brute_output", "无"),
        retry_count=retry_count,
    )
