import { glob } from "astro/loaders";
import { defineCollection } from "astro:content";
import { z } from "astro/zod";

const entrySchema = z.object({
  title: z.string(),
  description: z.string(),
  pubDate: z.coerce.date(),
  draft: z.boolean().default(false),
  featured: z.boolean().default(false),
});

const blog = defineCollection({
  loader: glob({
    pattern: "**/*.md",
    base: "./src/content/blog",
  }),
  schema: entrySchema,
});

const photos = defineCollection({
  loader: glob({
    pattern: "**/*.md",
    base: "./src/content/photos",
  }),
  schema: entrySchema.extend({
    image: z.string().optional(),
  }),
});

const ceramics = defineCollection({
  loader: glob({
    pattern: "**/*.md",
    base: "./src/content/ceramics",
  }),
  schema: entrySchema.extend({
    image: z.string().optional(),
  }),
});

export const collections = {
  blog,
  photos,
  ceramics,
};
