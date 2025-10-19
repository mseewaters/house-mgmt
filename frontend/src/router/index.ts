import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../components/HomePage.vue')
    },
    {
      path: '/clock',
      name: 'clock',
      component: () => import('../components/ClockView.vue')
    }
  ]
})

export default router