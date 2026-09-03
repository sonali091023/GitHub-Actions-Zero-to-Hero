# Flask Application — Docker & GitHub Actions CI/CD

A Flask application containerized using Docker and deployed automatically using GitHub Actions, Docker Hub, and a self-hosted runner.

## Technology Stack

* Python
* Flask
* Gunicorn
* Docker
* Docker Compose
* Docker Hub
* GitHub Actions
* Self-hosted GitHub Actions Runner

---

# 1. Project Architecture

```text
                       Developer
                           |
                           | Push Code / Run Workflow
                           v
                    GitHub Repository
                           |
                           v
                 Docker Build & Push
                 GitHub Actions Workflow
                           |
                           | docker build
                           v
                      Docker Image
                           |
                           | docker push
                           v
                       Docker Hub
                           |
                           | workflow_run
                           v
                    Deploy Flask App
                 GitHub Actions Workflow
                           |
                           v
                   Self-hosted Runner
                           |
                           | docker pull
                           v
                  Docker Hub Image
                           |
                           | docker stop
                           | docker rm
                           | docker run
                           v
                    Flask Container
                           |
                           | Port 80
                           v
                    Flask Application
```

---

# 2. Project Structure

```text
GitHub-Actions-Zero-to-Hero/
│
├── .github/
│   └── workflows/
│       ├── docker-build-push.yml
│       └── deploy-app.yml
│
├── templates/
│   └── index.html
│
├── app.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env
```

---

# 3. Flask Application

### `app.py`

```python
from flask import Flask, jsonify, render_template

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({
        "status": "UP"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
```

The application provides:

```text
/         → Flask web page
/health   → Health-check endpoint
```

The health endpoint returns:

```json
{
    "status": "UP"
}
```

---

# 4. Dockerfile

```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 80

CMD ["gunicorn", "--bind", "0.0.0.0:80", "app:app"]
```

### Port configuration

Gunicorn listens on:

```text
Container Port: 80
```

Therefore Docker must expose:

```text
80
```

---

# 5. Requirements

### `requirements.txt`

```text
Flask==3.1.3
gunicorn==23.0.0
```

Development/testing tools such as `pytest`, `flake8`, and `bandit` can be installed separately during CI.

---

# 6. Docker Compose

### `docker-compose.yml`

```yaml
services:
  web:
    image: ${DOCKERHUB_USERNAME}/flask-app:v1
    ports:
      - "80:80"
```

The port mapping means:

```text
Host Port 80
     |
     v
Container Port 80
     |
     v
Gunicorn
     |
     v
Flask
```

---

# 7. Docker Hub Username

Docker Compose uses:

```text
DOCKERHUB_USERNAME
```

For local execution, you can set it in PowerShell:

```powershell
$env:DOCKERHUB_USERNAME="sonali0910"
```

Verify:

```powershell
echo $env:DOCKERHUB_USERNAME
```

Or create a `.env` file:

```text
DOCKERHUB_USERNAME=sonali0910
```

Do not store Docker Hub passwords or tokens in `.env`.

---

# 8. Local Docker Execution

## Step 1 — Set Docker Hub Username

```powershell
$env:DOCKERHUB_USERNAME="sonali0910"
```

## Step 2 — Verify Configuration

```powershell
docker compose config
```

The image should resolve to:

```text
sonali0910/flask-app:v1
```

## Step 3 — Start Application

```powershell
docker compose up -d
```

## Step 4 — Verify Container

```powershell
docker ps
```

Expected:

```text
sonali0910/flask-app:v1
0.0.0.0:80->80/tcp
```

## Step 5 — Check Logs

```powershell
docker logs <container-id>
```

Expected Gunicorn output:

```text
Starting gunicorn 23.0.0
Listening at: http://0.0.0.0:80
Using worker: sync
Booting worker
```

## Step 6 — Test Application

Open:

```text
http://localhost
```

Health check:

```text
http://localhost/health
```

---

# 9. GitHub Actions — Build & Push Workflow

### `.github/workflows/docker-build-push.yml`

```yaml
name: Docker Build & Push

on:
  workflow_dispatch:

jobs:
  build-and-push:
    env:
      DOCKERHUB_USERNAME: ${{ vars.DOCKERHUB_USERNAME }}

    runs-on: self-hosted

    steps:

      - name: Code Checkout
        uses: actions/checkout@v4

      - name: Login to Docker Hub
        uses: docker/login-action@v4
        with:
          username: ${{ vars.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build & Push to Docker Hub
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: |
            ${{ vars.DOCKERHUB_USERNAME }}/flask-app:${{ github.ref_name }}
            ${{ vars.DOCKERHUB_USERNAME }}/flask-app:v1
            ${{ vars.DOCKERHUB_USERNAME }}/flask-app:${{ github.sha }}
```

---

# 10. GitHub Repository Configuration

The workflow requires:

## Repository Variable

```text
DOCKERHUB_USERNAME
```

Example:

```text
sonali0910
```

## Repository Secret

```text
DOCKERHUB_TOKEN
```

The token is used to authenticate with Docker Hub.

---

# 11. Build & Push Execution

The workflow is manually triggered using:

```yaml
on:
  workflow_dispatch:
```

Execution:

```text
GitHub
   |
   v
Actions
   |
   v
Docker Build & Push
   |
   +--> Checkout Code
   |
   +--> Login to Docker Hub
   |
   +--> Setup Buildx
   |
   +--> Build Docker Image
   |
   +--> Push Image
   |
   v
Docker Hub
```

Three image tags are created:

```text
sonali0910/flask-app:<branch>
sonali0910/flask-app:v1
sonali0910/flask-app:<commit-sha>
```

For example:

```text
sonali0910/flask-app:main
sonali0910/flask-app:v1
sonali0910/flask-app:abc123...
```

---

# 12. Automatic Deployment Workflow

### `.github/workflows/deploy-app.yml`

```yaml
name: Deploy Flask App

on:
  workflow_run:
    workflows: ["Docker Build & Push"]
    types:
      - completed

jobs:
  deploy:

    if: ${{ github.event.workflow_run.conclusion == 'success' }}

    env:
      DOCKERHUB_USERNAME: ${{ vars.DOCKERHUB_USERNAME }}

    runs-on: self-hosted

    steps:

      - name: Checkout code
        uses: actions/checkout@v4

      - name: Login to Docker Hub
        uses: docker/login-action@v4
        with:
          username: ${{ vars.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Pull latest image
        run: |
          docker pull $DOCKERHUB_USERNAME/flask-app:v1

      - name: Stop old container
        run: |
          docker stop flask-app || true
          docker rm flask-app || true

      - name: Run new container
        run: |
          docker run -d \
            --name flask-app \
            -p 80:80 \
            $DOCKERHUB_USERNAME/flask-app:v1

      - name: Verify deployment
        run: |
          docker ps
          docker logs --tail 20 flask-app
```

---

# 13. How Automatic Deployment Works

The important part is:

```yaml
on:
  workflow_run:
    workflows: ["Docker Build & Push"]
    types:
      - completed
```

This means:

> Run the deployment workflow after the `Docker Build & Push` workflow completes.

However, we don't want deployment to happen when the build fails.

Therefore:

```yaml
if: ${{ github.event.workflow_run.conclusion == 'success' }}
```

means:

```text
Build succeeded?
      |
   YES ─────→ Deploy
      |
    NO
      |
   Do not deploy
```

---

# 14. Complete CI/CD Execution

The complete pipeline is:

```text
             Developer
                 |
                 v
          GitHub Repository
                 |
                 v
      ┌─────────────────────┐
      │ Docker Build & Push │
      └─────────────────────┘
                 |
                 v
          Checkout Code
                 |
                 v
          Docker Login
                 |
                 v
           Docker Build
                 |
                 v
          Docker Image
                 |
                 v
           Docker Hub
                 |
                 |
                 v
      ┌─────────────────────┐
      │   Deploy Flask App  │
      └─────────────────────┘
                 |
                 v
         Self-hosted Runner
                 |
                 v
          Docker Login
                 |
                 v
          docker pull
                 |
                 v
       Stop Existing Container
                 |
                 v
        Remove Old Container
                 |
                 v
         docker run -d
                 |
                 v
       Flask Container :80
                 |
                 v
          Flask Application
```

---

# 15. Important Difference: Docker Compose vs Automatic Deployment

There are two ways this project can run the container.

### Local deployment

You are using Docker Compose:

```bash
docker compose up -d
```

with:

```yaml
ports:
  - "80:80"
```

### Automatic CI/CD deployment

Your `deploy-app.yml` does **not use Docker Compose**.

It directly runs:

```bash
docker run -d \
  --name flask-app \
  -p 80:80 \
  $DOCKERHUB_USERNAME/flask-app:v1
```

Therefore:

```text
Local:
Docker Compose
     ↓
Container


CI/CD:
GitHub Actions
     ↓
docker pull
     ↓
docker stop
     ↓
docker rm
     ↓
docker run
     ↓
Container
```

Both approaches use the same Docker image.

---

# 16. Self-hosted Runner

The deployment workflow uses:

```yaml
runs-on: self-hosted
```

Therefore a self-hosted GitHub Actions runner must be installed and running on the machine where the deployment should happen.

For example:

```text
GitHub
   |
   v
Self-hosted Runner
   |
   v
Docker Engine
   |
   v
Flask Container
```

The runner must have Docker installed and permission to execute Docker commands.

Verify:

```bash
docker --version
```

and:

```bash
docker ps
```

---

# 17. Deployment Verification

After the deployment workflow finishes, verify:

```bash
docker ps
```

You should see:

```text
flask-app
```

with:

```text
0.0.0.0:80->80/tcp
```

Check logs:

```bash
docker logs --tail 20 flask-app
```

Expected:

```text
Starting gunicorn
Listening at: http://0.0.0.0:80
Booting worker
```

---

# 18. Test the Application

On the EC2 instance:

```bash
curl http://localhost
```

Health check:

```bash
curl http://localhost/health
```

Expected:

```json
{
  "status": "UP"
}
```

From your browser:

```text
http://<EC2-PUBLIC-IP>
```

Make sure the EC2 Security Group allows inbound TCP traffic on port `80`.

---

# 19. Important Port Mapping

The project consistently uses port `80`.

```text
Flask
  ↓
Gunicorn :80
  ↓
Container :80
  ↓
Host/EC2 :80
```

Docker Compose:

```yaml
ports:
  - "80:80"
```

Automatic deployment:

```bash
docker run -d -p 80:80 ...
```

Therefore both local and EC2 deployments expose:

```text
Port 80
```

---

# 20. Troubleshooting

## `DOCKERHUB_USERNAME variable is not set`

For local Compose:

```powershell
$env:DOCKERHUB_USERNAME="sonali0910"
```

Or use `.env`.

---

## `invalid reference format`

Run:

```bash
docker compose config
```

If you see:

```text
/flask-app:v1
```

the username variable is missing.

It should be:

```text
sonali0910/flask-app:v1
```

---

## Container does not start

Check:

```bash
docker ps -a
```

Then:

```bash
docker logs flask-app
```

---

## Image is updated in Docker Hub but old container is running

Pushing a new image does not modify an already-running container.

You must recreate the container:

```bash
docker pull sonali0910/flask-app:v1
docker stop flask-app
docker rm flask-app
docker run -d --name flask-app -p 80:80 sonali0910/flask-app:v1
```

Your `deploy-app.yml` performs these operations automatically.

---

# 21. Final CI/CD Concept

This project demonstrates the difference between **CI** and **CD**.

### Continuous Integration

```text
Code
 ↓
GitHub Actions
 ↓
Docker Build
 ↓
Docker Image
 ↓
Docker Hub
```

### Continuous Deployment

```text
Docker Hub
 ↓
Self-hosted Runner
 ↓
docker pull
 ↓
Stop Old Container
 ↓
Remove Old Container
 ↓
Run New Container
 ↓
Application Updated
```

### Complete Pipeline

```text
              CI                         CD

Developer
   |
   v
GitHub
   |
   v
Build & Push
   |
   v
Docker Hub
   |
   v
Deploy Workflow
   |
   v
Self-hosted Runner
   |
   v
Docker Container
   |
   v
Flask Application
```

---

# 22. Execution Checklist

## First-time setup

* [ ] Create Flask application
* [ ] Create `templates/index.html`
* [ ] Create `requirements.txt`
* [ ] Create `Dockerfile`
* [ ] Create `docker-compose.yml`
* [ ] Create Docker Hub repository
* [ ] Create Docker Hub access token
* [ ] Add `DOCKERHUB_USERNAME` GitHub variable
* [ ] Add `DOCKERHUB_TOKEN` GitHub secret
* [ ] Configure self-hosted GitHub Actions runner
* [ ] Ensure Docker is installed on runner machine
* [ ] Ensure runner can execute Docker commands

## Local testing

```powershell
$env:DOCKERHUB_USERNAME="sonali0910"

docker compose config

docker compose up -d

docker ps

docker logs <container-id>
```

Test:

```text
http://localhost
```

and:

```text
http://localhost/health
```

## CI/CD execution

1. Go to GitHub → **Actions**
2. Select **Docker Build & Push**
3. Click **Run workflow**
4. Wait for Docker image build
5. Verify image on Docker Hub
6. `Deploy Flask App` starts automatically
7. Deployment workflow pulls `flask-app:v1`
8. Old `flask-app` container is stopped
9. Old container is removed
10. New container is created
11. Deployment logs are displayed
12. Verify the application on EC2

---

# 23. Expected Final Result

After successful execution:

```text
GitHub
   |
   | Build
   v
Docker Image
   |
   | Push
   v
Docker Hub
   |
   | Pull
   v
Self-hosted EC2
   |
   v
flask-app container
   |
   | :80
   v
Flask Application
```

The application should be accessible through:

```text
http://<EC2-PUBLIC-IP>
```

and the health endpoint:

```text
http://<EC2-PUBLIC-IP>/health
```

Expected response:

```json
{
  "status": "UP"
}
```
