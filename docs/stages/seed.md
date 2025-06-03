## config.yml

Example: All .csv files in a local folder

```yaml
seed:
  uri: ./data
  glob: "**/*.csv"
```

## Reference

### ::: investigraph.model.stage.SeedStage

## Bring your own code

```yaml
seed:
  handler: ./seed.py:handle
```

### Function signature

#### ::: investigraph.logic.seed
