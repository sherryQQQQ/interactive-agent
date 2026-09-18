# Docker

```bash
docker build -t interactive-agent .
docker run --rm interactive-agent
docker run --rm interactive-agent doctor
docker run --rm -v "$PWD/runs:/app/runs" interactive-agent demo --output runs/docker-demo
```

The default command lists experiments without contacting providers. Choose a
new demo output directory each time. Docker is optional; the Python checkout
is the primary tested development path. This image has not been build-tested
as part of the platform refactor.

External experiments need separately mounted source data, BM25 index and a
writable `/app/graphrag/eval/external` checkpoint directory. Data and credentials
are excluded from the image. Pass credentials at runtime only for an explicitly
authorized paid run. Inspect adapter `--help` and `--dry-run` first. Historical
checkpoints are not distributed in the image.
