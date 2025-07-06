# 🚀 shmuel.tech - Personal Project Platform

My personal infrastructure for sharing projects, writing, and media through a unified microservices platform with automatic deployment and DNS management.

## 🎯 What This Is

A sophisticated personal platform that makes it effortless to deploy and share any project I work on. Whether it's a new app, my writing, media files, or experiments - everything gets its own subdomain and deploys automatically.

## ✨ Key Features

### 🏗️ **Universal Service Support**
- **Any Docker Project**: If it runs in Docker, it can be deployed here
- **Local Services**: Projects that live in this monorepo (like Go apps, static sites)
- **Remote Services**: My other GitHub repositories deployed directly to subdomains
- **Unified Interface**: Make commands provide consistent build/deploy experience across all types

### 🌐 **Automatic Everything**
- **DNS Management**: New services automatically get `{service}.shmuel.tech` domains
- **SSL Certificates**: HTTPS works immediately for all services
- **Deployment**: Single command deploys everything or specific services
- **DNS Proxy**: Custom solution to work around Namecheap's IP restrictions

### 🧠 **Smart Operations**
- **Change Detection**: CI only deploys services that actually changed
- **Parallel Deployment**: Multiple services deploy simultaneously
- **Health Monitoring**: Built-in health checks for all services
- **Secret Management**: Environment variables sync across services

## 🌟 What Makes This Special

### **Hybrid Architecture**
I can deploy both projects that live in this repo and projects from my other GitHub repositories. This means I can:
- Keep complex projects in their own repositories
- Still deploy them seamlessly to my personal domain
- Maintain a unified deployment pipeline for everything

### **DNS Proxy Innovation**
Namecheap requires whitelisted IP addresses for their API, but cloud deployments have dynamic IPs. I built a custom DNS proxy service that provides a stable IP address and handles all DNS operations automatically.

### **One-Command Sharing**
From idea to live subdomain in one command. Whether it's a new blog post, a media gallery, or an experimental app - everything gets deployed the same way.

## 🎪 Live Examples

- **Main Site**: Personal homepage and portfolio
- **Media Service**: Photo and file sharing
- **Various Projects**: Each gets its own subdomain automatically

## 🔧 What I Can Do

### **Project Management**
- Create new services instantly with full scaffolding
- Deploy any of my GitHub repositories as services
- Remove services cleanly with automatic cleanup

### **Deployment**
- Deploy everything with one command
- Deploy only specific services that changed
- Parallel deployment for speed

### **Infrastructure**
- Automatic DNS and SSL for new services
- Health monitoring across all services
- Unified development environment with Docker Compose

## 🏆 Why This Matters

This platform lets me focus on building rather than infrastructure. Every project I work on can be shared immediately with a clean URL, automatic HTTPS, and professional deployment - whether it's a quick experiment or a major application.

The hybrid approach means I can keep projects in separate repositories when they're complex enough to warrant it, but still deploy them seamlessly through this unified system.

---

*Built for effortless project sharing - from local development to live subdomain in one command.* 