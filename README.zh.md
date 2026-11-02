# ZCode Pipeline

[English](README.en.md) · [Русский](README.ru.md) · [中文](README.zh.md) · [返回简要 README](README.md)

面向 [ZCode](https://z.ai) 的多智能体开发流水线：通过一组专职子智能体，把用户的原始需求转化为一条经过验证、正式验收的变更——强制执行需求简报、架构设计、任务分解、三重评审、QA 以及持续更新的知识库。

## 解决什么问题

| LLM 智能体的典型问题 | 流水线的强制约束 |
|---|---|
| 猜测含糊的需求 | **Briefer（需求访谈）** 通过多轮交互式提问产出完整简报；后续智能体没有简报一律拒绝启动 |
| 不做设计直接写码 | **Architect（架构师）** 产出设计方案，*并向后续所有智能体下达强制性建议* |
| 产出模糊的巨型任务 | **Tech Lead（技术负责人）** 分解出边界清晰、带契约的任务；**Tech Writer（技术撰稿人）** 生成自包含的任务文件（内联规则、目标形态、验收标准） |
| 不跑测试就宣称"测试通过" | **Developer（执行者）** 必须用真实命令输出证明每一条声明；评审者独立复核 |
| 给自己的工作盖橡皮章 | 三道独立的只读评审——**Security（安全）**、**Goal（目标）**、**Code（代码）**——循环直至*完全*通过（连 NIT 级别的发现也必须修复） |
| 接受半成品 | **QA** 真实运行测试（并可补充自己的测试）；**Manager（经理）** 将初始数据与最终产物逐项对trace，给出 `ACCEPTED`/`REJECTED` |
| 下个会话就全忘了 | **Summarizer（总结者）** 把每个已验收的史诗蒸馏进活文档（`.ai/docs/`），供下个史诗的智能体阅读 |
| 无视项目规范 | **Initializer（初始化器）** 按技术栈抓取当前最佳实践到 `.ai/guides/`，并接入项目 `AGENTS.md` |

## 工作原理

```
/init-project（每个项目一次）
      │
      ▼
初始化器 → 需求访谈 → 架构师 → 技术负责人 → 技术撰稿人 → 执行者
      │                                                        │
      │                            评审循环直至完全通过：
      │                            安全 → 目标 → 代码 ──────────┤
      │                                                        ▼
      │                     QA（QUALITY_PASSED）→ 经理（ACCEPTED）→ 总结者 → 提交
```

- **主智能体负责协调**：调度子智能体、把他们的提问块交互式渲染给用户（多选 + 自由输入）、维护任务状态；只有主智能体可以提交代码。
- **`pipeline` 技能**承载协调规则，按需加载（"跑一下流水线"、提及流水线阶段、或在含 `.ai/` 产物的项目中工作时触发）。
- **升级机制（Escalation）**：被卡住的智能体返回结构化标记 `!!! ESCALATION !!!`；协调者将其路由给技术负责人顾问，并把约束性决议送回。每个智能体每个任务最多一次升级——瞎猜即违反流程。
- **阶段门禁**写入每个智能体的提示词：没有简报 → 没有架构；没有分解 → 没有任务；评审未全部通过 → 没有 QA；没有 `ACCEPTED` → 没有提交。

## 12 个智能体

| 智能体 | 职责 | 产出 / 结论 |
|---|---|---|
| `initializer` | 阶段 0：识别/询问技术栈，收集当前最佳实践 | `.ai/guides/{tech}.md`、项目 `AGENTS.md` |
| `briefer` | 通过提问把任意原始需求变成最终简报 | `.ai/briefs/{epic}-brief.md` |
| `architect` | 设计方案；向后续智能体给出强制建议 | `.ai/architecture/{epic}-architecture.md` |
| `tech-lead` | 分解为边界清晰的任务（不写任务文件）；裁决升级 | `.ai/decomposition/{epic}-decomposition.md` |
| `tech-writer` | 依据分解生成自包含的任务文件 | `.ai/tasks/{epic}/{NN}-{name}-{date}.md` + `INDEX.md` |
| `developer` | 严格按任务文件实现；动码前必须 Phase 0；诚实验证 | 报告 + 状态 `implemented` |
| `security-review` | 只报告真实可利用的风险，须附证据 | `PASS / PASS_WITH_WARNINGS / FAIL / NEEDS_MORE_CONTEXT` |
| `goal-review` | 把每条验收标准对trace到证据；抓范围蔓延 | `GOAL_MET / GOAL_PARTIALLY_MET / GOAL_NOT_MET / NEEDS_CONTEXT` |
| `code-review` | 正确性、边界情况、规范、diff 卫生、测试完整性 | `APPROVE / REQUEST_CHANGES / NEEDS_DISCUSSION` |
| `qa` | 评审测试覆盖、真实运行检查、可补写自己的测试 | `QUALITY_PASSED / QUALITY_FAILED / BLOCKED` |
| `manager` | 终审：初始数据 vs 最终产物，证据可trace | `ACCEPTED / REJECTED` + 退回阶段 |
| `summarizer` | ACCEPTED 之后：把史诗蒸馏进知识库 | `.ai/docs/` wiki + 编年史 + `INDEX.md` |

## 产物与状态

每个项目都会留下 `.ai/` 轨迹：`briefs/ · architecture/ · decomposition/ · tasks/{epic}/ (+INDEX.md) · reviews/ · qa/ · guides/ · docs/`（知识库：`wiki/{component}.md`、`epics/{epic}-{date}/REPORT.md`、`INDEX.md`、`manual-checklist.md`）。

任务生命周期：`created → in_progress → implemented → reviewed → tested → accepted | rejected`。

wiki 具有权威性但可验证：页面带有"已在某 commit 验证"戳记，并要求读者将断言与实际代码复核。

## 安装

**插件市场（主渠道）：**
1. ZCode → Plugin Marketplace → **Add → Add Plugin Marketplace** → 粘贴本仓库 URL。
2. **Personal → ZCode Pipeline → Install** → 重启会话。
3. 验证：12 个智能体、`/init-project` 命令、`pipeline` 技能。

**备选渠道（无市场）：** 在 ZCode 中打开 `zcode-pipeline-bundle.md` 并说"按此文档安装"——它会在用户作用域重建全部文件。

## 使用

```
/init-project                                # 每个项目一次
"跑一下流水线：增加密码短语模式"               # 任意功能/修复/重构
```

之后只需回答交互式提问——阶段顺序、评审、修复、状态与提交全部由流水线驱动。

## 仓库结构与贡献

```
marketplace.json            # 市场目录（仓库根 = 市场）
zcode-pipeline/             # 插件（目录名 == 清单名）
  .zcode-plugin/plugin.json
  agents/                   # 12 个子智能体
  commands/init-project.md
  skills/pipeline/SKILL.md  # 协调者规则
  assets/AGENTS-template.md # 带个性化占位符的全局规则模板
scripts/build_bundle.py     # bundle 构建器（仓库自包含）
zcode-pipeline-bundle.md    # 生成产物——请勿手改
```

更新流程（提交与 CHANGELOG 使用英文）：
1. 只修改 `zcode-pipeline/{agents,commands,skills,assets}`。
2. 同步更新 `zcode-pipeline/.zcode-plugin/plugin.json` 与 `marketplace.json` 中的 `version`。
3. `python3 scripts/build_bundle.py`（检测到个人数据泄漏或标记损坏时会直接失败——不要绕过）。
4. 提交 + CHANGELOG 记录；里程碑打 tag；`git push --follow-tags`。
5. 在 ZCode → Settings → Plugins 中更新插件。

历史：[CHANGELOG.md](CHANGELOG.md)
