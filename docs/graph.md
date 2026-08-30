<script setup>
import KnowledgeGraph from './.vitepress/theme/KnowledgeGraph.vue'
</script>

# 知识网络图

探索式知识图谱：

- **搜索**：顶部输入关键词，按名称/描述定位并高亮匹配知识点
- **点击节点**：聚焦该知识点及其一跳关联（高亮邻域、弱化其它），右侧面板显示详情与关联列表
- **点关联项**：跳转到对应知识点继续探索；点空白或"重置视图"恢复全图
- **图例**：切换各模块显隐；节点可拖拽、滚轮缩放

<KnowledgeGraph />
