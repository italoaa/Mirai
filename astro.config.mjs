// @ts-check
import { defineConfig } from 'astro/config';

// https://astro.build/config
export default defineConfig({
  site: "https://mirai.ml",
  markdown: {
  shikiConfig: {
    theme: "css-variables",
    wrap: false,
    },
  },
});
