---
name: yms-brainstorm
description: |
  BrainStorm 外部大脑：想法不过夜，做过的事也不过夜。随手说的原话按顺序存档；整理成事实 / 解释 / 假设 / 情绪的 Insight；记下今天真的做了什么；维护长期记忆和当前状态机；把感悟沉淀成短期灵感、长期框架、执行清单；把多年的旧日志整理成可检索的地图。
  六个动作：记下来 capture、整理 insight、动作记录 action-log、沉淀 distill、状态机与回看 status-review、历史资料入职 history-onboarding。
  触发：/yms-brainstorm、「开始今天的头脑风暴」「帮我记下来」「整理一下今天说的」「记一下我今天做了什么」「更新状态机」「这周回看一下」「月度总结」「把这个感悟沉淀下来」「整理我的历史投资资料」
  External brain for an investor: verbatim capture, insight, action log, memory and status, distilled frameworks, history onboarding. Trigger: /yms-brainstorm, "start today's brainstorm", "note this down", "summarize what I said today", "update my status".
---

# BrainStorm · yms-brainstorm

> 跟 AI 聊完就关掉，等于每次从零开始。这个模块只做一件事：让你每次想过的、做过的，都留下来，变成下一次能直接用的东西。
> 来自《AI 投资指南》04 策略层 §七 · 06 进阶篇 §五–六

## 这个模块里有什么

| 你说 | 做什么 | 读 |
|:---|:---|:---|
| 「开始今天的头脑风暴」「帮我记下来」 | 先读你的长期记忆和当前状态，再让你随便说；原话按说话顺序存档 | `references/capture.md` |
| 「整理一下今天说的」 | 把原话拆成事实 / 解释 / 假设 / 情绪，写成一份 Insight，主线是你的原话 | `references/insight.md` |
| 「记一下我今天做了什么」 | 动作记录：读了哪份原件、跑了哪个流程、改了哪条规则、在哪一步犹豫了 | `references/action-log.md` |
| 「把这个感悟沉淀下来」 | 选去向：长期记忆、短期灵感、长期框架、执行清单，或者走规则变更 | `references/distill.md` |
| 「更新状态机」「这周回看一下」「月度总结」 | 刷新当前状态；对照这一周的想法和动作；到期的假设对真值；候选认知等你确认 | `references/status-review.md` |
| 「整理我的历史投资资料」 | 把多年的旧日志、复盘、感悟做成索引和阶段梳理，不改原文 | `references/history-onboarding.md` |

只读对应的那一份。

## 三层，加一层底

```text
原始想法（Raw）   随手说，原话按顺序存，不美化
   │  整理
   ▼
Insight           事实 / 解释 / 假设 / 情绪拆开；假设写清怎么验证
   │  每周回看
   ▼
状态机 STATUS     我现在在哪、最近在纠结什么、这阶段要提防自己什么
─────────────────────────────────────────────
长期记忆 MEMORY   三个月后还成立的才写这里；每次开始前先读
```

旁边还有一条线：**动作记录**。想法记的是「我今天在想什么」，动作记录记的是「我今天真的做了什么」。想法很容易美化自己，动作不会，两边对着看，很多「我以为我是这么做的」会露馅。

## 它和其他模块怎么接

- **和回看**：`yms-review` 的持有期复盘、三红旗、单笔归因是机器记的账；你看完账单的想法、为什么当时特别想买，记在这里。复盘结论想长期记住，走这里的「沉淀」。
- **和规则**：这里的东西都**不具备门禁效力**。一条假设反复被验证、想变成约束你的规则，走 `yms-review` 的规则变更，写进 `01_我的投资框架/长期规则.md`。
- **和主控**：`yms-autopilot` 的主控心跳每天会读这里上次以来的新增和改动，把新想法拆成研究任务。

## 开工前（六个动作共用）

1. 先认文件夹：根目录有 `总入口暗号.md` 的是 YMOS，说明书换成根目录的 `YMSKILL_ADAPTER.md`（没有就用 `yms-setup` 建文件夹里内置的 YMOS 映射；策略档案按映射找不到时，照内置映射里的兜底再找一遍，适配页是旧版的也照做），下面各步的路径一律按映射换，按本节末尾「在 YMOS 文件夹里」办，不当成没初始化。其他文件夹读说明书（`AGENTS.md` / `CLAUDE.md`）和「路径映射」，找到 BrainStorm 的位置（默认 `06_BrainStorm/`）。映射里写了子目录的（比如 YMOS 的原始想法在 `BrainStorm/每日头脑风暴/Raw_Thoughts/`），下面各个动作里的路径一律换成映射里的。
2. 第一次用、`MEMORY.md` 和 `STATUS.md` 还不存在：按 `templates/` 建出来，再开始。
3. 没有投资文件夹：问我是建完整的投资文件夹（`yms-setup`），还是只建一个 BrainStorm 先用起来。只建 BrainStorm 的，在我指定的位置建 `BrainStorm/`，结构和下面一样。

```text
06_BrainStorm/
├── MEMORY.md                       长期记忆
├── STATUS.md                       状态机
├── 原始想法/YYYY-MM/YYYY-MM-DD.md   原话
├── 动作记录/YYYY-MM/YYYY-MM-DD.md   今天真的做了什么
├── Insight/YYYY-MM/YYYY-MM-DD_<主题>.md
├── 感悟归档/短期灵感/  长期框架/  执行清单/
├── 回看/YYYY-MM-DD_周回看.md  YYYY-MM_月度总结.md
├── 状态快照/YYYY-MM-DD.md            状态机改版前的留底
└── 历史资料/原始资料/  资料索引.md  梳理/
```

**在 YMOS 文件夹里**（根目录有 `总入口暗号.md`）：记下来、整理、沉淀交给 YMOS 的「开始今天的头脑风暴」「整理一下今天说的」，历史资料入职交给「整理我的历史投资资料」；动作记录和每周回看照常做，写到 `BrainStorm/动作记录/`、`BrainStorm/回看/`，状态机改版前的快照放 `BrainStorm/状态机/快照/`（以根目录 `YMSKILL_ADAPTER.md` 为准；没有这个文件就按 `yms-setup` 建文件夹里的 YMOS 映射）。

## 这个模块的规矩

- **原话不美化**。按说话顺序存，只改明显的语音识别错字并用〔〕标出。
- **主线是用户的原话**。整理出来的 Insight 按他说话的顺序展开；AI 的看法只放在文末「附注」，标明是 AI 的。
- **写进 MEMORY、升级成框架或清单之前，先给他看，他说「确认」才写**。没人看着的时候（定时任务里）只写候选，不写正文。
- **不自动变规则**。这里的任何东西要约束交易，都走规则变更。
- **不用盈亏替代过程**。复盘问的是当时怎么想、怎么做，不是赚没赚。
- 原话里的金额照记（文件在用户本地）；整理成 Insight 时换成百分比。不给买卖建议；原话里说「明天想买 X」，记下来，提醒一句真要买走 `yms-gate`。
