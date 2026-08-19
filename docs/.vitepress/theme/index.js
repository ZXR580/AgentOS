import DefaultTheme from 'vitepress/theme'
import { h } from 'vue'
import HighlightLayer from './HighlightLayer.vue'
import KnowledgeGraph from './KnowledgeGraph.vue'

export default {
  extends: DefaultTheme,
  Layout() {
    return h(DefaultTheme.Layout, null, {
      'layout-top': () => h(HighlightLayer),
    })
  },
  enhanceApp({ app }) {
    app.component('KnowledgeGraph', KnowledgeGraph)
  },
}
