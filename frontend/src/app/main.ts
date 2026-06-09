import App from './App.vue'
import router from './router'
import '../styles/index.css'

export function mountApp() {
  return { App, router }
}
