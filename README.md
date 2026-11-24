# ACEest Fitness

ACEest Fitness is a Python desktop application for fitness-club management. It uses Tkinter for its interface and SQLite for local data storage, with functionality for client and workout management, charts, and PDF reports.

## Repository contents

| File | Purpose |
|---|---|
| `Aceestver.py` | Application entry point and application logic |
| `test_Aceestver.py` | Unit tests for database and selected application logic |
| `Dockerfile` | Container image definition for running the application with a virtual display |
| `Jenkinsfile` | Jenkins pipeline for tests, image build, and Kubernetes deployment |
| `kubernetes.yaml` | Kubernetes Deployment and NodePort Service definitions |
| `.github/workflows/ci.yml` | GitHub Actions workflow for tests and Docker image build |
| `DevOps_Report.md` | Report on the project CI/CD architecture and automation |

## Requirements

- Python 3
- Tkinter (on Debian/Ubuntu, install the `python3-tk` package)
- Docker for container builds
- Jenkins with Python, Docker, and `kubectl` available on its agent to run the full pipeline
- A Kubernetes cluster configured for the Jenkins agent for deployment

The application also uses Matplotlib and `fpdf2`; the Dockerfile installs the runtime dependencies. The container runs the GUI through Xvfb because containers generally do not have a physical display.

## Run locally

From the repository root:

```powershell
python Aceestver.py
```

On Windows, install a Python distribution that includes Tkinter. On a headless Linux machine, run the application with a virtual display (for example, `xvfb-run -a python3 Aceestver.py`) after installing the application dependencies.

## Run tests

Run the unit tests from the repository root:

```powershell
python -m unittest discover -s . -p "test_*.py" -v
```

The tests cover database initialization and selected client, workout-program, membership, and login behavior. GUI and report-rendering dependencies are isolated where they are not required for these logic tests.

## Build and run the Docker image

Build the image:

```powershell
docker build -t aceest-fitness:latest .
```

Run the GUI application in the container:

```powershell
docker run --rm aceest-fitness:latest
```

The container starts the application with `xvfb-run`. This provides a virtual display for GUI initialization; it does not by itself provide remote browser access to the desktop.

## CI/CD

### GitHub Actions

The workflow in `.github/workflows/ci.yml` runs on pushes. It checks out the source, installs `python3-tk`, runs the unit tests, and builds Docker images tagged with the commit SHA and `latest`. It does not publish images to a registry or deploy to Kubernetes.

### Jenkins and Kubernetes

The `Jenkinsfile` runs unit tests, builds an image tagged with the Jenkins build number and `latest`, applies `kubernetes.yaml`, and waits for the deployment rollout. If rollout verification fails, the pipeline attempts to roll back to the prior deployment revision.

Before deploying, configure a Jenkins agent with Python, Docker, and `kubectl`, plus access to the target cluster. The Kubernetes manifest uses `imagePullPolicy: Never`, so the image must already be available to the cluster nodes (for example, by loading it into a local cluster); this repository does not configure registry publication or image distribution.

The application is a Tkinter desktop GUI, not an HTTP server. Although the Kubernetes manifest declares port 8080 and a NodePort service, the application does not serve HTTP on that port. The service should not be treated as a working web interface without adding an appropriate server or changing the deployment model.

## Repository

[2025tm93233/devops-assignment-2](https://github.com/2025tm93233/devops-assignment-2)
