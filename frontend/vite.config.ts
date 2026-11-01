import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import topLevelAwait from 'vite-plugin-top-level-await'

// https://vite.dev/config/
export default defineConfig({
  // Слушаем IPv4 и IPv6: иначе Vite занимает только ::1, и браузер,
  // который открывает localhost через 127.0.0.1, получает отказ соединения.
  server: {
    host: true,
    port: 5173,
    strictPort: true,
  },
  plugins: [
    vue({
      template: {
        compilerOptions: {
          isCustomElement: (tag) => tag === 'math-field',
        },
      },
    }),
    topLevelAwait(),
  ],
  assetsInclude: ['**/*.wasm'],
  optimizeDeps: {
    exclude: ['@myriaddreamin/typst-ts-web-compiler', '@myriaddreamin/typst-ts-renderer'],
  },
  test: {
    environment: 'jsdom',
    globals: true,
  },
})
