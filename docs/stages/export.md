::: investigraph.logic.export



### Metadata

Location for the resulting [dataset metadata](../concepts/dataset.md), typically called `index.json`. Again, as investigraph is using [fsspec](https://github.com/fsspec/filesystem_spec) (see above), this can basically be anywhere:

**config.yml**

```yaml
load:
  index_uri: s3://my_bucket/<dataset>/index.json
```

**command line**

    investigraph run ... --index-uri sftp://username:password@host/<dataset>/index.json


**command line**

    investigraph run ... --entities-uri ...

#### `export.index_uri`

Uri to output dataset metadata. Can be anything that `fsspec` understands.

**Example**: `s3://<bucket-name>/<dataset-name>/index.json`

**Default**: `./data/<dataset-name>/index.json`

#### `export.entities_uri`

Uri to output transformed entities. Can be anything that `fsspec` understands, plus a `SQL` endpoint (for use with [followthemoney-store](https://github.com/alephdata/followthemoney-store))

**Example**:

- `s3://<bucket-name>/<dataset-name>/entities.ftm.json`
- `postgresql://user:password@host:port/database`

**Default**: `./data/<dataset-name>/entities.ftm.json`
