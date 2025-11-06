# Best Practices

This section provides recommendations for building robust and maintainable datasets with investigraph. These practices are adapted from the [zavod framework](https://zavod.opensanctions.org) (developed by [OpenSanctions](https://opensanctions.org)) and tailored for investigraph's architecture.

## Overview

Building quality datasets requires attention to:

- **Code organization** - Structure your transform functions clearly
- **Data handling** - Track and validate all source fields
- **Entity identifiers** - Generate stable, deterministic IDs
- **Caching strategies** - Optimize extraction performance
- **Data priorities** - Focus on essential information first
- **Logging** - Use appropriate log levels for debugging and monitoring

## Sections

- **[Dataset metadata](metadata.md)** - Writing excellent dataset documentation
- **[Transform patterns](transform.md)** - Writing effective transform handlers
- **[Entity keys and IDs](keys.md)** - Generating stable entity identifiers
- **[Utility functions](utils.md)** - Using context helpers and common patterns

## Code organization

### Transform function structure

Organize transform functions with clear separation of concerns:

```python
def handle(ctx, record, ix):
    """
    Main transform handler:
    1. Extract and clean data from record
    2. Create entities
    3. Emit entities
    """
    # Extract data
    org = make_organization(ctx, record)
    person = make_person(ctx, record)

    # Create relationships
    membership = make_membership(ctx, person, org, record)

    # Emit all entities
    yield org
    yield person
    yield membership


def make_organization(ctx, record):
    """Create organization entity from record"""
    org = ctx.make_entity("Organization")
    org.id = ctx.make_slug(record.pop("org_id"))
    org.add("name", record.pop("org_name"))
    return org
```

Use descriptive helper function names following the `make_thing` pattern:

- `make_person()` - Creates Person entities
- `make_company()` - Creates Company entities
- `make_address()` - Composes address information

### Import order

Organize imports (enforced by ruff/isort):

```python
# Standard library
import csv
from datetime import datetime

# Third-party packages
import pandas as pd
from normality import slugify

# Investigraph
from investigraph.model import Context
```

### Constants and patterns

Define regular expressions and constants at module level:

```python
import re

# Precompile patterns
ID_PATTERN = re.compile(r"^[A-Z]{2}\d{6}$")
DATE_PATTERN = re.compile(r"(\d{4})-(\d{2})-(\d{2})")

# Define mappings
COUNTRY_CODES = {
    "United Kingdom": "GB",
    "United States": "US",
}
```

## Data priorities

When extracting data, prioritize based on importance:

### Essential (minimum)

- **Names** - At minimum, extract the name of each entity

```python
entity.add("name", record["name"])
```

### Essential (when available)

- **Identifiers** - Official registration numbers, IDs
- **Dates** - Birth dates, incorporation dates, sanction dates
- **Jurisdictions** - Countries, registration jurisdictions

```python
entity.add("idNumber", record.get("registration_number"))
entity.add("incorporationDate", record.get("founded"))
entity.add("country", record.get("jurisdiction"))
```

### Should include

- **Relationships** - Ownership, membership, family relations
- **Temporal data** - Start/end dates for positions, sanctions
- **Contact information** - When publicly available and relevant

### Could include

- **Source URLs** - Links to original data
- **Notes** - Additional context

## Logging

Use appropriate log levels:

**Debug** - Detailed information for development:
```python
ctx.log.debug("Processing record", id=record["id"], type=record["type"])
```

**Info** - Progress tracking for large datasets:
```python
ctx.log.info("Processed batch", count=ix, entity_type="Organization")
```

**Warning** - Issues that need attention:
```python
if not record.get("name"):
    ctx.log.warning("Missing name", record_id=record["id"], row=ix)
```

**Error** - Serious problems:
```python
try:
    date = parse_date(record["date"])
except ValueError as e:
    ctx.log.error("Date parsing failed", value=record["date"], error=str(e))
```

## Caching strategies

### Extract stage caching

Investigraph caches extracted sources by default. Control via environment:

```bash
# Disable caching for frequently-updated sources
INVESTIGRAPH_EXTRACT_CACHE=0 investigraph run -c config.yml
```

**Cache considerations:**

- **Index pages** - Consider disabling cache for frequently-updated sources (sanction lists, regulatory filings)
- **Detail pages** - Keep default caching for large, slow-moving datasets (corporate registries)
- **Paginated content** - Be careful with pagination as cached pages may become stale when new items are added

### Archive storage

Use archive storage for sources that rarely change:

```yaml
extract:
  archive: true  # downloads and stores sources locally
  sources:
    - uri: https://example.com/annual-report-2023.pdf
```

Disable archiving for dynamic APIs:

```yaml
extract:
  archive: false
  sources:
    - uri: https://api.example.com/sanctions?updated_since=2024-01-01
```

## Testing and validation

### Test with limited data

Use the `-l` flag to test with a subset of records:

```bash
# Extract and transform first 10 records
investigraph extract -c config.yml -l 10 | \
  investigraph transform -c config.yml
```

### Review checklist

Before considering a dataset complete:

- [ ] All source fields are mapped or explicitly ignored
- [ ] Entity IDs are stable and deterministic
- [ ] Required properties are present (name, identifiers)
- [ ] Relationships are properly linked
- [ ] Dates are in ISO format (YYYY-MM-DD)
- [ ] Countries use ISO 2-letter codes
- [ ] No personally-identifying information in IDs
- [ ] Logging covers important events and warnings
- [ ] Configuration is documented (summary, publisher)
- [ ] Test run produces expected entity counts
- [ ] No errors or warnings in logs

## Common pitfalls

### Mutable default arguments

Don't use mutable defaults:

```python
# Wrong
def make_entity(ctx, data, aliases=[]):
    entity = ctx.make_entity("Person")
    aliases.append(data["name"])  # Modifies shared list!
    return entity

# Correct
def make_entity(ctx, data, aliases=None):
    if aliases is None:
        aliases = []
    entity = ctx.make_entity("Person")
    aliases.append(data["name"])
    return entity
```

### Empty entity checks

Always check if entities are valid before yielding:

```python
def handle(ctx, record, ix):
    entity = ctx.make_entity("Organization")
    entity.id = ctx.make_slug(record.get("id"))
    entity.add("name", record.get("name"))

    # Check for required data
    if not entity.id or not entity.has("name"):
        ctx.log.warning("Skipping invalid entity", record=ix)
        return

    yield entity
```

### ID collisions

Ensure IDs are unique across the dataset:

```python
# Wrong - might collide if multiple entity types share ID space
entity.id = ctx.make_slug(record["id"])

# Correct - include entity type in ID
entity.id = ctx.make_slug("person", record["id"])
```

## Further reading

- **[Transform patterns](transform.md)** - Detailed transform examples
- **[Entity keys and IDs](keys.md)** - ID generation strategies
- **[Utility functions](utils.md)** - Context helpers and common patterns
- [Context API reference](../reference/context.md) - Available context methods
- [FollowTheMoney](../stack/followthemoney.md) - Entity model documentation
