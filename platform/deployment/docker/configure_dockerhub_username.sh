#!/usr/bin/env bash
# platform/deployment/docker/configure_dockerhub_username.sh
# Designed to be SOURCED by run.sh — no top-level executable code outside functions.

set -euo pipefail

configure_dockerhub_username() {
    echo "🐳 Configuring Docker Hub username for GitOps"

    # In ArgoCD mode the username is already hardcoded in the kustomization.yaml
    # overlays. ArgoCD reads directly from Git and cannot access .env.
    if [[ "${DEPLOY_MODE:-}" == "argocd" ]]; then
        echo "✅ ArgoCD mode — DockerHub username is set in overlay kustomization.yaml (skipping substitution)"
        return 0
    fi

    # Direct mode — validate the variable is set
    : "${DOCKERHUB_USERNAME:?Set DOCKERHUB_USERNAME in .env}"
    : "${APP_NAME:=devops-console}"
    : "${PROJECT_ROOT:?PROJECT_ROOT must be set}"

    echo "🔧 Setting DockerHub image in kustomize overlays (direct mode)"

    local changed=0
    local overlay
    # Kustomize overlays live under platform/deployment/kubernetes/overlays/<env>,
    # not under app/ — app/ only contains the Python source and Dockerfile.
    for overlay in local prod; do
        local kfile="${PROJECT_ROOT}/platform/deployment/kubernetes/overlays/${overlay}/kustomization.yaml"
        if [[ ! -f "$kfile" ]]; then
            echo "  ℹ️  kubernetes/overlays/${overlay}/kustomization.yaml not found — skipping"
            continue
        fi

        # Use a temp file for portability (macOS/BSD sed -i requires a suffix
        # argument, GNU sed doesn't — writing to a temp file avoids that
        # incompatibility entirely so this works on any Linux/macOS box).
        local tmpfile
        tmpfile=$(mktemp)
        sed "s|newName:.*|newName: ${DOCKERHUB_USERNAME}/${APP_NAME}|g" \
            "$kfile" > "$tmpfile"
        mv "$tmpfile" "$kfile"
        echo "  ✅ Updated image in kubernetes/overlays/${overlay}/kustomization.yaml"
        changed=$((changed + 1))
    done

    if [[ $changed -eq 0 ]]; then
        echo "  ⚠️  No kustomization overlay files were found or updated"
        return 1
    fi

    echo "✅ Docker Hub username configured"
}