import DefaultTheme from 'vitepress/theme'
import { h } from 'vue'
import 'katex/dist/katex.min.css'
import HighlightLayer from './HighlightLayer.vue'
import TermHover from './TermHover.vue'
import KnowledgeGraph from './KnowledgeGraph.vue'
import Mermaid from './Mermaid.vue'
import SectionGraph from './SectionGraph.vue'
import Flux from './Flux.vue'
import Compare from './Compare.vue'
import Pillars from './Pillars.vue'
import Layer from './Layer.vue'
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
    app.component('Mermaid', Mermaid)
    app.component('SectionGraph', SectionGraph)
    app.component('Flux', Flux)
    app.component('Compare', Compare)
    app.component('Pillars', Pillars)
    app.component('Layer', Layer)
    app.component('ExamPage', ExamPage)
  },
}
