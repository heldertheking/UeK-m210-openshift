# GitHub Openshift Deployment Tutorial

This repository is a tutorial on how to deploy a simple web application to OpenShift using GitHub Actions.

## Prerequisites

- GitHub account
- OpenShift account (with access to a project/namespace)
- GitHub Actions enabled on your repository
- Basic knowledge of Git, GitHub, and OpenShift
- Basic knowledge of Docker
- **Docker installed locally** (for manual testing)
- **OpenShift CLI (`oc`) installed locally** (for troubleshooting)

> **Tip:** If you are new to OpenShift, ask your administrator for the correct project/namespace and permissions.

## Steps of Deployment (Overview)

1. Code Checkout
2. Login to GHCR (GitHub Container Registry)
3. Build and Push Docker Image
4. Replace placeholders in deployment.yaml, service.yaml, and route.yaml
5. Install, Login, and Deploy to OpenShift

---

## Explanation of GitHub Action

The [Action file](./.github/workflows/deploy.yml) is a `.yaml` file and consists of different parts.

### 1. Conditional Deployment

In the file, the `on` keyword defines when the action should run.

```yaml
on:
  push:
    tags:
      - 'v*.*.*'
    branches:
      - main
```

This section tells GitHub that the deployment only occurs when a tag is pushed or when the `main` branch is updated.

> **Common Pitfall:** If you push to a different branch or use a tag format not matching `v*.*.*`, the workflow will not trigger.

### 2. Permissions

```yaml
permissions:
  contents: read
  packages: write
```

This permits the workflow to read the repository and push images to the GitHub Container Registry (GHCR).

**Important:** Make sure the repository has write permissions on the package itself (if using existing packages).

`https://github.com/users/<YOUR_GITHUB_USERNAME>/packages/container/<PACKAGE_NAME>/settings`

> **Tip:** If you get `denied: permission_denied` errors when pushing images, check your repository and package permissions.

### 3. Jobs and Steps

The last part of the file defines the jobs and steps that should be executed.

```yaml
jobs:
  build-and-deploy:
    # Tells GitHub to use an Ubuntu runner
    runs-on: ubuntu-latest
    env:
      # Defines the name of the image. The package name is always the repository name.
      IMAGE_NAME: ghcr.io/${{ github.repository_owner }}/${{ github.repository }}:${{ github.ref_name }}
      # Defines the tag of the image
      IMAGE_TAG: ${{ github.ref_name }}
```

> **Note:** The image name in GHCR will always use your repository name. If you want to use a custom image name, you must manually edit the workflow file to change the IMAGE_NAME variable.

#### Steps of the Job

This is the last section of the file and is part of the `jobs:` section.

```yaml
    steps:
      # Checkout the code
      - name: Checkout code
        uses: actions/checkout@v4

      # Login to GitHub Container Registry
      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      # Build and push Docker image
      - name: Build Docker image
        run: |
          docker build -t $IMAGE_NAME .

      - name: Push Docker image
        run: |
          docker push $IMAGE_NAME

      # Replace placeholders in deployment.yaml
      - name: Replace image tag in deployment.yaml
        run: |
          sed -i 's|{{IMAGE_TAG}}|${{ github.ref_name }}|g' deployment.yaml
          sed -i 's|{{IMAGE_OWNER}}|${{ github.repository_owner }}|g' deployment.yaml
          sed -i 's|{{REPOSITORY}}|${{ github.repository }}|g' deployment.yaml
          sed -i 's|{{OPENSHIFT_APP_NAME}}|${{ secrets.OPENSHIFT_APP_NAME }}|g' deployment.yaml
          sed -i 's|{{OPENSHIFT_APP_NAME}}|${{ secrets.OPENSHIFT_APP_NAME }}|g' service.yaml
          sed -i 's|{{OPENSHIFT_APP_NAME}}|${{ secrets.OPENSHIFT_APP_NAME }}|g' route.yaml
          
      - name: Install OpenShift CLI
        run: |
          curl -sL https://mirror.openshift.com/pub/openshift-v4/clients/oc/latest/linux/oc.tar.gz -o oc.tar.gz
          tar -xzf oc.tar.gz
          sudo mv oc /usr/local/bin/

      # Login to OpenShift
      - name: Log in to OpenShift
        run: |
          oc login ${{ secrets.OPENSHIFT_SERVER }} --token=${{ secrets.OPENSHIFT_TOKEN }} --insecure-skip-tls-verify=true
          oc project ${{ secrets.OPENSHIFT_PROJECT }}

      # Deploy to OpenShift
      - name: Apply deployment
        run: |
          oc apply -f deployment.yaml
          oc apply -f service.yaml
          oc apply -f route.yaml
```

> **Where you might get stuck:**
> - **Docker build/push errors:** Make sure Docker is installed and running locally if you want to test these steps manually. On GitHub Actions, ensure your repository has the correct permissions.
> - **sed command not working on Windows:** The `sed -i` command works on Linux runners (as in GitHub Actions). If you test locally on Windows, use a compatible tool or edit the file manually.
> - **OpenShift CLI install fails:** The `sudo` command is for Linux. On Windows, install the CLI manually from the [OpenShift CLI downloads](https://mirror.openshift.com/pub/openshift-v4/clients/oc/).
> - **oc login fails:** Double-check your `OPENSHIFT_SERVER`, `OPENSHIFT_TOKEN`, and `OPENSHIFT_PROJECT` secrets. Tokens can expire or be revoked.
> - **oc apply errors:** Ensure your YAML files are valid and reference the correct image/tag.

---

### 4. Secrets

On GitHub, go to your repository > Settings > Secrets and variables > Actions > New repository secret

There you need to set the following secrets:

- `OPENSHIFT_SERVER` (URL of your OpenShift API server)
- `OPENSHIFT_TOKEN` (Token for authentication)
- `OPENSHIFT_PROJECT` (Project/namespace name)
- `OPENSHIFT_APP_NAME` (Your app name, used for placeholder replacement)

You can find the values for these secrets in your OpenShift project.

#### Helpful commands

- To get the OpenShift server URL:
  ```bash
  oc whoami --show-server
  ```

- To get the OpenShift token:
  ```bash
  oc whoami --show-token
  ```

> **Tip:** If you don't want to use your personal token, you can create a Service Account and use its token instead (recommended for automation).

- Create Service Account
    ```bash
    oc create serviceaccount SERVICE_ACCOUNT_NAME -n YOUR_PROJECT_NAME
    ```
- Assign Role to Service Account
  ```bash
    oc adm policy add-role-to-user edit -z SERVICE_ACCOUNT_NAME -n YOUR_PROJECT_NAME
    ```
- Create Token for Service Account
  ```bash
    oc create token SERVICE_ACCOUNT_NAME -n YOUR_PROJECT_NAME --duration=TOKEN_DURATION_IN_SECONDS
  ```

> **Common Pitfall:** Service Account tokens may have limited permissions. If you get authorization errors, check the assigned roles and project.

---

## Troubleshooting

**Q: My workflow is not triggering!**
- Check that you are pushing to the `main` branch or using a tag like `v1.2.3`.
- Ensure GitHub Actions is enabled for your repository.

**Q: Docker image push fails with permission denied!**
- Check that your repository and package permissions allow writing to GHCR.
- Ensure `${{ secrets.GITHUB_TOKEN }}` is set and has the correct scope.

**Q: OpenShift login fails!**
- Double-check your `OPENSHIFT_SERVER` and `OPENSHIFT_TOKEN` secrets.
- Tokens can expire or be revoked; try generating a new one.
- Make sure your IP is allowed to access the OpenShift API (some clusters restrict access).

**Q: oc apply fails with YAML errors!**
- Validate your YAML files with a linter or `oc apply --dry-run=client -f <file>`.
- Ensure the image name and tag in `deployment.yaml` match what was pushed.

**Q: sed command fails on Windows!**
- The workflow runs on Ubuntu, so `sed` works there. For local testing on Windows, use Notepad++ or PowerShell equivalents.

---

## Conclusion

That's it! You now have a fully automated deployment pipeline for your OpenShift project.

> **If you get stuck, check the troubleshooting section above or search for your error message in the [OpenShift Docs](https://docs.openshift.com/) or [GitHub Actions Docs](https://docs.github.com/en/actions).**
