# GitHub Pages

The website and Python program use Version 3. The static website in `dist/`
runs its scientific Python engine in the browser. A separate Python server
or ChatGPT login is not required by this application.

The repository includes `.github/workflows/pages.yml`. After the source is
pushed to the `main` branch, enable **Settings → Pages → Build and deployment
→ Source → GitHub Actions**. The workflow checks the release, uploads `dist/`
and deploys it. The completed workflow reports the actual website URL.

All application assets use relative paths, including the Python worker and
its self-hosted scientific dependencies. This supports a project site under
a repository path as well as a site at the domain root. Navigation uses URL
fragments, so tutorial and calculator links do not require server rewrites.

To update a notebook calculation, modify `sources/notebook_v3.ipynb`, keep
the tutorial annotations in `sources/tutorial_*.json` aligned, install the
notebook requirements, and run:

```bash
python validate_notebook.py
python prepare_content.py
python verify_checking_procedures.py
python scripts/check_release.py
```

Commit both the sources and generated `dist/` files. The Pages workflow
publishes those exact checked static assets. The workflow does not rerun
scientific calculations or infer tensor coefficients during deployment.

Official instructions:
https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
