# 智能体应用开发实践赛 · 知识手册学习站

基于 VitePress 的本地学习站点，包含备考知识手册、知识网络图与文档高亮功能。

## 环境要求

- Node.js 18 及以上（开发必需）
- 可选：Python 3（用于离线静态服务，构建产物可直接 `python -m http.server` 托管）

## 快速开始

```bash
# 1. 安装依赖
npm install

# 2. 启动本地预览（自动同步知识库内容） 要在对应文件夹下执行 
npm run dev
# 浏览器打开 http://localhost:5173 

# 3. 构建静态站点
npm run build
# 产物在 docs/.vitepress/dist/，可整体部署或分享
```

## 功能说明

### 文档高亮

- 用鼠标选中正文文本，点击出现的"高亮"按钮，选中的文字被黄色标记
- 标记保存在浏览器本地（localStorage），刷新后保留，每个浏览器各自独立
- 点击已标记的文字可删除该条高亮
- 页面右上角有"清除本页高亮"按钮
- 侧边栏、导航栏等区域的文字不会被高亮

### 知识网络图

- 入口在顶部导航"知识网络图"
- 节点按模块着色：AI 理论、智能体、操作系统、软件、硬件
- 点击图例可隐藏或显示对应模块的节点
- 节点可拖拽，滚轮缩放
- 点击节点弹出详情卡片，包含知识点摘要和"查看详情"链接，跳转到手册对应章节
- 边的标签表示知识点之间的关系类型

### 其他

- 右上角搜索框支持全站本地搜索
- 右上角月亮图标切换深色模式
- 每页右侧有本页目录大纲

## 目录结构

```
LearningSite/
├── package.json              # 项目配置与脚本
├── copy-docs.mjs             # 同步脚本：从 ../KnowledgeBase 复制手册章节
├── docs/
│   ├── index.md              # 首页
│   ├── graph.md              # 知识网络图页面
│   ├── ch01~ch07.md          # 手册章节（由脚本自动同步，勿直接编辑）
│   ├── public/
│   │   └── graph-data.json   # 图谱数据（节点、关系、章节锚点）
│   └── .vitepress/
│       ├── config.mts        # 站点配置：导航、侧边栏、搜索
│       ├── dist/             # 构建产物
│       └── theme/
│           ├── index.js          # 主题入口，注册组件
│           ├── HighlightLayer.vue    # 高亮功能组件
│           └── KnowledgeGraph.vue    # 知识网络图组件
└── README.md
```

## 更新内容

手册内容维护在 `../KnowledgeBase/` 目录下的 md 文件中，`npm run dev` 和 `npm run build` 会自动执行 `copy-docs.mjs` 同步到站点。

新增章节步骤：

1. 在 `KnowledgeBase/` 下新建 `chNN_xxx.md`
2. 编辑 `copy-docs.mjs`，把文件名加入 `files` 列表
3. 编辑 `.vitepress/config.mts`，在 `nav` 和 `sidebar` 中加入链接

## 常见问题

| 问题 | 处理 |
|---|---|
| 安装依赖慢 | 使用国内 npm 镜像：`npm config set registry https://registry.npmmirror.com` |
| 端口被占用 | `npm run dev -- --port 5174` |
| 高亮不生效 | 确认选中文字在正文区域；清除浏览器缓存后重试 |
| 图谱空白 | 按 F12 查看控制台，确认 graph-data.json 可访问 |
