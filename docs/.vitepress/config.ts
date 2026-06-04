import skillSidebar from "./generated/skill-sidebar.json";

export default {
  lang: "zh-CN",
  title: "Mozhi 的 Agent 工作区",
  description: "Agent 工作区与已注册 skill 的在线文档。",
  cleanUrls: true,
  themeConfig: {
    nav: [
      { text: "工作区", link: "/workspace/" },
      { text: "Skills", link: "/skills/" },
      { text: "参考", link: "/reference/" }
    ],
    sidebar: [
      {
        text: "工作区",
        items: [
          { text: "概览", link: "/workspace/" },
          { text: "快速开始", link: "/workspace/getting-started" },
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
        text: "参考",
        items: [
          { text: "参考索引", link: "/reference/" },
          { text: "主仓协议", link: "/reference/main-repo-protocol" },
          { text: "Skill 子仓协议", link: "/reference/skill-repo-protocol" },
          { text: "文档 Manifest", link: "/reference/skill-docs-manifest" },
          { text: "Docker 部署", link: "/deployment-docker" }
        ]
      }
    ],
    search: {
      provider: "local"
    }
  }
};
