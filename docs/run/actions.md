# GitHub Actions

Automate dataset pipelines using GitHub Actions. This allows scheduled execution, automatic updates, and CI/CD integration for your investigraph datasets.

## Example: Dataset catalog automation

The [dataresearchcenter/datasets](https://github.com/dataresearchcenter/datasets) repository demonstrates a complete automation setup with scheduled workflows for different intervals.

## Basic workflow

Create `.github/workflows/run-dataset.yml`:

```yaml
name: Run dataset

on:
  workflow_dispatch: {}  # manual trigger
  schedule:
    - cron: '0 2 * * *'  # daily at 2am UTC

jobs:
  run:
    runs-on: ubuntu-latest
    container:
      image: ghcr.io/dataresearchcenter/investigraph:latest

    steps:
      - uses: actions/checkout@v4

      - name: Run dataset
        run: |
          investigraph run \
            -c /datasets/my_dataset/config.yml \
            --entities-uri ./data/entities.ftm.json \
            --index-uri ./data/index.json

      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: dataset-output
          path: ./data/
```

## Processing multiple datasets in parallel

Use matrix strategy to process multiple datasets concurrently:

```yaml
name: Run datasets

on:
  schedule:
    - cron: '13 12 * * *'  # daily at 12:13 UTC
  workflow_dispatch: {}

jobs:
  data:
    runs-on: ubuntu-latest
    container:
      image: ghcr.io/dataresearchcenter/datasets:latest

    strategy:
      matrix:
        dataset:
          - ec_meetings
          - eu_transparency_register
          - gdho

    env:
      AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
      AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
      AWS_S3_ENDPOINT_URL: https://s3.investigativedata.org

    steps:
      - name: Run dataset
        run: |
          investigraph run \
            -c /datasets/${{ matrix.dataset }}/config.yml \
            --entities-uri s3://data.ftm.store/${{ matrix.dataset }}/entities.ftm.json \
            --index-uri s3://data.ftm.store/${{ matrix.dataset }}/index.json
```

## Building and publishing catalogs

Process datasets and build a catalog:

```yaml
name: Build catalog

on:
  schedule:
    - cron: '0 3 * * *'
  workflow_dispatch: {}

jobs:
  datasets:
    runs-on: ubuntu-latest
    container:
      image: ghcr.io/myorg/datasets:latest

    strategy:
      matrix:
        dataset:
          - dataset1
          - dataset2
          - dataset3

    env:
      AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
      AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}

    steps:
      - name: Process dataset
        run: |
          investigraph run \
            -c /datasets/${{ matrix.dataset }}/config.yml \
            --entities-uri s3://bucket/${{ matrix.dataset }}/entities.ftm.json \
            --index-uri s3://bucket/${{ matrix.dataset }}/index.json

  catalog:
    needs: datasets
    runs-on: ubuntu-latest
    container:
      image: ghcr.io/myorg/datasets:latest

    env:
      AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
      AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
      AWS_S3_ENDPOINT_URL: https://s3.endpoint.com

    steps:
      - name: Build catalog
        working-directory: /datasets
        run: make publish

      - name: Send notification
        if: success()
        run: |
          anystore io -i ${{ secrets.HEARTBEAT_URL }}
```

## Scheduled workflows at different intervals

### Daily workflow

```yaml
name: Daily datasets

on:
  schedule:
    - cron: '0 2 * * *'  # 2am UTC daily
  workflow_dispatch: {}

jobs:
  run:
    # ... job configuration
```

### Weekly workflow

```yaml
name: Weekly datasets

on:
  schedule:
    - cron: '0 3 * * 0'  # 3am UTC on Sundays
  workflow_dispatch: {}

jobs:
  run:
    # ... job configuration
```

### Monthly workflow

```yaml
name: Monthly datasets

on:
  schedule:
    - cron: '0 4 1 * *'  # 4am UTC on 1st of month
  workflow_dispatch: {}

jobs:
  run:
    # ... job configuration
```

## Using custom Docker images

Build and use a custom image in workflows:

```yaml
name: CI/CD

on:
  push:
    branches: [main]
  workflow_dispatch: {}

jobs:
  build-image:
    runs-on: ubuntu-latest
    permissions:
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: .
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ghcr.io/${{ github.repository }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

  run-datasets:
    needs: build-image
    runs-on: ubuntu-latest
    container:
      image: ghcr.io/${{ github.repository }}:latest

    steps:
      - name: Run pipelines
        run: |
          investigraph run -c /datasets/dataset1/config.yml
```

## Caching strategies

Use GitHub Actions cache to speed up builds:

```yaml
steps:
  - uses: actions/checkout@v4

  - name: Cache investigraph archive
    uses: actions/cache@v4
    with:
      path: ~/.cache/investigraph
      key: ${{ runner.os }}-investigraph-${{ hashFiles('datasets/**/config.yml') }}
      restore-keys: |
        ${{ runner.os }}-investigraph-

  - name: Run dataset
    run: investigraph run -c datasets/my_dataset/config.yml
```

## Publishing to cloud storage

### S3-compatible storage

```yaml
env:
  AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
  AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
  AWS_S3_ENDPOINT_URL: https://s3.endpoint.com

steps:
  - name: Run and publish
    run: |
      investigraph run \
        -c /datasets/my_dataset/config.yml \
        --entities-uri s3://bucket/dataset/entities.ftm.json \
        --index-uri s3://bucket/dataset/index.json
```

### Google Cloud Storage

```yaml
env:
  GOOGLE_APPLICATION_CREDENTIALS: ${{ secrets.GCS_CREDENTIALS }}

steps:
  - name: Run and publish
    run: |
      investigraph run \
        -c /datasets/my_dataset/config.yml \
        --entities-uri gs://bucket/dataset/entities.ftm.json \
        --index-uri gs://bucket/dataset/index.json
```

## Error notifications

Send notifications on failure:

```yaml
jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - name: Run dataset
        run: investigraph run -c datasets/my_dataset/config.yml

      - name: Notify on failure
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: 'Dataset pipeline failed',
              body: 'Workflow ${{ github.workflow }} failed on run ${{ github.run_id }}'
            })
```

## Testing datasets in CI

Test datasets on pull requests:

```yaml
name: Test datasets

on:
  pull_request:
    paths:
      - 'datasets/**'
      - '.github/workflows/test.yml'

jobs:
  test:
    runs-on: ubuntu-latest
    container:
      image: ghcr.io/dataresearchcenter/investigraph:latest

    steps:
      - uses: actions/checkout@v4

      - name: Extract test data
        run: |
          investigraph extract \
            -c datasets/${{ matrix.dataset }}/config.yml \
            -l 10

      - name: Transform test data
        run: |
          investigraph extract -c datasets/${{ matrix.dataset }}/config.yml -l 10 | \
          investigraph transform -c datasets/${{ matrix.dataset }}/config.yml
```

## Complete example: dataresearchcenter/datasets workflow

Based on the [dataresearchcenter/datasets repository](https://github.com/dataresearchcenter/datasets):

```yaml
name: Daily datasets

on:
  schedule:
    - cron: '13 12 * * *'
  workflow_dispatch: {}

jobs:
  data:
    runs-on: ubuntu-latest
    container:
      image: ghcr.io/dataresearchcenter/datasets:latest

    strategy:
      matrix:
        dataset:
          - ec_meetings
          - eu_transparency_register

    env:
      AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
      AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
      AWS_S3_ENDPOINT_URL: ${{ secrets.AWS_S3_ENDPOINT_URL }}

    steps:
      - name: Run dataset pipeline
        run: |
          investigraph run \
            -c /datasets/${{ matrix.dataset }}/config.yml \
            --entities-uri s3://data.ftm.store/${{ matrix.dataset }}/entities.ftm.json \
            --index-uri s3://data.ftm.store/${{ matrix.dataset }}/index.json

  catalog:
    needs: data
    runs-on: ubuntu-latest
    container:
      image: ghcr.io/dataresearchcenter/datasets:latest

    env:
      AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
      AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
      AWS_S3_ENDPOINT_URL: ${{ secrets.AWS_S3_ENDPOINT_URL }}

    steps:
      - name: Publish catalog
        working-directory: /datasets
        run: make publish

      - name: Send heartbeat
        if: success()
        run: anystore io -i ${{ secrets.DATASETS_DAILY_HEARTBEAT }}
```

## Secrets configuration

Required secrets in repository settings:

- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_S3_ENDPOINT_URL` - S3 endpoint URL (optional, for custom endpoints)
- `DATASETS_DAILY_HEARTBEAT` - Monitoring/notification URL (optional)

## Best practices

1. **Use workflow_dispatch** - Always include manual trigger for testing
2. **Set reasonable schedules** - Avoid running all workflows at the same time
3. **Use matrix for parallelization** - Process multiple datasets concurrently
4. **Cache appropriately** - Cache archive and extracted data between runs
5. **Monitor failures** - Set up notifications for failed runs
6. **Test in CI** - Validate datasets on pull requests before merging
7. **Use secrets** - Never hardcode credentials in workflow files
8. **Version control outputs** - Consider committing generated index files for tracking
9. **Document schedules** - Comment why specific cron schedules are chosen
10. **Use containers** - Run in Docker containers for consistency

## Debugging workflows

Enable debug logging:

```yaml
env:
  DEBUG: 1
  ACTIONS_STEP_DEBUG: true
```

Add verbose investigraph output:

```yaml
steps:
  - name: Run with debug
    run: |
      investigraph --verbose run -c datasets/my_dataset/config.yml
```

Test locally with act:

```bash
# Install act: https://github.com/nektos/act
act -j run-datasets --secret-file .secrets
```
