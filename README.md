# CS2 Model Compiler / CS2 模型编译器

[English](#english) | [中文](#中文)

# 此项目用于UPKK CS2 PlayerModel 自动构建 并可查看构建状态


### 使用方法

#### 触发编译
1. 访问 [Actions](https://github.com/UpKK-Xnet-YYDCS/cs2-model-compiler/actions) 页面
2. 选择 "Compile Models" 工作流
3. 点击 "Run workflow" → 选择 `master` 分支 → 运行

#### 查看结果
- **BuildStats.md** - 每次运行后自动更新到仓库根目录
- **编译模型** - 作为 GitHub Actions artifact 提供（保留 7 天）


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
