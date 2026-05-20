# Brainstorming: AI电子取证平台 forhacker

**Date Started:** 2026-05-20
**Status:** Done
**Current Phase:** finalizing
**Based On:** —
**Final Spec:** docs/superpowers/specs/2026-05-21-forhacker-design.md
**Last Updated:** 2026-05-21 03:00

## Original User Request

> 我们正式开始我们的任务吧，"E:\ProjectHJM\forhacker"，在这个目录下，我计划开展一个项目，本项目的目前的，使用AIagent来辅助电子取证，之前也设计了一个类似的项目，在E:\项目下，有多个目录与之相关，但是，因为之前设计思路上的问题，缺少必要的规划和调试，导致之前的项目臃肿不堪，且几乎无法进行团队协作，我也感觉我自己的思路上其实一直都有些问题，所以我希望和你讨论来重构项目，包括项目开展的方法面面，甚至包括对于agent方案的调整，我们先想办法尽可能多的去讨论细节，并注重对于整体架构的设计，由于很可能对话很长，我要求你对对话做一个记录，在E:\ProjectHJM\forhacker\记录中，对话日志直接记录我们对话内容，设计日志则是记录下有意义，认为将要落实的内容

---

## Phase A: Alignment Decision Log

### Q1: 电子取证覆盖范围
**Options Presented:**
- A: 磁盘/文件系统取证
- B: 多源综合分析
- C: 取证流程自动化平台（可扩展agent框架）

**Decision:** C — 且范围更大：信息收集 + 大数据 + 渗透测试 + 电子取证 + CTF，定位为"应对网络犯罪的综合平台"

**Rationale:** 用户确认之前选的 C，现在想进一步扩展为涵盖更多安全领域的统一平台

**Timestamp:** 2026-05-20 23:05

### Q2: 范围分解与组织方式
**Options Presented:**
- A: 统一核心 + 领域插件（推荐）
- B: 先聚焦一个领域跑通 MVP
- C: 大一统平台一次性设计

**Decision:** A — 统一核心 + 领域插件

**Rationale:** 轻量 Agent 调度核心 + 各领域独立插件，避免旧项目臃肿问题，支持并行开发

**Timestamp:** 2026-05-20 23:10

### Q3: Agent 架构模式
**Options Presented:**
- A: 单 Agent + 工具链
- B: 多 Agent 协作（Supervisor 模式）
- C: 多 Agent 协作（Peer-to-Peer）

**Decision:** B — Supervisor 模式

**Rationale:** 调度 Agent 负责分解分配，专业子 Agent 各司其职，与 Superpowers 自身架构一致

**Timestamp:** 2026-05-20 23:15

### Q4: 核心技术栈
**Options Presented:**
- A: Python 全栈
- B: Go 核心 + Python 插件
- C: Python + Rust 性能层

**Decision:** C — Python 主体 + Rust (PyO3) 性能扩展

**Rationale:** Python 有最好的 AI/取证/安全工具生态，Rust 处理大数据和文件解析的性能瓶颈

**Timestamp:** 2026-05-20 23:20

### Q5: 插件系统设计
**Options Presented:**
- A: MCP 协议
- B: 自定义 Python 插件接口
- C: 混合方案（推荐）

**Decision:** C — Python 抽象类 + MCP Server 双模

**Rationale:** 内部深度集成不失灵活性，对外用 MCP 标准协议对接 AI 生态

**Timestamp:** 2026-05-20 23:25

### Q6: LLM 后端策略与切换粒度
**Options Presented:**
- A: 项目级切换
- B: Agent 级切换
- C: 全架构抽象 + 全局离线开关

**Decision:** C — 统一 LLM 抽象层 + 全局离线模式开关

**Rationale:** 一套代码覆盖所有场景（比赛在线/决赛离线/开发/训练/真实案件）。Agent 代码完全不感知后端差异，`LLMBackend` 统一接口下适配 OpenAI / Anthropic / DeepSeek / Ollama / vLLM

**Additional Context from User:**
- 短期依赖云端 API 赢得线上赛、加速开发
- 中长期必须支持纯本地部署（断网决赛、真实案件）
- 需要本地模型训练和测试的完整流程
- 四种场景需统一架构支撑

**Timestamp:** 2026-05-20 23:30

### Q7: Agent 间通信协议
**Options Presented:**
- A: 进程内直接调用
- B: 消息队列
- C: 抽象通信层 + 双模实现

**Decision:** C — MessageBus 抽象层，默认进程内，可选 Redis/NATS 分布式

**Rationale:** 与 LLM 层、插件层一致的设计哲学：抽象接口 + 多实现。单机零依赖，团队可扩展

**Timestamp:** 2026-05-20 23:35

### Q8: 任务编排引擎
**Options Presented:**
- A: 静态 DAG
- B: 动态任务树
- C: DAG + 动态扩展

**Decision:** C — DAG 基础 + 运行时动态追加节点

**Rationale:** 兼顾取证比赛的结构化流程和真实调查的探索性。有 DAG 才有审计链和断点续跑，动态扩展保证灵活性

**Timestamp:** 2026-05-20 23:40

### Q9: 数据层与证据管理
**Options Presented:**
- A: PostgreSQL + 文件系统
- B: PostgreSQL + MinIO/S3
- C: Neo4j + PostgreSQL + 文件系统

**Decision:** PostgreSQL + 本地文件系统（经 Q21 修正）

**Rationale:** 团队远程协作是核心需求。PostgreSQL 管理结构化数据和审计链。MinIO 在服务器 20G 磁盘上不现实（检材几百GB），证据存本地 `cases/<case-id>/evidence/`，后续有经费再扩展

**Timestamp:** 2026-05-20 23:45 | **修正:** 2026-05-21 01:20 (Q21)

### Q10: 安全隔离与沙箱
**Options Presented:**
- A: Docker + WSL2 Firecracker（本地分级隔离）
- B: 本地 Docker + 云端强隔离
- C: 全分层方案

**Decision:** A — Docker + WSL2 Firecracker 本地分级隔离

**Rationale:** 服务器配置低(2C8G20G)只做辅助；笔记本是主力。常规任务 Docker 隔离，高风险任务 WSL2 内 Firecracker microVM 隔离。断网决赛场景完整可用

**Timestamp:** 2026-05-20 23:50

### Q11: 用户界面
**Options Presented:**
- A: Web 全栈
- B: CLI 优先 + Web 辅助
- C: Tauri 桌面应用

**Decision:** B — CLI 优先 + Web 辅助可视化

**Rationale:** CTF 比赛场景要求速度和可脚本化，CLI 效率最高；复杂取证可视化（时间线、关联图）走本地 Web Dashboard

**Timestamp:** 2026-05-20 23:55

### Q12: 团队协作模型
**Options Presented:**
- A: 案件为中心 + 角色权限
- B: Git 式分支协作
- C: 混合模型

**Decision:** C — 案件空间 + 角色权限 + DAG 任务分配 + Finding 提交/审核

**Rationale:** 结构化的任务分工避免冲突，Finding 级别的审核合并提供质量门控，全局共享的证据索引让所有成员可见

**Timestamp:** 2026-05-21 00:00

### Q13: 插件 SDK 与开发体验
**Options Presented:**
- A: 最小 SDK
- B: 脚手架 CLI + 模板
- C: 内部插件市场

**Decision:** C — 脚手架 CLI + 内部插件市场

**Rationale:** 统一插件结构保证团队协作不乱，内部市场让领域插件可积累、可复用、可版本管理

**Timestamp:** 2026-05-21 00:05

### Q14: 代码仓库结构
**Options Presented:**
- A: 严格 Monorepo + 分支保护
- B: 核心 Monorepo + 插件独立 Repo
- C: 完全联邦制

**Decision:** B — 核心 Monorepo + 插件独立 Repo

**Rationale:** 团队是警院学生（~10人，水平不一，每周仅2-4小时同步）。你亲手控核心框架；每个领域插件独立 repo 分配给 1-2 人 owner，通过模板保证一致性，PR 集成时你用 AI Code Review 把控质量。零基础成员从测试/文档起步，逐步接手简单插件

**Additional Context（团队画像）:**
- 5人有基础 → 插件 owner，管理自己的 AI 干活
- 2人有想法 → 核心贡献 + Code Review 辅助
- 3人零基础 → 测试、文档、报告生成、先跟 AI 学
- 协作窗口：每周 1-2 次 × 2小时线下同步
- 核心理念：成员当小组长，AI 是手下员工

**Timestamp:** 2026-05-21 00:15

### Q15: 第一个迭代目标
**Options Presented:**
- A: 先做核心最小骨架
- B: 先做垂直切片
- C: 双线并行

**Decision:** C — 你+师兄做核心骨架，竞赛选手并行做取证插件 MVP

**Rationale:** 核心框架设计是当前讨论的焦点——必须适配 Cell 团队模型、有足够弹性、能真正完成任务。同时取证插件团队不需要等核心完全定型即可基于旧知识库开始

**Timestamp:** 2026-05-21 00:30

### Q16: MetaAgent — 系统自我进化机制
**Options Presented:**
- A: 定时巡检 + 人工审核
- B: 全自动闭环
- C: 知识搬运靠人

**Decision:** A — 定时巡检 + 人工审核

**Rationale:** MetaAgent 两个目标：① 追踪取证领域新工具/技术/WriteUp ② 追踪 AI/Agent 平台本身的优化方案（新 prompt 技巧、新 Claude Code 功能、新 MCP 工具、新 skill 模式）。源包括 GitHub、arXiv、CTF writeup 站、安全博客、B站、主流技术媒体。人类审核是安全阀——取证场景准确率优先

**Additional Context:**
- 当前 Claude Code + DeepSeek 方案仍有很多手动环节，MetaAgent 应主动发现优化方案
- AI 圈子日新月异，一个人追踪不现实，这正是 AI 比人强的场景
- 项目目前仍停留在问答模式，需要向真正的自动化迈进

**Timestamp:** 2026-05-21 00:35

### Q16.1: MetaAgent 自主级别
**Options Presented:**
- A: 信息收集全自动，行动建议人工批
- B: 低风险自主，高风险人工
- C: 全自主但有回滚

**Decision:** A — 但人类批准后可自动执行安装，每次安装有日志、可回滚、安装前备份

**Rationale:**
- 信息收集/搜索/浏览/摘要全自动
- 改进建议提交人类审核时必须说明：该功能有什么用、对项目的作用和影响、价值
- 必要时 MetaAgent 应协调项目的整体改动（不只是单点建议）
- 人类批准后自动安装，但全程记录审计日志 + 备份原方案，支持一键回滚
- MetaAgent 不能自主修改代码/prompt/配置，扳机永远在人类手里

**MetaAgent 四角色:**
1. 设计调研员 — 每次设计前搜索现有方案、论文、开源项目
2. 持续观察员 — 7×24 监控多源，生成改进建议
3. 网络操作员 — 情报收集、舆情监控，提供浏览器基础设施给其他插件复用
4. 自优化引擎 — 发现 AI/Agent 平台本身的优化方案

**Timestamp:** 2026-05-21 00:45

### Q17: AI 产出代码质量保证
**Options Presented:**
- A: CI 铁闸 + AI Code Review
- B: 核心 Cell 逐 PR 人工审核
- C: 信任为主

**Decision:** A — CI 铁闸 + AI Code Review，人类可通过手机异步审批

**Rationale:** CI 自动执行不伤感情，零基础在报错中学习，核心 Cell 只做策略审核。审批结果通过手机 Bot 推送（见 Q18）

**Timestamp:** 2026-05-21 00:50

### Q18: 移动端异步交互通道
**Options Presented:**
- A: Claude Code 管道 + HTTP 转发
- B: Claude Code 长会话 + 文件轮询 + Bot
- C: 远程桌面先过渡

**Decision:** 分两步 — 现在用 C（Chrome Remote Desktop / Microsoft Remote Desktop）立刻实现手机对话；后续用 AI 开发 B（企业微信/Telegram Bot + 文件桥接）作为正式方案

**Rationale:** C 零开发、现在就能用、今晚就能从手机发消息。B 完成后可实现手机审批 MetaAgent 建议、查看 CI 结果、接收 AI Code Review 通知

**Additional Notes — MetaAgent 调度:**
- 默认每天自动巡检一次（定时可配置）
- 支持手动即时触发
- 发现成果定时报告，手机可接收（Q18-B 完成后）
- Chrome Remote Desktop 设为独立子任务，后续派 agent 执行

**Timestamp:** 2026-05-21 01:00

### Q19: 知识在 Cell 之间的流动
**Options Presented:**
- A: 共享 knowledge-base repo + CI 自动汇入
- B: Cell 各自维护 + 跨 repo 搜索
- C: knowledge-base 为唯一真相源 + 审核入库

**Decision:** A — 共享 knowledge-base repo + CI 自动汇入

**Rationale:** 每个 Cell repo 的 `knowledge/` 目录 CI 自动同步到中央 knowledge-base，全局索引可搜索。零人力开销、知识不碎片化

**Additional Context:**
- 手机操控 agent 独立为 `E:\ProjectHJM\手机操控agent` 项目，不纳入 MetaAgent 初始需求
- 当前方案整体先聚焦电脑端使用
- 公网服务器 (2C8G) 可用作中继，不承载 Agent 推理

**Timestamp:** 2026-05-21 01:05

### Q20: 比赛实战流程
**Options Presented:**
- A: 赛前准备 + 赛中各自作战
- B: 指挥端集中调度
- C: 混合模式

**Decision:** B — 指挥端集中调度（Supervisor 分解任务 → 分配成员 → 汇总答案）

**Timestamp:** 2026-05-21 01:10

### Q20.1: 远程协作传输层
**Options Presented:**
- A: Syncthing（推荐，P2P + NAT穿透 + 中继）
- B: 自建 Relay（旧项目方案）
- C: Git Auto-Sync

**Decision:** A — Syncthing

**Rationale:** 成熟方案，千万用户验证，自动处理 NAT 穿透/断线/LAN/中继全部场景。AI 只读写本地文件，搬运是程序的事。公网服务器做中继节点

**Additional Context:**
- 远程协作主要用于日常训练和线上赛
- 线下赛（断网）协作方案预留插件位置，有资格进线下赛/实际工作前不开发
- 原则：能交给程序的绝不交给 AI

**Timestamp:** 2026-05-21 01:15

### Q21: 公网服务器角色
**Options Presented:**
- A: 元数据+协作中继
- B: 证据分布式 MinIO + 服务器索引
- C: 文件系统管理证据

**Decision:** 服务器仅做 Syncthing 中继 + PostgreSQL 元数据

**Rationale:** 服务器 2C8G 20G，检材镜像几百GB不可能存。检材各电脑自行下载，Syncthing 只同步小文件（YAML/JSON/MD），证据在本地按 `cases/<case-id>/evidence/` 管理。后续有经费再扩展存储

**Timestamp:** 2026-05-21 01:20

---

## Phase A → B Transition Confirmation [2026-05-21 01:30]

**Alignment Summary (compiled by Agent):**

### 项目定位
1. **Q1**: 范围覆盖信息收集、大数据、渗透、取证、CTF——"应对网络犯罪的综合平台"
2. **Q2**: 统一核心 + 领域插件，避免旧项目臃肿

### 架构设计
3. **Q3**: Supervisor 多 Agent 协作模式（调度 Agent + 专业子 Agent）
4. **Q4**: Python 主体 + Rust (PyO3) 处理性能瓶颈
5. **Q5**: 插件系统 = Python 抽象类 + MCP Server 双模
6. **Q6**: LLM 统一抽象层 + 全局离线开关（适配 OpenAI/Anthropic/DeepSeek/Ollama/vLLM）
7. **Q7**: MessageBus 抽象通信层，默认进程内，可选 Redis/NATS
8. **Q8**: DAG 任务引擎 + 运行时动态扩展
9. **Q9**: PostgreSQL + 本地文件系统（修正：不做 MinIO）

### 基础设施
10. **Q10**: Docker + WSL2 Firecracker 分级隔离（常规任务 Docker，高风险 VM）
11. **Q11**: CLI 优先 + Web 辅助可视化
12. **Q21**: 公网服务器仅做 Syncthing 中继 + PostgreSQL

### 团队与协作
13. **Q12**: 案件空间 + 角色权限 + DAG 任务分配 + Finding 审核
14. **Q13**: 脚手架 CLI + 内部插件市场
15. **Q14**: 核心 Monorepo + 插件独立 Repo（GitHub Organization: forhacker）
16. **Q17**: CI 铁闸 + AI Code Review 自动质量门禁
17. **Q18**: 手机交互分两步——先用 Chrome Remote Desktop，后建 Bot 桥接
18. **Q19**: 共享 knowledge-base repo + CI 自动汇入
19. **Q20/Q20.1**: 比赛指挥端集中调度 + Syncthing 远程协作（线下赛协作预留插件位）

### MetaAgent（核心差异化）
20. **Q16**: 四角色——设计调研员 + 持续观察员 + 网络操作员 + 自优化引擎
21. **Q16.1**: 信息收集全自动，行动人类批准后执行，全程审计 + 可回滚
22. **Q15**: 第一个迭代：核心骨架 + 取证插件 MVP 双线并行

### 团队文化（非技术决策，但同等重要）
- Cell 制，不是部门制——每个人 + AI = 一个独立生产力单元
- AI 是真·生产力，不是噱头——AI 使用方案本身是核心竞争力
- 去官僚化——靠产出说话，不依赖学校审批
- 教育是产出的一部分——每个模块有 TUTORIAL.md，零基础可上手
- 遗留遗产——文档、接口、模板均独立于平台/模型/工具链

### 文档体系
- **Q22**: VISION.md + docs/superpowers/ + tutorials/ + 每 Cell 的 TUTORIAL.md

**User Confirmation:** ✓ Confirmed

---

## Phase B: Spec Writing Status

- [✓] Initial draft complete (2026-05-21 02:00)
- [✓] Round 1 revision (2026-05-21 02:30)
- [✓] Round 2 revision (2026-05-21 03:00)
- [ ] Round 3 revision
- [ ] Final sign-off

## Phase B Review Progress

### Round 1 [✓ completed]

**Dispatched reviewers (6):** architect | red-team | edge-cases | yagni-gatekeeper | exemplar-matcher(worktree-rototill) | exemplar-matcher(codex-app-compatibility)

**Receipt Status:** architect ✓ | red-team ✓ | edge-cases ✓ | yagni-gatekeeper ✓ | exemplar-matcher(worktree-rototill) ✓ | exemplar-matcher(codex-app-compatibility) ✓

**Findings:**

| ID | Sev | Location | Reviewer | Problem | Arbiter | Status |
|----|-----|----------|----------|---------|---------|--------|
| F1.1 | BLOCKING | §1.3 Task Engine | architect | SubAgent execution contract not defined | KEEP | ✓ FIXED |
| F1.2 | BLOCKING | §1.3/§1.4 Supervisor+Plugin | architect | Capability registry has no named interface | KEEP | ✓ FIXED |
| F1.3 | IMPORTANT | §3.1 Data Layer | architect | No data access abstraction layer | KEEP | ✓ FIXED |
| F1.4 | IMPORTANT | §1.3/§5.2 DAG+Shared | architect | DAG persistence boundary undefined | KEEP | ✓ FIXED |
| F1.5 | IMPORTANT | §5.2 Shared State | architect | Schema version field missing | KEEP | ✓ FIXED |
| F1.6 | NIT | §3.2 evidence.py | architect | evidence.py mixes FS and DB concerns | APPENDIX | — |
| F1.7 | BLOCKING | §5.2 Finding IDs | red-team, edge-cases | Sequential IDs collide under concurrency | KEEP (merged) | ✓ FIXED |
| F1.8 | BLOCKING | §4 Security Isolation | red-team, edge-cases | HIGH-risk silently downgraded to Docker | KEEP (merged) | ✓ FIXED |
| F1.9 | IMPORTANT | §3.1/§7 KB Flow | red-team | PostgreSQL findings no automation to KB | KEEP | ✓ FIXED |
| F1.10 | IMPORTANT | §5.3 CI Gates / Risks | red-team | CI gates don't enforce workflow claim | KEEP | ✓ FIXED |
| F1.11 | NIT | §1.3/§Design Principles | red-team | Two confidence vocabularies share field name | APPENDIX | — |
| F1.12 | BLOCKING | §4 Security Router | edge-cases | Unknown task type has undefined risk default | KEEP | ✓ FIXED |
| F1.13 | BLOCKING | §2.2/§2.3 MetaAgent | edge-cases | Overlapping scans with no mutex | KEEP | ✓ FIXED |
| F1.14 | BLOCKING | §1.3 Task Engine | edge-cases | Tasks stuck in blocked on dependency fail | KEEP | ✓ FIXED |
| F1.15 | BLOCKING | §1.3/§5.2 Supervisor | edge-cases | Supervisor crash loses in-flight state | KEEP | ✓ FIXED |
| F1.16 | BLOCKING | §5.2 Syncthing | edge-cases | Syncthing conflict files break shared state | KEEP | ✓ FIXED |
| F1.17 | IMPORTANT | §1.1 LLMBackend | edge-cases | No retry/timeout/circuit-breaker | KEEP | ✓ FIXED |
| F1.18 | IMPORTANT | §1.4 PluginManager | edge-cases | Plugin load failure undefined behavior | KEEP | ✓ FIXED |
| F1.19 | IMPORTANT | §3.2 Evidence SHA256 | edge-cases | Hash mismatch has no action protocol | KEEP | ✓ FIXED |
| F1.20 | IMPORTANT | §3.1 agents table | edge-cases | Heartbeat staleness and reassignment undefined | KEEP | ✓ FIXED |
| F1.21 | IMPORTANT | §3 Data Layer | edge-cases | No PostgreSQL connection failure handling | KEEP | ✓ FIXED |
| F1.22 | IMPORTANT | §7 KB Dedup | edge-cases | KB dedup strategy unspecified | KEEP | ✓ FIXED |
| F1.23 | IMPORTANT | §2.3 Evaluator | edge-cases | Evaluator miscalibration dead loop | KEEP | ✓ FIXED |
| F1.24 | IMPORTANT | §2.3 Rollback | edge-cases | Rollback of partial failure undefined | KEEP | ✓ FIXED |
| F1.25 | NIT | §6.1 CLI | edge-cases | case status undefined for no case | APPENDIX | — |
| F1.26 | NIT | §6.2 Dashboard | edge-cases | Port conflict no detection | APPENDIX | — |
| F1.27 | IMPORTANT | §1.2 bus/redis_nats.py | yagni-gatekeeper | RedisNatsBus has zero consumers | KEEP | ✓ FIXED |
| F1.28 | IMPORTANT | §1.4 BasePlugin ABC | yagni-gatekeeper | register_agents() orphaned interface | KEEP | ✓ FIXED |
| F1.29 | NIT | §1.2 redis_nats.py name | yagni-gatekeeper | Filename bundles two technologies | APPENDIX | — |
| F1.30 | IMPORTANT | §2.1 browser.py | yagni-gatekeeper | "stealth browser" over-scopes | KEEP | ✓ FIXED |
| F1.31 | IMPORTANT | §Risks | exemplar-matcher(worktree) | Risk section lacks status labels + cross-validation table | KEEP | ✓ FIXED |
| F1.32 | IMPORTANT | §Design (cross) | exemplar-matcher(worktree) | No inline TDD design revision narrative | KEEP | ✓ FIXED |
| F1.33 | IMPORTANT | Header/§Design | exemplar-matcher(worktree) | No traceability table for 22 decisions | KEEP | ✓ FIXED |
| F1.34 | NIT | §1.1/§4 routers | exemplar-matcher(worktree) | Conditional logic prose instead of tables | APPENDIX | — |
| F1.35 | BLOCKING | Cross-cutting | exemplar-matcher(codex) | Empirical findings table absent | KEEP | ✓ FIXED |
| F1.36 | IMPORTANT | Cross-cutting | exemplar-matcher(codex) | Decision matrix absent | KEEP | ✓ FIXED |
| F1.37 | IMPORTANT | Cross-cutting | exemplar-matcher(codex) | What-Does-NOT-Change preservation list absent | KEEP | ✓ FIXED |
| F1.38 | IMPORTANT | §File Inventory | exemplar-matcher(codex) | Scope summary table with line counts absent | KEEP | ✓ FIXED |
| F1.39 | NIT | §Testing Strategy | exemplar-matcher(codex) | Test cases not numbered | APPENDIX | — |
| F1.40 | NIT | Cross-cutting | exemplar-matcher(codex) | Future Considerations section absent | APPENDIX | — |
| F1.41 | NIT | §1.1 LLMResponse | edge-cases | Truncated LLM finish_reason unhandled | APPENDIX | — |

**Arbiter Output:**
- counts: raw=43 → dedup=39 → after_filter=31
- degradation_check: N/A (round 1)
- convergence_status: CONTINUE
- arbiter_rationale: 4 dedup pairs merged (finding ID collision, silent risk downgrade, RedisNatsBus filename, decision table). No false discards, no conflicts. 8 NITs moved to appendix. 31 effective findings (10 BLOCKING + 21 IMPORTANT). Core themes: shared state protocol is densest cluster, interface contracts missing in 3 areas, 2 dead YAGNI interfaces, both exemplar-matchers flagged same structural gaps.

### Appendix (NITs)

- F1.6: evidence.py mixes FS and DB concerns under data/ — consider splitting
- F1.11: Task confidence (HIGH/MEDIUM/LOW) vs finding confidence (verified/inferred/unknown) share field name — disambiguate
- F1.25: `forhacker case status` undefined for no active case or zero tasks
- F1.26: Web dashboard port conflict with no port selection
- F1.29: redis_nats.py filename bundles two technologies — pick one if retained
- F1.34: Conditional logic in prose — convert routers to decision-outcome tables
- F1.39: Test cases not numbered — add sequential numbering and pass/fail criteria
- F1.40: Future Considerations section absent — add deferred design decisions with triggers
- F1.41: Truncated LLM output (finish_reason=length) unhandled

---

### Round 2 [STOP_DEGENERATE]

**Dispatched reviewers (6):** architect | red-team | edge-cases | yagni-gatekeeper | exemplar-matcher(worktree-rototill) | exemplar-matcher(codex-app-compatibility)

**Receipt Status:** architect ✓ | red-team ✓ | edge-cases ✓ | yagni-gatekeeper ✓ | exemplar-matcher(worktree-rototill) ✓ | exemplar-matcher(codex-app-compatibility) ✓

**Findings:**

| ID | Sev | Location | Reviewer | Problem | Arbiter | Status |
|----|-----|----------|----------|---------|---------|--------|
| F2.1 | BLOCKING | §3.1 Data access pattern | architect | Contradictory two-path data docs | KEEP | ✓ FIXED |
| F2.2 | BLOCKING | §1.1 LLMBackend.complete() | red-team | Cannot represent chat messages/tools | KEEP | ✓ FIXED |
| F2.3 | BLOCKING | §1.3 Cascade failure + state machine | red-team | No failed→blocked recovery transition | KEEP | ✓ FIXED |
| F2.4 | BLOCKING | §3.1 degraded × §3.2 evidence hash | red-team | evidence_index not in shared/ for degraded | KEEP | ✓ FIXED |
| F2.5 | BLOCKING | §3.1 degraded × agent heartbeat | red-team | Heartbeat not in shared/ for degraded | KEEP | ✓ FIXED |
| F2.6 | BLOCKING | §1.4 Plugin dependencies | edge-cases | No cycle detection in plugin deps | KEEP | ✓ FIXED |
| F2.7 | BLOCKING | §1.3 Supervisor + CapabilityRegistry | edge-cases | Empty registry → zero-task DAG undefined | KEEP | ✓ FIXED |
| F2.8 | BLOCKING | §1.3 Dynamic add_task + cycle detect | edge-cases, red-team | Cycle detection not mandated per call | KEEP (merged) | ✓ FIXED |
| F2.9 | IMPORTANT | §1.4 CapabilityRegistry placement | architect | task/→plugin/ dependency inverted | KEEP | ✓ FIXED |
| F2.10 | IMPORTANT | §2.1 Platform Optimizer | architect | No introspection interface for platform | KEEP | ✓ FIXED |
| F2.11 | IMPORTANT | §1.3 Supervisor recovery × add_task | red-team | Dynamic tasks lost between checkpoints | KEEP | ✓ FIXED |
| F2.12 | IMPORTANT | §2.3 MetaAgent file-based lock | red-team | File lock TOCTOU race in Syncthing | KEEP | ✓ FIXED |
| F2.13 | IMPORTANT | §7 KB pipeline × confidence | red-team | 3 confidence taxonomies, no mapping | KEEP | ✓ FIXED |
| F2.14 | IMPORTANT | §3.2 Evidence index orphans | edge-cases | Orphan entries, integrity=missing undefined | KEEP | ✓ FIXED |
| F2.15 | IMPORTANT | §5.2 Syncthing conflict resolution | edge-cases | Detection but no resolution procedure | KEEP | ✓ FIXED |
| F2.16 | IMPORTANT | §3.1 PostgreSQL reconciliation | edge-cases | One-way sync overwrites PG-only data | KEEP | ✓ FIXED |
| F2.17 | IMPORTANT | §7 KB pipeline case update | edge-cases | Re-ingestion on case update undefined | KEEP | ✓ FIXED |
| F2.18 | IMPORTANT | §5.2 messages/ + progress.yaml | yagni-gatekeeper | Zero-spec entries in shared/ tree | KEEP | ✓ FIXED |
| F2.19 | IMPORTANT | §1.4 get_agent_roles + scaffolding | yagni-gatekeeper | Orphaned after register_agents removed | KEEP | ✓ FIXED |
| F2.20 | IMPORTANT | §Risks R2 narrative depth | exemplar-matcher | HIGH risk too condensed vs sample | KEEP | ✓ FIXED |

**Arbiter Output:**
- counts: raw=34 → dedup=34 → after_filter=34
- degradation_check: FAILED (20 > 0.5 × 31 = 15.5)
- convergence_status: STOP_DEGENERATE
- arbiter_rationale: 20 effective findings (8 BLOCKING + 12 IMPORTANT) = 64.5% of Round 1's 31, exceeding 50% threshold. Reviewers found new categories (degraded-mode integrity gaps, LLMBackend type-system holes, cycle detection in 2 subsystems, contradictory docs) rather than refining prior findings. Expected for greenfield spec. Correct action: apply 20 revisions, end loop.

### Appendix (NITs)

- F2.21: Relocate MCP server from plugin/ to forhacker/server/mcp.py
- F2.22: Document task/ → collab/shared.py dependency
- F2.23: Add dependency_findings to SubAgentContext
- F2.24: Split evaluator watchdog: M>0 vs M=0
- F2.25: Note: empty risk_levels {} = all HIGH for plugin tools
- F2.26: Define empty state UI for web dashboard
- F2.27: Atomic dag_state.yaml write (temp file + rename)
- F2.28: Narrow syncthing.py to "health check" only
- F2.29: Risk headings with inline status labels
- F2.30: Inline design rationale for 2-3 key decisions
- F2.31: Label manual tests (T7-T11, T14)
- F2.32: Add fail-mode narratives for T14
- F2.33: Per-phase LOC estimates in phase headings

---

## Phase B User Intervention Decisions

### I1: Round 2 STOP_DEGENERATE — Accept All Findings [2026-05-21 03:00]
**Context:** Round 2 degradation check failed (20 > 50% × 31). Arbiter recommended applying all 20 revisions and ending the loop.
**User Decision:** "A" — 全部接受并修复 (accept all 20 findings + 13 NITs and fix)
**Rationale:** User accepted the arbiter's recommendation without individual negotiation.
**Disposition:** All 20 findings + 13 NITs applied to spec. Loop terminated.
