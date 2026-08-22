import DefaultTheme from 'vitepress/theme'
import { h } from 'vue'
import 'katex/dist/katex.min.css'
import HighlightLayer from './HighlightLayer.vue'
import TermHover from './TermHover.vue'
import KnowledgeGraph from './KnowledgeGraph.vue'
import ExamPage from './exam/ExamPage.vue'

export default {
  extends: DefaultTheme,
  Layout() {
    return h(DefaultTheme.Layout, null, {
      'layout-top': () => [h(HighlightLayer), h(TermHover)],
    })
  },
  enhanceApp({ app }) {
    app.component('KnowledgeGraph', KnowledgeGraph)
    app.component('ExamPage', ExamPage)
  },
}
