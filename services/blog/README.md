# Hugo Blog Service

A static blog built with Hugo and the beautifulhugo theme, designed to be deployed via Docker.
 
## Features

- **Hugo Static Site Generator**: Fast and flexible static site generation
- **Beautiful Hugo Theme**: Professional and responsive design
- **Full Search Integration**: JSON-based search functionality
- **Tags & Categories**: Automatic taxonomy support
- **Image Optimization**: Hugo Pipes for responsive images
- **Markdown Support**: Full Markdown with syntax highlighting
- **RSS & SEO**: Built-in RSS feeds and SEO optimization
- **Docker Build**: Multi-stage Docker build for production deployment

## Project Structure

```
services/blog/
├── config.toml              # Hugo configuration
├── content/
│   ├── about.md            # About page
│   └── post/
│       └── hello-world/    # Example post (page bundle)
│           └── index.md
├── themes/
│   └── beautifulhugo/      # Theme (git submodule)
├── layouts/
│   ├── _default/
│   │   └── index.json      # Search JSON output
│   └── shortcodes/
│       └── resize.html     # Image optimization shortcode
├── archetypes/
│   └── default.md          # Post template
├── static/                 # Static assets
├── Dockerfile              # Multi-stage build
├── Makefile               # Service commands
└── fly.toml               # Deployment configuration
```

## Usage

### Development

```bash
# Start Hugo development server
make -C services/blog serve

# or use the alias
make -C services/blog dev
```

Visit `http://localhost:1313` to view the blog.

### Creating Posts

```bash
# From project root
make new-post TITLE="My New Post"

# Or from blog directory
make new-post TITLE="My New Post"
```

This creates a new post using the page bundle format at `content/post/my-new-post/index.md`.

### Adding Images

Place images in the same directory as your post's `index.md` file, then use the resize shortcode:

```markdown
{{< resize "my-image.jpg" "Image description" >}}
```

### Building

```bash
# Test build
make -C services/blog test

# Docker build
make -C services/blog build
# or from project root
make build-blog
```

### Deployment

```bash
# Deploy to Fly.io
make -C services/blog deploy
```

## Configuration

### Hugo Configuration (config.toml)

- **Theme**: beautifulhugo
- **Search**: Enabled with JSON output
- **Taxonomies**: Tags and categories
- **Output Formats**: HTML, RSS, JSON
- **Syntax Highlighting**: GitHub style with line numbers
- **SEO**: Enabled with OpenGraph and Twitter cards

### Content Guidelines

#### Post Front Matter

```yaml
---
title: "Your Post Title"
date: 2025-01-01T00:00:00Z
description: "Brief description for SEO"
tags: ["tag1", "tag2"]
draft: false
---
```

#### Page Bundles

Use page bundles for posts with images:

```
content/post/my-post/
├── index.md
├── feature-image.jpg
└── diagram.png
```

## Search Integration

The blog includes full-text search functionality:

- Search index: `/index.json`
- Includes title, description, URL, and tags
- Automatically generated for all posts

## Theme Features

The beautifulhugo theme includes:

- Responsive design
- Social media integration
- Disqus comments support
- Google Analytics integration
- Syntax highlighting
- Table of contents
- Share buttons

## Docker Build

The Dockerfile uses a multi-stage build:

1. **Build Stage**: Uses `klakegg/hugo:0.124.1-ext-alpine` to build the site
2. **Serve Stage**: Uses `nginx:alpine` to serve static files

## Commands Reference

### Main Makefile Commands

- `make new-post TITLE="Post Title"` - Create new blog post
- `make build-blog` - Build blog Docker image

### Blog Service Commands

- `make serve` - Start Hugo development server
- `make dev` - Alias for serve
- `make test` - Test Hugo build
- `make build` - Build Docker image
- `make run` - Run Docker container locally
- `make clean` - Clean build artifacts
- `make new-post TITLE="Title"` - Create new post
- `make deploy` - Deploy to Fly.io

## URLs

- **Local Development**: `http://localhost:1313`
- **Production**: `https://blog.shmuel.tech`
- **Local Docker**: `http://localhost:3000`

## Notes

- Posts are created as drafts by default
- Use `draft: false` in front matter to publish
- Images are automatically optimized using Hugo Pipes
- RSS feed available at `/index.xml`
- Search index available at `/index.json`
