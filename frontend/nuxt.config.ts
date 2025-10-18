// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['@nuxtjs/tailwindcss'],

  // Import Tailwind CSS globally
  css: ['~/assets/css/tailwind.css'],

  devServer: {
    port: 50004,
    host: 'localhost'
  },

  app: {
    head: {
      title: 'Media Center',
      link: [
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,1,0'
        },
        {
          rel: 'icon',
          type: 'image/svg+xml',
          href: '/favicon.png'
        }
      ]
    }
  },

  compatibilityDate: '2025-03-10'
});