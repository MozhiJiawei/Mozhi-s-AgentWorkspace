import skillSidebar from "./generated/skill-sidebar.json";

export default {
  lang: "zh-CN",
  title: "Mozhi 的 Agent 工作区",
  description: "Agent 工作区与已注册 skill 的在线文档。",
  cleanUrls: true,
  ignoreDeadLinks: [
    (link: string) =>
      /\.(html|htm|pptx)$/.test(link) ||
      /^\/skill-static\/.+\.(html|htm|pptx)$/.test(link) ||
      /\/source_understanding_review$/.test(link) ||
      /\/prototype(?:-[a-z-]+)?$/.test(link)
  ],
  themeConfig: {
    nav: [
      { text: "工作区", link: "/workspace/" },
      { text: "Skills", link: "/skills/" },
      { text: "运维", link: "/operations/" },
      { text: "参考", link: "/reference/" }
    ],
    sidebar: [
      {
        text: "工作区",
        items: [
          { text: "概览", link: "/workspace/" },
          { text: "快速开始", link: "/workspace/getting-started" },
          { text: "核心概念", link: "/workspace/concepts" },
          {
            text: "文档架构需求",
            link: "/documentation-architecture-requirements"
          }
        ]
      },
      {
        text: "Skills",
        items: skillSidebar
      },
      {
        text: "运维",
        items: [
          { text: "运维索引", link: "/operations/" },
          { text: "文档服务器", link: "/operations/docs-server" },
          { text: "文档发布", link: "/operations/release-docs" },
          { text: "Submodules", link: "/operations/submodules" },
          { text: "Pre-Commit Gates", link: "/operations/pre-commit-gates" },
          { text: "Docker 部署", link: "/deployment-docker" }
        ]
      },
      {
        text: "参考",
        items: [
          { text: "参考索引", link: "/reference/" },
          { text: "主仓协议", link: "/reference/main-repo-protocol" },
          { text: "Skill 子仓协议", link: "/reference/skill-repo-protocol" },
          { text: "Skill 资料规范", link: "/reference/skill-material-standards" },
          { text: "文档 Manifest", link: "/reference/skill-docs-manifest" }
        ]
      }
    ],
    search: {
      provider: "local"
    },
    outline: {
      level: [2, 3],
      label: "On this page"
    }
  }
};
