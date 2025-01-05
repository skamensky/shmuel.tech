I want to use k8s for my project.

Here are the constraints and requirements:
- Limit processing so it doesn't get expensive. Ideally run off of one node with multiple pods.
- Mono repo with the following aspects:
    - infrastructure as code for:
        * the cluster definition in terraform
        * DNS
        * vpc
    - cluster yaml files defining each service
    - a folder for each service's application code and dockerfile
    - github action for building and pushing images to GAR using buildx (support for personal cache)
- We should use our VPC for as much as possible
- Each service should have its own subdomain. 
- Services should define resources.requests and resources.limits 
- We should use GKE
- We should use argocd for each service
- I want auto scaling to be off by default, so someone doesn't DDS my wallet. But i want to be able to turn it on in case I get posted to a news site like hacker news or reddit.
- monitoring to get an email when a service goes down or traffic spikes
- TLD is `shmuel.tech`. We need to organize SSL termination,k8's ingress, google cloud dns such that argocd can define subdomains per application (and we won't have to change terraform files to add subdomains)
Examples of services:

- generic redis to support other services
- generic postgres to support other services (should use persistent volume claims to persist DB). make recommendations here about how to handle.
- web application for my website/blog powered by golang and some vanilla JS
- media tracking application written from scratch in react and using supabase
    * has an admin interface for me which will be authenticated using simple user password
    * frontend shows things like music I like, podcasts I've listened to, books I've read, tv and movies I've watched


Terraform config is retrieved from a json file for reuse instead of a vars file.

e.g.

```
{
    "backend":{
        "project_id": "shmuel-tech",
        "tf_bucket_name": "shmuel",
        "tf_region": "me-west1"
    },
    "cluster":{
        ...
    },
    ...
}
```

And in terraform: `config = jsondecode(file("${path.module}/config.json"))`

Suggested file layout:
repo-root/
│
├── terraform/                  # Infrastructure as Code
│   ├── backend.tf
│   ├── config.json
│   ├── dns.tf
│   ├── gke.tf
│   ├── locals.tf
│   ├── network.tf
│   ├── output.tf
│   └── service_accounts.tf
│
├── argocd/                     # ArgoCD GitOps files
│   ├── base/                   # Shared configurations managed by ArgoCD
│   │   ├── ingress.yaml        # Common ingress for all services
│   │   ├── namespace.yaml      # Namespace setup
│   │   └── secrets.yaml        # Shared secrets (use SealedSecrets)
│   ├── applications/           # Separate folder per service
│   │   ├── echo-server/
│   │   │   ├── application.yaml
│   │   │   ├── deployment.yaml
│   │   │   └── service.yaml
│   │   ├── redis/
│   │   │   ├── application.yaml
│   │   │   ├── deployment.yaml
│   │   │   └── service.yaml
│   │   ├── postgres/
│   │   │   ├── application.yaml
│   │   │   ├── statefulset.yaml
│   │   │   └── service.yaml
│   │   ├── blog/
│   │   │   ├── application.yaml
│   │   │   ├── deployment.yaml
│   │   │   └── service.yaml
│   │   └── media-tracking/
│   │       ├── application.yaml
│   │       ├── deployment.yaml
│   │       ├── service.yaml
│   │       └── ingress.yaml
│   ├── project.yaml            # Optional: ArgoCD project definition
│   └── README.md               # ArgoCD setup guide
│
├── services/                   # Microservices' application code
│   ├── redis/                  # Redis service
│   │   ├── Dockerfile
│   │   └── src/
│   ├── postgres/               # Postgres service
│   │   ├── Dockerfile
│   │   └── src/
│   ├── blog/                   # Web application (Golang)
│   │   ├── Dockerfile
│   │   └── src/
│   └── media-tracking/         # Media tracking application
│       ├── Dockerfile
│       ├── frontend/
│       │   ├── package.json
│       │   └── src/
│       └── backend/
│           ├── package.json
│           └── src/
│
├── .github/                    # GitHub-specific configurations
│   ├── workflows/
│   │   ├── build-and-push.yml
│   │   └── deploy.yml
│
├── docs/                       # Documentation
│   ├── README.md
│   └── argocd.md
│
└── scripts/                    # Helper scripts
    ├── build-images.sh
    ├── deploy.sh
    └── cleanup.sh


The files I have so far are:



For now, please generate the files for argocd and echo-server (use ealen/echo-server) 


Output the file in usual markdown format. NOT in the <FILE></FILE> format. The <FILE> format is for input ONLY. Files should be separated (not a single file with comments demarcating which file the content belongs to). Do not use chat-canvas mode.
Feel free to add other suggested files servicing the argocd functionality I'm trying to accomplish BUT NOTHING ELSE. The rest of the files above are just for reference to give you context and will be created later.