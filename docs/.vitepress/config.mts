import { defineConfig } from 'vitepress'

export default defineConfig({
  title: '智能体应用开发实践赛 · 知识手册',
  description: '基于操作系统 AI+ 理论模拟练习备考知识手册',
  lang: 'zh-CN',
  cleanUrls: true,

  themeConfig: {
    nav: [
      { text: '总览', link: '/' },
      { text: '知识网络图', link: '/graph' },
      { text: '第 1 章', link: '/ch01_ai_foundation' },
      { text: '第 2 章', link: '/ch02_os_linux' },
      { text: '第 3 章', link: '/ch03_software' },
      { text: '第 4 章', link: '/ch04_agent' },
      { text: '第 5 章', link: '/ch05_hardware' },
      { text: '第 6 章', link: '/ch06_appendix' },
      { text: '第 7 章', link: '/ch07_mcp_agent_practice' },
    ],

    sidebar: [
      {
        text: '导航',
        items: [
          { text: '总览', link: '/' },
          { text: '知识网络图', link: '/graph' },
        ],
      },
      {
        text: '知识手册',
        items: [
          { text: '第 1 章 人工智能基础理论', link: '/ch01_ai_foundation' },
          { text: '第 2 章 国产操作系统技术基础', link: '/ch02_os_linux' },
          { text: '第 3 章 国产软件技术基础', link: '/ch03_software' },
          { text: '第 4 章 智能体技术基础', link: '/ch04_agent' },
          { text: '第 5 章 国产硬件技术基础', link: '/ch05_hardware' },
          { text: '第 6 章 附录', link: '/ch06_appendix' },
          { text: '第 7 章 MCP 与 Agent 落地实践', link: '/ch07_mcp_agent_practice' },
        ],
      },
    ],

    search: {
      provider: 'local',
    },

    outline: {
      level: [2, 3],
      label: '本页目录',
    },

    docFooter: {
      prev: '上一页',
      next: '下一页',
    },

    darkModeSwitchLabel: '深色模式',
    sidebarMenuLabel: '目录',
    returnToTopLabel: '返回顶部',
    lastUpdatedText: '最后更新',
  },

  vite: {
    optimizeDeps: {
      include: ['echarts/core'],
    },
  },
})
