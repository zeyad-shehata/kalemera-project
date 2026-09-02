import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  hasValidBackEntry,
  resolveBackTarget,
  resolveAuthPageRedirect,
} from '../src/utils/navigation.ts'

test('back returns to the actual previous route when history has an entry', () => {
  assert.equal(hasValidBackEntry({ back: '/checkout' }), true)
  assert.equal(resolveBackTarget({ back: '/checkout' }), '/checkout')
})

test('back preserves query parameters of the previous route', () => {
  assert.equal(resolveBackTarget({ back: '/product/12?lang=en' }), '/product/12?lang=en')
})

test('back falls back to Home only when history is unavailable', () => {
  // No history state at all
  assert.equal(hasValidBackEntry(null), false)
  assert.equal(resolveBackTarget(null), null)
  // Empty/unknown state object
  assert.equal(hasValidBackEntry({}), false)
  assert.equal(resolveBackTarget({}), null)
  // back explicitly null / empty
  assert.equal(hasValidBackEntry({ back: null }), false)
  assert.equal(resolveBackTarget({ back: null }), null)
  assert.equal(hasValidBackEntry({ back: '' }), false)
  // External (non in-app) URL is never treated as a valid back target
  assert.equal(hasValidBackEntry({ back: 'https://example.com' }), false)
  assert.equal(hasValidBackEntry({ back: 'mailto:test@x.com' }), false)
})

test('auth-page redirect preserves the previous in-app route', () => {
  // Stale /login entry while the user is actually on /checkout
  assert.equal(resolveAuthPageRedirect('/checkout', '/login'), '/checkout')
  // Query string from the source route is preserved
  assert.equal(resolveAuthPageRedirect('/cart?tab=full', '/login'), '/cart?tab=full')
})

test('auth-page redirect falls back to Home only without a real source', () => {
  // Direct entry / first load (source is Home)
  assert.equal(resolveAuthPageRedirect('/', '/login'), null)
  // Same page (should never redirect onto itself)
  assert.equal(resolveAuthPageRedirect('/login', '/login'), null)
  // Empty source
  assert.equal(resolveAuthPageRedirect('', '/login'), null)
})