# ForHacker GitHub Org 初始化指南

## 前提条件

1. 你需要在 GitHub 上创建一个组织（Organization），建议名称：`forhacker`
   - 地址：https://github.com/organizations/plan
2. 安装 `gh` CLI（可选，但推荐）：https://cli.github.com/
3. 确认当前项目在 `E:\ProjectHJM\forhacker` 且所有测试通过

## 步骤 1：创建 GitHub Repos

在 `forhacker` org 下创建以下仓库（全部为空，不要勾选 README/LICENSE/.gitignore）：

| 仓库名 | 用途 |
|--------|------|
| `core` | 核心框架 |
| `plugin-forensics-core` | Cell: forensics-core |
| `plugin-file-analyzer` | Cell: file-analyzer |
| `plugin-log-parser` | Cell: log-parser |
| `plugin-network-forensics` | Cell: network-forensics |
| `plugin-registry-analyzer` | Cell: registry-analyzer |
| `plugin-browser-forensics` | Cell: browser-forensics |
| `plugin-email-forensics` | Cell: email-forensics |
| `plugin-timeline-analyzer` | Cell: timeline-analyzer |
| `knowledge-base` | 共享知识库 |
| `docs` | 中央文档 |

## 步骤 2：推送核心仓库

```bash
cd E:\ProjectHJM\forhacker
git remote add origin https://github.com/forhacker/core.git
git branch -M main
git push -u origin main
```

## 步骤 3：拆分 Cell 为独立仓库

### 方式 A：自动脚本

```bash
cd E:\ProjectHJM\forhacker
export FORHACKER_ORG="forhacker"
bash scripts/bootstrap-github.sh
```

### 方式 B：手动（以 forensics_core 为例）

```bash
# 1. 复制 Cell 到临时目录
cp -r cells/forensics_core /tmp/forensics-core
cd /tmp/forensics-core

# 2. 复制 CI 配置
mkdir -p .github/workflows
cp E:/ProjectHJM/forhacker/.github/workflows/quality.yml .github/workflows/

# 3. 初始化独立 git 仓库
git init
git checkout -b main
git add .
git commit -m "feat: forensics-core Cell plugin for ForHacker"
git remote add origin https://github.com/forhacker/plugin-forensics-core.git
git push -u origin main
```

对其余 7 个 Cell 重复上述步骤。

## 步骤 4：更新 Marketplace 地址

在 `E:\ProjectHJM\forhacker\plugins.yaml` 中，确认每个插件的 `repo_url` 指向正确的 GitHub 地址。推送更新：

```bash
cd E:\ProjectHJM\forhacker
git add plugins.yaml
git commit -m "chore: update marketplace URLs for live repos"
git push
```

## 步骤 5：验证

```bash
# 重新安装核心（确保 marketplace 读取最新 YAML）
cd E:\ProjectHJM\forhacker
pip install -e .

# 浏览 marketplace（应显示 8 个插件）
forhacker plugin marketplace

# 安装一个 Cell 插件（需要 gh CLI 或手动 git clone）
forhacker plugin install forensics-core
```

## 团队成员入门

每个成员执行：

```bash
# 1. 克隆核心
git clone https://github.com/forhacker/core
cd core
pip install -e ".[dev]"

# 2. 安装需要的 Cell 插件
forhacker plugin install forensics-core
forhacker plugin install log-parser
# ... 按需安装

# 3. 创建第一个 case
forhacker case create "my-first-case"

# 4. 运行取证管道
forhacker case run "my-first-case" "analyze this memory dump"

# 5. 查看 Dashboard
forhacker web serve
# 浏览器打开 http://localhost:8000
```

## Cell 贡献者入门

每个 Cell 贡献者：

```bash
# 1. 克隆自己要维护的 Cell
git clone https://github.com/forhacker/plugin-forensics-core
cd plugin-forensics-core

# 2. 安装开发依赖
pip install -e ".[dev]"

# 3. 跑测试
pytest tests/

# 4. 修改 plugin.py，添加新工具
# 5. 提交 PR，等待 CI 通过 + AI Code Review

# 6. 如果需要核心环境测试：
cd /path/to/core
ln -s /path/to/plugin-forensics-core cells/forensics_core
```
