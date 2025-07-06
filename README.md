# 🚀 shmuel.tech - Smart Microservices Platform

A sophisticated infrastructure-as-code solution for managing multiple microservices with automatic deployment, DNS management, and intelligent CI/CD workflows.

## � What This Is

**shmuel.tech** is a production-ready monorepo platform that makes deploying and managing multiple microservices as easy as running a single command. It's designed for developers who want enterprise-grade infrastructure automation without the complexity.

## ✨ Key Capabilities

### 🏗️ **Instant Service Creation**
- **Go Services**: Scaffolds complete Go microservices with web interfaces, health checks, and tests
- **Remote Services**: Deploy external GitHub repositories directly into your infrastructure
- **Static Sites**: Deploy static websites with nginx and custom configuration
- **Mixed Architecture**: Run different types of services side-by-side seamlessly

### 🌐 **Automatic DNS & SSL Management**
- **Zero-Touch DNS**: Automatically manages DNS records across all your services
- **SSL Certificates**: Handles certificate provisioning and renewal automatically
- **Custom Domains**: Maps services to clean URLs (e.g., `media.shmuel.tech`, `api.shmuel.tech`)
- **DNS Proxy Innovation**: Clever workaround for Namecheap's IP whitelisting requirements

### 🚀 **Lightning-Fast Deployment**
- **Parallel Deployment**: Deploys multiple services simultaneously for maximum speed
- **Smart CI/CD**: Only deploys services that have actually changed
- **Bulk Operations**: Manage secrets, DNS, and deployments across all services at once
- **Multi-Environment**: Supports both production and sandbox environments

### 🧠 **Intelligent Automation**
- **Change Detection**: Automatically identifies which services need updates
- **Dependency Management**: Handles service dependencies and configuration
- **Health Monitoring**: Built-in health checks and monitoring for all services
- **Secret Management**: Secure environment variable and secret synchronization

## 🌟 What Makes This Special

### **1. Hybrid Service Architecture**
Unlike traditional monorepos, this platform supports both local services (written in Go) and remote services (pulling from external GitHub repositories). This means you can:
- Deploy your own microservices alongside external tools
- Include third-party applications in your infrastructure
- Maintain a unified deployment pipeline for mixed architectures

### **2. DNS Proxy Innovation**
Namecheap's API requires whitelisted IP addresses, which is problematic for dynamic cloud deployments. This platform includes a custom DNS proxy service that:
- Provides a stable, whitelisted IP address
- Handles all DNS operations through a secure proxy
- Enables fully automated DNS management despite API restrictions

### **3. Intelligent CI/CD**
The GitHub Actions workflow doesn't just deploy everything blindly. Instead, it:
- Analyzes git changes to determine which services are affected
- Only deploys services that have actually changed
- Performs bulk DNS updates before parallel deployments
- Handles failures gracefully without breaking other services

### **4. One-Command Everything**
From a single command, you can:
- Create a new service with full scaffolding
- Deploy all services with automatic DNS and SSL
- Update only changed services
- Manage secrets across your entire infrastructure

### **5. Production-Ready from Day One**
Every generated service includes:
- Beautiful web interfaces with modern styling
- Health check endpoints for monitoring
- Proper error handling and logging
- Docker containerization
- Makefile automation
- Test frameworks

## 🎪 Live Examples

The platform currently powers several live services:

- **Main Site**: Static website served from the root domain
- **Media Service**: File handling and media processing
- **DNS Proxy**: The ingenious workaround for Namecheap API limitations
- **External Apps**: Third-party tools deployed from GitHub repositories

## 🔧 What You Can Do

### **Service Management**
- Create new Go microservices in seconds
- Deploy external GitHub repositories as services
- Remove services cleanly with automatic cleanup
- List and monitor all your services

### **Deployment Operations**
- Deploy all services with one command
- Deploy only specific services
- Run deployments in parallel for speed
- Deploy in detached mode for CI/CD

### **DNS & Infrastructure**
- Automatic DNS record management
- SSL certificate provisioning
- Custom domain mapping
- Multi-environment support

### **Development Workflow**
- Local development with Docker Compose
- Unified testing across all services
- Secret management and synchronization
- Change detection and smart deployments

## 🏆 Why This Matters

This platform demonstrates how modern infrastructure should work:
- **Automation First**: Everything is automated, from service creation to deployment
- **Developer Experience**: One command to create, deploy, and manage services
- **Production Ready**: Built-in monitoring, health checks, and error handling
- **Scalable**: Add services without increasing operational complexity
- **Innovative**: Creative solutions to real-world problems (like the DNS proxy)

## 🎯 Perfect For

- **Solo Developers**: Manage multiple services without DevOps overhead
- **Small Teams**: Standardized infrastructure without platform engineering
- **Side Projects**: Production-ready deployment for personal projects
- **Prototyping**: Quickly deploy and iterate on microservice architectures
- **Learning**: Study modern infrastructure patterns and automation

---

*Ready to deploy your next microservice? The entire platform is designed around making that as simple as a single command.* 