# CS2 Model Compiler / CS2 模型编译器

[English](#english) | [中文](#中文)

---

## English

### Overview
Automated GitHub Actions workflow for compiling CS2 (Counter-Strike 2) model files using Source 2 Resource Compiler.

### Features
- ✅ Self-hosted GitHub Actions runner on Windows
- ✅ Automatic environment setup with `uv` (Python package manager)
- ✅ Compiles `.vmdl` model files to `.vmdl_c` compiled format
- ✅ Generates `BuildStats.md` with compilation results
- ✅ Auto-updates `BuildStats.md` to GitHub repository
- ✅ Toolchain version tracking from `steam.inf`

### How to Use

#### Trigger Compilation
1. Go to [Actions](https://github.com/UpKK-Xnet-YYDCS/cs2-model-compiler/actions) tab
2. Select "Compile Models" workflow
3. Click "Run workflow" → Choose `master` branch → Run

#### View Results
- **BuildStats.md** - Automatically updated in repository root after each run
- **Compiled Models** - Available as GitHub Actions artifact (7-day retention)

### Workflow Steps
1. Checkout repository
2. Setup Python environment via `uv`
3. Install dependencies from `requirements.txt`
4. Run `compile_models.py` to compile all models
5. Generate `BuildStats.md` with:
   - Toolchain version (from `steam.inf`)
   - CS2 game version
   - Model compilation status table (✅ Success / ❌ Failed / ⏭️ Skipped)
   - Failure reasons for failed models
6. Auto-commit `BuildStats.md` to repository

### BuildStats.md Example
```markdown
# Build Stats
**Generated:** 2026-05-03 20:46:57
**Toolchain Version:** Client 2000809, Patch 1.41.5.8 (Apr 30 2026 15:09:15)

## Summary
- **Success:** 10
- **Failed:** 0
- **Skipped:** 0
- **Total:** 10

## Model Compilation Results
| Directory | File | Status | Failure Reason |
|-----------|------|--------|----------------|
| upkk/curren_chan | curren_chan.vmdl | OK | - |
```

### Requirements
- Windows machine with CS2 installed
- GitHub Actions self-hosted runner configured
- Python 3.10+ (auto-installed by `uv`)

---

## 中文

### 概述
使用 Source 2 资源编译器自动编译 CS2（反恐精英 2）模型文件的 GitHub Actions 工作流。

### 功能特性
- ✅ Windows 自托管 GitHub Actions Runner
- ✅ 使用 `uv`（Python 包管理器）自动配置环境
- ✅ 将 `.vmdl` 模型文件编译为 `.vmdl_c` 编译格式
- ✅ 生成包含编译结果的 `BuildStats.md`
- ✅ 自动更新 `BuildStats.md` 到 GitHub 仓库
- ✅ 从 `steam.inf` 追踪工具链版本

### 使用方法

#### 触发编译
1. 访问 [Actions](https://github.com/UpKK-Xnet-YYDCS/cs2-model-compiler/actions) 页面
2. 选择 "Compile Models" 工作流
3. 点击 "Run workflow" → 选择 `master` 分支 → 运行

#### 查看结果
- **BuildStats.md** - 每次运行后自动更新到仓库根目录
- **编译模型** - 作为 GitHub Actions artifact 提供（保留 7 天）

### 工作流步骤
1. 检出仓库代码
2. 通过 `uv` 设置 Python 环境
3. 从 `requirements.txt` 安装依赖
4. 运行 `compile_models.py` 编译所有模型
5. 生成 `BuildStats.md`，包含：
   - 工具链版本（来自 `steam.inf`）
   - CS2 游戏版本
   - 模型编译状态表格（✅ 成功 / ❌ 失败 / ⏭️ 跳过）
   - 失败模型的错误原因
6. 自动提交 `BuildStats.md` 到仓库

### BuildStats.md 示例
```markdown
# Build Stats
**生成时间：** 2026-05-03 20:46:57
**工具链版本：** Client 2000809, Patch 1.41.5.8 (2026年4月30日 15:09:15)

## 摘要
- **成功：** 10
- **失败：** 0
- **跳过：** 0
- **总计：** 10

## 模型编译结果
| 目录 | 文件 | 状态 | 失败原因 |
|------|------|------|----------|
| upkk/curren_chan | curren_chan.vmdl | OK | - |
```

### 系统要求
- 已安装 CS2 的 Windows 机器
- 已配置 GitHub Actions 自托管 Runner
- Python 3.10+（`uv` 会自动安装）

### 本地开发
```powershell
# 克隆仓库
git clone https://github.com/UpKK-Xnet-YYDCS/cs2-model-compiler.git

# 安装 uv
Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression

# 运行编译脚本
cd F:\CS2-ModelBuilder
uv run python compile_models.py
```

---

### License
MIT License
