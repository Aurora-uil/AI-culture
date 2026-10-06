# 删除元代固定剧情弹窗：设计说明

## 背景

`C02Scene.vue` 静态引用了不存在的 `@/components/dialogue/YuanFixedDialogue.vue`，导致 Vite 在转换阶段报错。元代当前正式入口已经跳转到 `/chapter/yuan/story`，由 `YuanStoryExperience.vue` 提供完整的十二幕剧情，因此通用场景页中的“固定剧情对话”弹窗属于未完成且重复的旧入口。

## 决策

从 `C02Scene.vue` 中完整移除固定剧情弹窗，而不是创建占位组件或仅隐藏按钮。

删除范围：

- `YuanFixedDialogue.vue` 的异步导入与失败占位逻辑；
- `dialogueOpen` 状态；
- `startFixedDialogue` 和 `onDialogueDone` 处理函数；
- 工具栏中的“固定剧情对话”按钮；
- 固定剧情弹窗模板。

保留范围：

- 元代十二幕剧情 `/chapter/yuan/story`；
- `YuanRubbingCompare.vue` 与“拓片比对”按钮；
- 通用场景页中的六体文字透镜、AI 对话、关系图谱和场景状态；
- 现有事件类型与未被当前页面使用的任务状态机，避免扩大本次修复范围。

## 数据与行为

删除后，进入元代正式流程仍由 `C00Intro.vue` 和 `C01Guide.vue` 跳转到 `/chapter/yuan/story`。通用 `C02Scene.vue` 不再加载缺失组件，也不再显示重复入口。其他章节行为不变。

## 错误处理

不再依赖对动态导入调用 `.catch()`。Vite 会在运行时之前解析静态可见的导入路径，因此缺失模块不能通过 Promise 回退可靠处理；删除无效导入可从根源消除错误。

## 验证

1. 先保留一个能够复现原始 Vite 导入失败的自动化检查，确认修改前为红。
2. 修改后运行同一检查，确认 `C02Scene.vue` 可被 Vite 转换。
3. 运行 `npm run typecheck`。
4. 运行 `npm run build`。
5. 搜索 `YuanFixedDialogue` 和固定剧情弹窗状态，确认没有残留引用。

## 非目标

- 不新增或重写元代剧情内容；
- 不调整十二幕剧情的交互与视觉；
- 不重构元代任务状态机；
- 不修改拓片比对流程。
