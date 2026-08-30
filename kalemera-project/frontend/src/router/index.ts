import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue'),
  },
  {
    path: '/product/:id',
    name: 'ProductDetail',
    component: () => import('../views/ProductDetail.vue'),
  },
  {
    path: '/cart',
    name: 'Cart',
    component: () => import('../views/Cart.vue'),
  },
  {
    path: '/checkout',
    name: 'Checkout',
    component: () => import('../views/Checkout.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/orders',
    name: 'MyOrders',
    component: () => import('../views/MyOrders.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
  },
  {
    path: '/admin',
    component: () => import('../views/admin/AdminLayout.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: '',
        name: 'AdminDashboard',
        component: () => import('../views/admin/AdminDashboard.vue'),
      },
      {
        path: 'products',
        name: 'AdminProducts',
        component: () => import('../views/admin/AdminProducts.vue'),
      },
      {
        path: 'categories',
        name: 'AdminCategories',
        component: () => import('../views/admin/AdminCategories.vue'),
      },
      {
        path: 'reports',
        name: 'AdminReports',
        component: () => import('../views/admin/AdminReports.vue'),
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()

  // Initialize session on first load if not done
  if (!authStore.initialized) {
    await authStore.fetchCurrentUser()
  }

  const isAuthenticated = authStore.isAuthenticated
  const isAdmin = authStore.isAdmin

  if (to.meta.requiresAdmin) {
    if (isAuthenticated && isAdmin) {
      next()
    } else if (isAuthenticated) {
      next('/')
    } else {
      next({ path: '/login', query: { redirect: to.fullPath } })
    }
  } else if (to.meta.requiresAuth) {
    if (isAuthenticated) {
      next()
    } else {
      next({ path: '/login', query: { redirect: to.fullPath } })
    }
  } else {
    // Redirect already authenticated users away from auth pages
    if (isAuthenticated && (to.path === '/login' || to.path === '/register')) {
      next('/')
    } else {
      next()
    }
  }
})

export default router
