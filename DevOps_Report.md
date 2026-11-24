# DevOps Automation Report — ACEest Fitness

**Project repository:** [2025tm93233/devops-assignment-2](https://github.com/2025tm93233/devops-assignment-2)  
**Report date:** 25 November 2026

## 1. Project and CI/CD architecture

ACEest Fitness is a Python desktop application built with Tkinter. It manages fitness-club information using SQLite and includes workout, charting, and PDF-report functionality. The repository combines automated checks and container/deployment configuration across GitHub Actions, Jenkins, Docker, and Kubernetes.

The current delivery path has two related but distinct workflows:

1. **GitHub Actions — continuous integration and image build.** A push starts the workflow in `.github/workflows/ci.yml` on an Ubuntu runner. It checks out the source, installs `python3-tk`, discovers and runs the Python `unittest` suite, then builds a Docker image tagged with both the commit SHA and `latest`. This provides a repeatable test-and-build check for repository changes. The workflow does not publish the image to a registry or deploy it.
2. **Jenkins — test, build, and deployment.** The `Jenkinsfile` defines test and Docker-build stages, followed by a deployment stage. It selects shell commands on Unix agents and batch commands on Windows agents. Deployment applies `kubernetes.yaml`, waits for the `aceest-fitness` rollout, and attempts `kubectl rollout undo` if rollout verification fails.
3. **Docker — packaged runtime.** The Dockerfile starts from Debian Bookworm slim and installs Python, Tkinter, Matplotlib, Xvfb, and supporting packages. It installs `fpdf2` in a virtual environment and launches the application under `xvfb-run`, enabling the GUI application to start in a display-less container environment.
4. **Kubernetes — desired deployment configuration.** The manifest requests two replicas and configures rolling updates, resource requests and limits, and process-based liveness and readiness probes. A NodePort service is also declared.

In the intended Jenkins path, a successful test stage permits the image build, which is followed by Kubernetes deployment and rollout verification. If verification fails, the pipeline requests rollback and reports the deployment as failed. GitHub Actions separately validates code and builds an image on pushes; it is not shown as a trigger for Jenkins.

## 2. Challenges and mitigation strategies

**GUI dependencies in automated environments.** The application uses Tkinter and Matplotlib, while CI runners and containers commonly have no graphical display. The GitHub Actions workflow installs `python3-tk`. The Docker image includes Xvfb and launches the app through `xvfb-run`, providing a virtual display. The tests focus on application/database logic and isolate optional GUI/reporting modules so those checks do not require a live desktop session.

**Consistent execution across Jenkins agents.** Jenkins may run on either Unix or Windows. The pipeline explicitly selects `sh` or `bat` for its test, Docker, and Kubernetes commands. This improves portability, although the actual agent still needs compatible Python, Docker, and `kubectl` installations and access to a configured Kubernetes cluster.

**Deployment failure and recovery.** Applying a Kubernetes manifest does not prove that the new release becomes healthy. The Jenkins pipeline waits for rollout status with a timeout and attempts a rollback if verification throws an error. The manifest also limits unavailable pods during rolling updates and defines process probes. These measures add a deployment gate and a recovery attempt; they do not replace application-level health checks or validation of a restored release.

**Image availability and tag consistency.** The two CI paths build images with different tags: GitHub Actions uses the commit SHA and `latest`, while Jenkins uses the Jenkins build number and `latest`. The Kubernetes manifest requests `aceest-fitness:latest` with `imagePullPolicy: Never`, which requires the image to already exist in the runtime’s local image store. No image registry push or node image-distribution step is configured in these files. Deployment therefore depends on the Jenkins build and Kubernetes nodes sharing or receiving the matching image. A registry-based publish-and-pull flow, with an immutable tag passed into the deployment, would make this handoff more reliable.

**Application and Kubernetes service model.** The Docker command starts a Tkinter desktop GUI, but the Kubernetes manifest also declares container port 8080 and a NodePort service. The application code does not establish an HTTP service on that port, and its probes only check whether the process name exists. As a result, these Kubernetes settings do not demonstrate that users can access the application through the service or that the GUI is usable in a cluster. The deployment target should be clarified: retain a containerized desktop app for an appropriate interactive environment, or add a supported headless/web interface before treating this as a network service.

## 3. Key automation outcomes

- Pushes to the GitHub repository trigger automated unit-test discovery and a Docker image build.
- The test suite covers database initialization and selected client, workout-program, membership, and login logic.
- Docker packages the Python runtime and the graphical/reporting dependencies needed by the application.
- Jenkins provides a defined path from testing to image building and Kubernetes rollout, including a bounded rollout wait and rollback attempt.
- Kubernetes configuration specifies two application replicas, rolling-update behavior, resource bounds, probes, and a NodePort service.
- **Local verification for this report:** `python -m unittest discover -s . -p 'test_*.py' -v` completed successfully: **8 tests passed**. This verifies the test suite in the local project environment; it is not evidence that a remote GitHub Actions run or a live Jenkins/Kubernetes deployment was executed.

The repository therefore demonstrates meaningful CI automation and supplies deployment building blocks. Before claiming a complete, repeatable CD release, the image publication/distribution mechanism, Jenkins trigger and credentials/cluster setup, and the GUI-versus-service deployment model should be resolved and exercised in the target environment.
