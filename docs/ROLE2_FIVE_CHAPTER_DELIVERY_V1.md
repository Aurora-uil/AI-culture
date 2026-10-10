# 2号成员五章交付包 V1.0（核心玩法·视觉·通用前端）

> 对应《分工方案V1.1》§2.2 / §5.2。队员一剧情已冻结，本包只做玩法层与视觉层，不改剧情分支与结局判定。

## 一、新增文件（玩法层，供1号剧情节点接入）

| 文件 | 对应任务 | 接口 |
|---|---|---|
| `components/game/GameplayState.vue` | 共用加载/空/错误/离线/重试壳 | `state, title, note + @retry` |
| `chapters/han/HanPackRecord.vue` | H-U02/U03/U04 行囊·路线·见闻卡 | `play-complete {pack,route,records}` / `play-fail` / `play-exit` |
| `chapters/wei/WeiCompareScale.vue` | W-U02 对照尺（延续/变化/并存/未知） | `play-complete {judgments}` |
| `chapters/wei/WeiDraftPreview.vue` | W-U03 营造推演样稿（标推演非复原） | `play-complete {elements}` |
| `chapters/tang/TangRosterCaption.vue` | T-U03/U04 名册校对+120字展签 | `play-complete {roster,caption}`，越界词拦截 |
| `chapters/qing/QingResourceRecord.vue` | Q-U02/U03/U04 资源+多来源记录册 | `play-complete {resources,records,kept}`，冲突不自动合并 |
| `chapters/contemporary/ContemporaryAuthStudio.vue` | C-U01~U05 观察/权利/授权/共创/作品卡 | 权利不足阻断生成，作品卡固定“AI辅助·非原作” |

已有探索组件（HanRouteMap / WeiEvidenceCompare / TangScrollViewer / QingMigrationMap / QiangKnowledgeWorkbench）本次补齐390×844单列布局与44px触屏点击区，未改史实红线逻辑。

## 二、每章验收对照

- 汉：2次路线判断+1次物资取舍+记录卡保留“不确定”；亲见/转述/推测图例常驻。
- 北魏：对照尺四类+样稿每项来源层级；双屏红线“非前后替代”保留。
- 唐：文成公主永不在画中；名册≥1处纠正；展签四要素+120字+越界拦截。
- 清：2组冲突并列+2次资源取舍；走廊/范围表达不确定；不生成精确人数。
- 当代：非生成式针法观察；权利不清不可生成；生成前后溯源；作品卡固定声明。

## 三、共用规范

- 设计令牌/章节色沿用 `styles/tokens.css`，未复制全局CSS；命名 `chapter-scene-subject-version.ext`。
- 状态：正常/加载/空/错误/离线/重试齐备；断网不阻断主线（GameplayState offline）。
- 可访问性：焦点可见、替代文本、减少动画`prefers-reduced-motion`、色盲不只靠颜色（权利卡文字+图标）。
- 资产：沿用`public/assets/<chapter>/`，真实文物保留来源与版权标签（SceneViewer source-label）；AI示意标“非史实照片/非原作复制”。

## 四、1号接入方式（示例）

```vue
<HanPackRecord @play-complete="onPlayDone" @play-fail="onPlayFail" @play-exit="backToStory" />
```

## 五、可用性记录（内部3人试玩）

| 问题 | 严重度 | 处理 |
|---|---|---|
| 行囊上限不明 | P1 | 加“最多3样”与失败原因回传 |
| 对照尺来源看不见 | P1 | 每项可展开来源说明 |
| 展签越界只判对错 | P1 | 改为越界词提示+修改建议 |
| 移动端双屏挤压 | P1 | ≤900px改单列，false横向溢出 |
| 生成按钮可绕过授权 | P0 | 未满足条件disabled+title说明 |

状态：REVIEW，可进联调。
