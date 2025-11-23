# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a **DevOps Training in Operations (TIO)** repository from the PGP in Cloud Computing program. It contains hands-on exercises demonstrating DevOps practices on AWS, focusing on containerized application deployment using Docker, ECS Fargate, and supporting AWS services.

The exercises build a complete CI/CD workflow for a Java web application (HelloWorld) deployed as a Docker container.

## Training Structure

The repository contains materials for progressive DevOps exercises:

- **TIO 1 (DevOps 101)**: Environment setup, building artifacts, local containerization
- **TIO 2 (DevOps 102)**: Container registry, ECS cluster deployment with load balancing
- **TIO 3a (DevOps 103)**: Mutable deployment (in-place updates)
- **TIO 3b (DevOps 103)**: Immutable deployment (blue-green style)
- **Additional TIO**: CodeCommit integration for source control

## Architecture Overview

### Complete Deployment Pipeline

1. **DevOps Instance (EC2)**: Development environment where code is built and tested
2. **Script Repository (S3)**: Stores installation and build scripts
3. **Container Registry (ECR)**: Private Docker image repository
4. **Container Orchestration (ECS Fargate)**: Serverless container deployment
5. **Load Balancing (ALB)**: Application Load Balancer for traffic distribution
6. **Source Control (CodeCommit)**: Git repository for application code

### Key AWS Services Used

- **EC2**: Amazon Linux 2 t2.micro instance for build environment
- **S3**: Script storage and distribution
- **ECR**: Private Docker image registry
- **ECS**: Container orchestration (Fargate launch type)
- **ALB**: Application Load Balancer
- **IAM**: LabInstanceProfile (EC2 role), LabRole (ECS task role)
- **CodeCommit**: Git-based source repository

## Application Stack

- **Application**: HelloWorld Java web application
- **Build Tool**: Apache Maven 3.9.4
- **Runtime**: Java OpenJDK 11
- **Web Server**: Apache Tomcat (tomcat:jre11 Docker image)
- **Artifact**: WAR (Web Application Archive) file
- **Container**: Docker

## Common Commands

### Initial Environment Setup (TIO 1)

**Run on fresh EC2 instance:**
```bash
bash installscript.sh
```

This installs:
- Java OpenJDK 11
- Apache Maven 3.9.4
- Sets up Maven environment variables
- Downloads HelloWorld source code from GitHub
- Compiles code and builds WAR file

Expected location after install: `/opt/HelloWorld/target/HelloWorld-1.war`

### Build and Deploy Container Locally

```bash
bash buildscript.sh
```

This script:
1. Creates `/opt/docker` directory
2. Copies WAR file to working directory
3. Generates Dockerfile with Tomcat base image
4. Builds Docker image tagged as `helloworld:v1`
5. Runs container on port 80 (maps to Tomcat's 8080)
6. Displays public IP URL for accessing the application

**Note**: The script uses lowercase `dockerfile` (not `Dockerfile`)

### Docker Commands

```bash
# View Docker images
sudo docker images

# View running containers
sudo docker ps

# View all containers (including stopped)
sudo docker ps -a

# Stop container (use first 3 characters of container ID)
sudo docker stop <container_id>

# Build specific version
sudo docker build -f dockerfile -t helloworld:v2 /opt/docker

# Run on specific port
sudo docker run -d -p 80:8080 helloworld:v1
```

### ECR Operations

```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region us-east-1 | sudo docker login --username AWS --password-stdin <account_id>.dkr.ecr.us-east-1.amazonaws.com

# Tag image for ECR
sudo docker tag helloworld:v1 <ecr_repository_uri>:v1

# Push to ECR
sudo docker push <ecr_repository_uri>:v1
```

### Maven Commands

```bash
# Verify Maven installation
mvn -version

# Build WAR file
cd /opt/HelloWorld
mvn package

# Output: /opt/HelloWorld/target/HelloWorld-1.war
```

### Application Version Updates

To update the application version (for TIO 3 exercises):

```bash
# Navigate to source
cd /opt/HelloWorld/src/main/webapp

# Edit version in JSP file
nano index.jsp
# Change version (v1 → v2 → v3) at bottom of file
# Ctrl+S to save, Ctrl+X to exit

# Rebuild
cd /opt/HelloWorld
rm -f target/HelloWorld-1.war
mvn package

# Copy to Docker build directory
cd /opt/docker
rm -f HelloWorld.war
cp /opt/HelloWorld/target/HelloWorld-1.war HelloWorld.war

# Build and test new version
sudo docker build -f dockerfile -t helloworld:v2 .
sudo docker run -d -p 80:8080 helloworld:v2
```

### CodeCommit Setup (Additional TIO)

```bash
# Install prerequisites
sudo yum install python3-pip git -y
pip3 install git-remote-codecommit

# Configure Git
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
git config --global init.defaultBranch main

# Clone repository using git-remote-codecommit
git clone codecommit::us-east-1://DevOps_Codebase

# Add and commit changes
cd DevOps_Codebase
git add .
git commit -m "Added Codebase"
git push -f origin master
```

## Important Notes

### Security Considerations

- **SSH Keys**: Repository contains `devOps_kp.pem` and `devOps_pk.ppk` - these should NOT be committed to version control
- **IAM Roles**: Scripts rely on EC2 having LabInstanceProfile role attached for S3/ECR access
- **Port 80**: Must be open in EC2 security group for HTTP access
- **Region**: All exercises use `us-east-1` (N.Virginia)

### Prerequisites for Exercises

1. **AWS Lab Environment**: Exercises designed for AWS Academy or similar lab environment with pre-configured IAM roles
2. **Docker Installation**: Not included in `installscript.sh` - must be installed separately:
   ```bash
   sudo amazon-linux-extras install docker -y
   sudo service docker start
   ```
3. **Application Source**: HelloWorld app downloaded from `https://github.com/pbharadwaj1608/helloworld/raw/main/HelloWorld.zip`

### Deployment Models

**Mutable Deployment (TIO 3a)**:
- Update existing task definition (create new revision)
- Update existing service to use new revision
- In-place replacement of containers
- Faster, but brief downtime possible

**Immutable Deployment (TIO 3b)**:
- Create completely new task definition and service
- Deploy new infrastructure alongside old
- Switch traffic to new deployment
- Blue-green deployment style, zero-downtime

### ECS Configuration Naming Conventions

From the exercises:
- Cluster: `devopscluster`
- Task Definition: `devopstask` (TIO 2) or `taskversion3` (TIO 3b)
- Service: `devopsservice` (TIO 2) or `serviceversion3` (TIO 3b)
- Container: `devopsimage` (TIO 2) or `version3` (TIO 3b)
- Load Balancer: `devopslb`
- Target Group: `devopstg`
- Container Port: `8080` (Tomcat)

### S3 Bucket Naming

Format: `glmmddhhmm` where:
- `gl` = prefix (Great Learning)
- `mmddhhmm` = Month, Day, Hour, Minute (e.g., `pgpcc12251538` for Dec 25, 15:38)

### Script Behavior Notes

- `installscript.sh` uses `set -e` to exit on any error
- `buildscript.sh` appends lines to dockerfile using `>>` operator
- Dockerfile removes default Tomcat webapps and deploys HelloWorld as ROOT application
- Scripts expect specific directory structure in `/opt`

## Training Progression

1. **TIO 1**: Build and test locally on EC2 instance
2. **TIO 2**: Push to ECR and deploy to ECS with load balancing
3. **TIO 3a**: Update to v2 using mutable deployment
4. **TIO 3b**: Update to v3 using immutable deployment
5. **Additional**: Integrate with CodeCommit for source control

Each TIO builds on the previous one - resources from earlier TIOs may be reused in later exercises.
