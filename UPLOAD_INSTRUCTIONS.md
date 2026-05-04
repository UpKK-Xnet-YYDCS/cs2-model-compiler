# CS2 Workshop 上传指南

## 方法一：通过 Steam 客户端上传（推荐）

### 步骤：
1. 打开 **Steam 客户端**
2. 进入 **库** → **工具**
3. 安装并运行 **Counter-Strike 2 Workshop Tools**
4. 启动 **Counter-Strike 2**
5. 在主菜单选择 **创意工坊**
6. 选择 **上传新物品** 或 **管理我的工坊物品**
7. 选择已复制的目录：`F:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game\csgo_addons\upkkmodelpack2026_agents`
8. 填写物品信息并上传

## 方法二：通过 SteamCMD 上传

### 前提是已经通过 Steam 客户端保存了登录凭据

### 步骤：
1. 打开 PowerShell，进入 SteamCMD 目录：
   ```powershell
   cd F:\SteamCMD
   ```

2. 交互式登录（只做一次）：
   ```powershell
   .\steamcmd.exe
   # 在交互界面输入：
   login e54385991
   # 输入密码和 Steam Guard 验证码
   remember_password
   quit
   ```

3. 使用脚本上传（已配置好）：
   ```powershell
   cd F:\CS2-ModelBuilder
   uv run upload_to_workshop.py
   ```

4. 或者直接运行 SteamCMD 命令：
   ```powershell
   cd F:\SteamCMD
   .\steamcmd.exe +login e54385991 +workshop_build_item "F:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game\csgo_addons\upkkmodelpack2026_agents" +quit
   ```

## 当前配置状态

- ✅ 模型已编译到：`F:\CS2-ModelBuilder\compiled`
- ✅ 模型已复制到：`F:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game\csgo_addons\upkkmodelpack2026_agents`
- ✅ Workshop Item ID：`3716458508`
- ✅ BuildStats.md 已自动生成并提交到 GitHub

## GitHub Actions 工作流

### 1. Compile Models
- 手动触发编译
- 生成 BuildStats.md 并自动提交到仓库

### 2. Upload to Workshop
- 手动触发
- 将编译好的模型复制到本地创意工坊目录

## 快速命令

```powershell
# 编译模型
cd F:\CS2-ModelBuilder
uv run python compile_models.py

# 复制到创意工坊目录
uv run upload_to_workshop.py

# 查看 BuildStats
cat F:\CS2-ModelBuilder\compiled\BuildStats.md
```
