import { createApp } from 'vue'

import { mountApp } from './app/main'

const { App, router } = mountApp()

createApp(App).use(router).mount('#app')
