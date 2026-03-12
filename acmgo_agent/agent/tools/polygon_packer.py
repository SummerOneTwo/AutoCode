"""
Polygon format packing tool.
"""
import os
import shutil
import sys
from typing import Dict, Any
from .base import Tool


class PackPolygonTool(Tool):
    """Tool for packing development files into Polygon format."""

    def __init__(self, work_dir: str):
        super().__init__(
            name="pack_polygon_to_format",
            description=(
                "将开发阶段文件打包成 Polygon 标准格式。"
                "创建 files/, solutions/, statements/, scripts/ 目录结构并移动相应文件。"
                "清理根目录下的开发阶段文件。"
            ),
            parameters={},
        )
        self.work_dir = os.path.abspath(work_dir)

    def execute(self) -> Dict[str, Any]:
        """Pack development files into Polygon format."""
        # Check work directory
        if not os.path.exists(self.work_dir):
            return {
                "success": False,
                "error": f"工作目录不存在: {self.work_dir}",
            }

        results = {
            "files_copied": [],
            "files_removed": [],
            "directories_created": [],
        }

        # 1. Create directories
        directories = ["files", "solutions", "statements", "scripts"]
        for dir_name in directories:
            dir_path = os.path.join(self.work_dir, dir_name)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                results["directories_created"].append(dir_name)

        # 2. Copy files to files/ directory
        files_dir = os.path.join(self.work_dir, "files")
        for src in ["testlib.h", "gen.cpp", "val.cpp"]:
            src_path = os.path.join(self.work_dir, src)
            if os.path.exists(src_path):
                dst_path = os.path.join(files_dir, src)
                shutil.copy2(src_path, dst_path)
                results["files_copied"].append(f"{src} -> files/{src}")

        # 3. Copy files to solutions/ directory
        solutions_dir = os.path.join(self.work_dir, "solutions")
        for src in ["sol.cpp", "brute.cpp"]:
            src_path = os.path.join(self.work_dir, src)
            if os.path.exists(src_path):
                dst_path = os.path.join(solutions_dir, src)
                shutil.copy2(src_path, dst_path)
                results["files_copied"].append(f"{src} -> solutions/{src}")

        # 4. Copy README.md to statements/ directory
        statements_dir = os.path.join(self.work_dir, "statements")
        readme_src = os.path.join(self.work_dir, "README.md")
        if os.path.exists(readme_src):
            readme_dst = os.path.join(statements_dir, "README.md")
            shutil.copy2(readme_src, readme_dst)
            results["files_copied"].append("README.md -> statements/README.md")

        # 5. Copy stress.py to scripts/ directory
        scripts_dir = os.path.join(self.work_dir, "scripts")
        stress_src = os.path.join(self.work_dir, "stress.py")
        if os.path.exists(stress_src):
            stress_dst = os.path.join(scripts_dir, "stress.py")
            shutil.copy2(stress_src, stress_dst)
            results["files_copied"].append("stress.py -> scripts/stress.py")

        # 6. Remove development files from root
        dev_files = [
            "testlib.h", "gen.cpp", "val.cpp", "sol.cpp", "brute.cpp",
            "gen.exe", "val.exe", "sol.exe", "brute.exe",
            "input.txt", "sol.out", "brute.out",
            "README.md", "stress.py",
        ]

        exe_ext = ".exe" if sys.platform == "win32" else ""

        # Add any existing executables
        for name in ["gen", "val", "sol", "brute"]:
            exe_name = f"{name}{exe_ext}"
            if exe_name not in dev_files:
                dev_files.append(exe_name)

        for f in dev_files:
            file_path = os.path.join(self.work_dir, f)
            if os.path.exists(file_path):
                os.remove(file_path)
                results["files_removed"].append(f)

        # 7. Check if problem.xml exists, if not create a template
        problem_xml = os.path.join(self.work_dir, "problem.xml")
        if not os.path.exists(problem_xml):
            # Create a basic problem.xml template
            problem_name = os.path.basename(self.work_dir)
            template = self._generate_problem_xml_template(problem_name)
            with open(problem_xml, "w", encoding="utf-8") as f:
                f.write(template)
            results["files_copied"].append("problem.xml (created)")

        return {
            "success": True,
            "message": "Polygon 格式整理完成",
            "results": results,
        }

    def _generate_problem_xml_template(self, problem_name: str) -> str:
        """Generate a basic problem.xml template."""
        return f"""<?xml version="1.0" encoding="utf-8" standalone="no"?>
<problem revision="1" short-name="{problem_name}" url="https://polygon.codeforces.com/p/user/{problem_name}">
    <names>
        <name language="chinese" value="{problem_name}"/>
    </names>
    <statements>
        <statement charset="UTF-8" language="chinese" mathjax="true" path="statements/README.md" type="application/x-tex"/>
    </statements>
    <judging cpu-name="Intel(R) Core(TM) i3-8100 CPU @ 3.60GHz" cpu-speed="3600" os="Windows">
        <testset name="tests">
            <time-limit>1000</time-limit>
            <memory-limit>268435456</memory-limit>
            <test-count>20</test-count>
            <input-path-pattern>tests/%02d.in</input-path-pattern>
            <answer-path-pattern>tests/%02d.ans</answer-path-pattern>
            <tests/>
        </testset>
    </judging>
    <files>
        <resources>
            <file path="files/testlib.h"/>
        </resources>
        <executables>
            <executable>
                <source path="files/gen.cpp"/>
            </executable>
            <executable>
                <source path="files/val.cpp"/>
            </executable>
        </executables>
    </files>
    <assets>
        <solutions>
            <solution tag="main">
                <source path="solutions/sol.cpp"/>
            </solution>
            <solution tag="rejected">
                <source path="solutions/brute.cpp"/>
            </solution>
        </solutions>
    </assets>
</problem>
"""


class SetupDevTool(Tool):
    """Tool for setting up development environment from Polygon format."""

    def __init__(self, work_dir: str):
        super().__init__(
            name="setup_dev",
            description=(
                "从 Polygon 格式设置开发环境。"
                "将 files/, solutions/, statements/ 目录下的文件复制到根目录。"
                "用于继续修改已打包的问题。"
            ),
            parameters={},
        )
        self.work_dir = os.path.abspath(work_dir)

    def execute(self) -> Dict[str, Any]:
        """Set up development environment from Polygon format."""
        # Check work directory
        if not os.path.exists(self.work_dir):
            return {
                "success": False,
                "error": f"工作目录不存在: {self.work_dir}",
            }

        results = {
            "files_copied": [],
            "files_removed": [],
        }

        # 1. Copy files from files/ to root
        files_dir = os.path.join(self.work_dir, "files")
        if os.path.exists(files_dir):
            for src in ["testlib.h", "gen.cpp", "val.cpp"]:
                src_path = os.path.join(files_dir, src)
                if os.path.exists(src_path):
                    dst_path = os.path.join(self.work_dir, src)
                    shutil.copy2(src_path, dst_path)
                    results["files_copied"].append(f"files/{src} -> {src}")

        # 2. Copy files from solutions/ to root
        solutions_dir = os.path.join(self.work_dir, "solutions")
        if os.path.exists(solutions_dir):
            for src in ["sol.cpp", "brute.cpp"]:
                src_path = os.path.join(solutions_dir, src)
                if os.path.exists(src_path):
                    dst_path = os.path.join(self.work_dir, src)
                    shutil.copy2(src_path, dst_path)
                    results["files_copied"].append(f"solutions/{src} -> {src}")

        # 3. Copy README.md from statements/ to root
        statements_dir = os.path.join(self.work_dir, "statements")
        if os.path.exists(statements_dir):
            readme_src = os.path.join(statements_dir, "README.md")
            if os.path.exists(readme_src):
                readme_dst = os.path.join(self.work_dir, "README.md")
                shutil.copy2(readme_src, readme_dst)
                results["files_copied"].append("statements/README.md -> README.md")

        # 4. Copy stress.py from scripts/ to root (if exists)
        scripts_dir = os.path.join(self.work_dir, "scripts")
        if os.path.exists(scripts_dir):
            stress_src = os.path.join(scripts_dir, "stress.py")
            if os.path.exists(stress_src):
                stress_dst = os.path.join(self.work_dir, "stress.py")
                shutil.copy2(stress_src, stress_dst)
                results["files_copied"].append("scripts/stress.py -> stress.py")

        return {
            "success": True,
            "message": "开发环境设置完成",
            "results": results,
        }
