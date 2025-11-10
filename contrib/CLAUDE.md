# Building Dataset Scrapers with investigraph

This guide helps Claude AI agents build dataset scrapers using the investigraph framework. This is **not** about developing the core investigraph library itself, but about creating dataset scrapers.

## What is investigraph?

investigraph is an ETL framework for building FollowTheMoney (FTM) datasets. It extracts data from sources, transforms it into structured entities, and exports it in standardized formats.

**Core principles:**

- **YAML-first approach** - Most datasets built with config.yml, minimal Python
- **pandas integration** - Extract data using runpandarun
- **FollowTheMoney entities** - Structured format for people, companies, relationships
- **Deterministic IDs** - Stable entity identifiers across runs
- **Incremental patterns** - Start simple, add complexity as needed

## Quick start

Every dataset needs:

1. `config.yml` - Dataset configuration
2. Optional `extract.py` - Custom extraction logic (if needed)
3. Optional `transform.py` - Custom transformation logic (if needed)

Most datasets only need `config.yml`.

## Step 1: Create config.yml

Basic structure:

```yaml
name: my_dataset
title: My Dataset Title
prefix: my-prefix

summary: |
  Brief one-sentence description of what this dataset contains.

publisher:
  name: Source Organization
  url: https://example.com

extract:
  sources:
    - uri: https://example.com/data.csv

transform:
  queries:
    - entities:
        person:
          schema: Person
          keys:
            - person_id
          properties:
            name:
              column: person_name
```

## Step 2: Extract configuration

### Simple CSV/Excel extraction

```yaml
extract:
  sources:
    - uri: https://example.com/data.csv
      pandas:
        read:
          options:
            encoding: utf-8
```

### Multiple sources

```yaml
extract:
  sources:
    - uri: https://example.com/2023.csv
    - uri: https://example.com/2024.csv
```

### Custom extraction (when needed)

Create `extract.py` for APIs or complex formats:

```python
def handle(ctx):
    # Simple extraction
    with ctx.open() as fh:
        for line in fh:
            yield {"id": line.strip()}
```

Handler signature:
- `ctx`: SourceContext with helper methods
- Yields: dictionaries (records)

## Step 3: Transform configuration

### YAML-only transforms (recommended)

```yaml
transform:
  queries:
    - entities:
        person:
          schema: Person
          keys: [person_id]
          properties:
            name:
              column: person_name
            birthDate:
              column: birth_date
            country:
              column: nationality
```

### Python transforms (for complex logic)

Create `transform.py`:

```python
def handle(ctx, record, ix):
    # Create entity
    entity = ctx.make_entity("Person")
    entity.id = ctx.make_slug(record["id"])
    entity.add("name", record["name"])

    yield entity
```

Handler signature:
- `ctx`: SourceContext with helper methods
- `record`: dict from extract stage
- `ix`: record index
- Yields: entities

## Entity ID generation

Three methods for generating IDs:

### make_slug() - For dataset-native IDs

```python
# Simple ID
entity.id = ctx.make_slug(record["id"])
# Result: "prefix-12345"

# With type prefix
entity.id = ctx.make_slug("person", record["id"])
# Result: "prefix-person-12345"

# Multiple components
entity.id = ctx.make_slug("company", record["country"], record["reg_number"])
# Result: "prefix-company-gb-12345"
```

Use when source has stable unique identifiers.

### make_id() - For hashed IDs

```python
# Hash multiple attributes
entity.id = ctx.make_id(
    record["name"],
    record["birth_date"],
    record["country"]
)
# Result: "prefix-abc123def456..." (SHA1)
```

Use when:
- No stable source identifier exists
- Need to combine multiple attributes
- Should hide sensitive information

### make_fingerprint_id() - For normalized IDs

```python
# Handles variations automatically
entity.id = ctx.make_fingerprint_id(record["name"])
# "John Smith" and "JOHN SMITH" produce same ID
```

Use when data has inconsistent formatting.

## Common transform patterns

### Single entity per record

```python
def handle(ctx, record, ix):
    entity = ctx.make_entity("Organization")
    entity.id = ctx.make_slug(record["id"])
    entity.add("name", record["name"])
    entity.add("country", record["country"])

    yield entity
```

### Multiple entities per record

```python
def handle(ctx, record, ix):
    # Create company
    company = ctx.make_entity("Company")
    company.id = ctx.make_slug("company", record["company_id"])
    company.add("name", record["company_name"])
    yield company

    # Create director
    director = ctx.make_entity("Person")
    director.id = ctx.make_slug("person", record["director_id"])
    director.add("name", record["director_name"])
    yield director

    # Create relationship
    directorship = ctx.make_entity("Directorship")
    directorship.id = ctx.make_id(director.id, "director", company.id)
    directorship.add("director", director)
    directorship.add("organization", company)
    yield directorship
```

### Field tracking

```python
def handle(ctx, record, ix):
    # Copy record to track fields
    data = dict(record)

    entity = ctx.make_entity("Organization")
    entity.id = ctx.make_slug(data.pop("id"))
    entity.add("name", data.pop("name"))
    entity.add("country", data.pop("country", None))

    # Log unhandled fields
    if data:
        ctx.log.warning("Unhandled fields", fields=list(data.keys()), record=ix)

    yield entity
```

### Conditional entity creation

```python
def handle(ctx, record, ix):
    # Skip test records
    if record.get("status") == "TEST":
        return

    # Choose schema based on type
    entity_type = record.get("type", "").lower()

    if entity_type == "person":
        entity = ctx.make_entity("Person")
        entity.add("birthDate", record.get("birth_date"))
    elif entity_type == "company":
        entity = ctx.make_entity("Company")
        entity.add("incorporationDate", record.get("founded_date"))
    else:
        ctx.log.warning("Unknown entity type", type=entity_type, row=ix)
        return

    entity.id = ctx.make_slug(entity_type, record["id"])
    entity.add("name", record["name"])

    yield entity
```

## Utility functions

### From ftmq.util

```python
from ftmq.util import (
    make_fingerprint,      # Normalize text for matching
    clean_name,            # Clean person/org names
    get_country_code,      # "United Kingdom" -> "gb"
    join_text,             # Join with cleaning
)

# Examples
fingerprint = make_fingerprint("  John  Smith  ")  # "john smith"
clean = clean_name("Mr. John Smith, Jr.")  # "John Smith"
code = get_country_code("United Kingdom")  # "gb"
text = join_text("Hello", "", "World")  # "Hello World"
```

### From investigraph.util

```python
from investigraph.util import (
    join_text,        # Join text with cleaning
    str_or_none,      # Safe string conversion
)

# Examples
text = join_text("First", None, "Last")  # "First Last"
safe = str_or_none(None)  # None instead of "None"
```

### Address composition

```python
entity.add("country", record.get("country"))
entity.add("city", record.get("city"))
entity.add("street", record.get("street"))
entity.add("postalCode", record.get("postal_code"))
```

## Dataset metadata

Essential fields:

```yaml
name: dataset_slug          # Lowercase with underscores
title: Human Readable Title # Official source name
prefix: short-id           # 2-10 characters for entity IDs

summary: |
  One to two sentences explaining what the dataset contains.
  Focus on who/what is included.

description: |
  Paragraph 1: What the dataset contains and why it exists.
  Paragraph 2: What data fields are included and their quality.
  Paragraph 3: Update frequency, source authority, limitations.

publisher:
  name: Organization Name
  description: |
    Who they are and their role. Explain for international users
    unfamiliar with the organization.
  url: https://official-site.org
  country: us
  official: true

frequency: daily  # daily, weekly, monthly, annually, never
category: sanctions  # sanctions, crime, corp, role.pep, gov
license: CC-BY-4.0
```

## Entity schemas

FollowTheMoney defines entity schemas that represent people, organizations, and relationships. Each schema has specific properties it can contain.

**Explore all schemas and properties:**

https://followthemoney.tech/explorer/schemata/

Use the schema explorer to:
- Browse all available entity schemas
- See which properties each schema supports
- Understand property types (name, date, country, etc.)
- Check required vs optional properties
- View schema inheritance relationships

Common schemas:

**People:**
- `Person` - Individual
- `LegalEntity` - Generic person or organization

**Organizations:**
- `Organization` - Generic organization
- `Company` - Business entity
- `PublicBody` - Government institution

**Relationships:**
- `Membership` - Person ↔ Organization
- `Directorship` - Director ↔ Company
- `Ownership` - Owner ↔ Asset
- `Family` - Person ↔ Relative
- `Occupancy` - Person ↔ Position

**Other:**
- `Event` - Meeting, transaction
- `Passport` - Travel document
- `Address` - Physical location

## Testing and validation

### Test with limited data

```bash
# Extract and transform first 10 records
investigraph extract -c config.yml -l 10 | \
  investigraph transform -c config.yml
```

### Run complete pipeline

```bash
investigraph run -c config.yml
```

### Check output

```bash
# View entities
cat data/entities.ftm.json | head

# Count entities
cat data/entities.ftm.json | wc -l
```

## Review checklist

Before considering dataset complete:

- [ ] All source fields are mapped or explicitly ignored
- [ ] Entity IDs are stable and deterministic
- [ ] Required properties present (name, identifiers)
- [ ] Relationships properly linked
- [ ] Dates in ISO format (YYYY-MM-DD)
- [ ] Countries use ISO 2-letter codes
- [ ] No personally-identifying information in IDs
- [ ] Logging covers important events
- [ ] Configuration documented (summary, publisher)
- [ ] Test run produces expected entity counts
- [ ] No errors or warnings in logs

## Common entity types and properties

### Person

```python
person = ctx.make_entity("Person")
person.id = ctx.make_slug("person", record["id"])
person.add("name", record["name"])
person.add("birthDate", record["birth_date"])  # YYYY-MM-DD
person.add("nationality", record["country"])    # ISO 2-letter
person.add("idNumber", record["passport"])
```

### Company

```python
company = ctx.make_entity("Company")
company.id = ctx.make_slug("company", record["id"])
company.add("name", record["name"])
company.add("country", record["jurisdiction"])
company.add("incorporationDate", record["founded"])
company.add("idNumber", record["registration_number"])
```

### Organization

```python
org = ctx.make_entity("Organization")
org.id = ctx.make_slug("org", record["id"])
org.add("name", record["name"])
org.add("country", record["country"])
```

### Membership

```python
membership = ctx.make_entity("Membership")
membership.id = ctx.make_id(person.id, "member", org.id)
membership.add("member", person)
membership.add("organization", org)
membership.add("role", record["position"])
membership.add("startDate", record["start_date"])
```

### Ownership

```python
ownership = ctx.make_entity("Ownership")
ownership.id = ctx.make_id(owner.id, "owns", company.id)
ownership.add("owner", owner)
ownership.add("asset", company)
ownership.add("percentage", record["stake"])
ownership.add("startDate", record["acquired_date"])
```

## Logging

Use appropriate log levels:

```python
# Debug - Detailed development info
ctx.log.debug("Processing record", id=record["id"])

# Info - Progress tracking
if ix % 1000 == 0:
    ctx.log.info("Progress", records_processed=ix)

# Warning - Issues needing attention
if not record.get("name"):
    ctx.log.warning("Missing name", record_id=record["id"], row=ix)

# Error - Serious problems
try:
    date = parse_date(record["date"])
except ValueError as e:
    ctx.log.error("Date parsing failed", value=record["date"], error=str(e))
```

## Best practices

### Code organization

Organize transforms with helper functions:

```python
def handle(ctx, record, ix):
    # Extract data
    org = make_organization(ctx, record)
    person = make_person(ctx, record)

    # Create relationships
    membership = make_membership(ctx, person, org, record)

    # Emit all
    yield org
    yield person
    yield membership


def make_organization(ctx, record):
    org = ctx.make_entity("Organization")
    org.id = ctx.make_slug(record.pop("org_id"))
    org.add("name", record.pop("org_name"))
    return org
```

### Data priorities

When extracting data, prioritize:

**Essential (minimum):**
- Names

**Essential (when available):**
- Identifiers (registration numbers, IDs)
- Dates (birth dates, incorporation dates)
- Jurisdictions (countries)

**Should include:**
- Relationships (ownership, membership)
- Temporal data (start/end dates)

**Could include:**
- Source URLs
- Notes, additional context

### Avoid ID collisions

```python
# Wrong - may collide between persons and companies
person.id = ctx.make_slug(record["id"])
company.id = ctx.make_slug(record["id"])

# Correct - distinct ID spaces
person.id = ctx.make_slug("person", record["id"])
company.id = ctx.make_slug("company", record["id"])
```

### Privacy considerations

```python
# Wrong - exposes sensitive data
entity.id = ctx.make_slug(record["social_security_number"])

# Correct - hash sensitive data
entity.id = ctx.make_id(record["social_security_number"])
```

## Common pitfalls

### Empty entity checks

```python
def handle(ctx, record, ix):
    entity = ctx.make_entity("Organization")
    entity.id = ctx.make_slug(record.get("id"))
    entity.add("name", record.get("name"))

    # Check before yielding
    if not entity.id or not entity.has("name"):
        ctx.log.warning("Skipping invalid entity", record=ix)
        return

    yield entity
```

### Mutable default arguments

```python
# Wrong
def make_entity(ctx, data, aliases=[]):
    aliases.append(data["name"])  # Modifies shared list!
    return entity

# Correct
def make_entity(ctx, data, aliases=None):
    if aliases is None:
        aliases = []
    aliases.append(data["name"])
    return entity
```

## Configuration reference

### Extract options

```yaml
extract:
  handler: ./extract.py:handle  # Optional custom handler
  archive: true                 # Store sources locally
  sources:
    - uri: https://example.com/data.csv
      name: custom_name          # Optional source name
      pandas:
        read:
          options:
            encoding: utf-8
            sep: ","
```

### Transform options

```yaml
transform:
  handler: ./transform.py:handle  # Optional custom handler
  queries:
    - entities:
        person:
          schema: Person
          key_literal: custom-prefix  # Add static prefix
          keys: [person_id]           # ID columns
          properties:
            name:
              column: person_name
            birthDate:
              column: birth_date
```

### Export options

```yaml
export:
  handler: ./export.py:handle           # Optional custom handler
  index_uri: ./data/index.json          # Index file path
  entities_uri: ./data/entities.ftm.json  # Entities file path
```

## FollowTheMoney schema reference

All entity types and properties are defined by the FollowTheMoney specification.

**Schema Explorer**: https://followthemoney.tech/explorer/schemata/

The schema explorer shows:
- Complete list of all entity schemas
- Properties available for each schema
- Property types and validation rules
- Schema inheritance hierarchy
- Required vs optional properties

When building transforms, always check the schema explorer to ensure you're using the correct property names and types for your entities.

## Documentation references

- **Tutorial**: docs/tutorial.md
- **Configuration**: docs/build/config.md
- **Transform patterns**: docs/how-to/transform.md
- **Entity IDs**: docs/how-to/keys.md
- **Utilities**: docs/how-to/utils.md
- **Metadata**: docs/how-to/metadata.md

## Example workflow

1. **Start simple** - Use YAML-only config
2. **Test early** - Run with limited data (`-l 10`)
3. **Add complexity** - Write Python handlers if needed
4. **Track fields** - Ensure all source data is handled
5. **Validate output** - Check entity counts and properties
6. **Document** - Write clear metadata
7. **Review** - Use checklist before completion

## Getting help

When asking for help, provide:

1. Your config.yml
2. Sample input data (2-3 records)
3. Expected output entities
4. Error messages or logs
5. What you've tried

This helps Claude understand your specific dataset needs and provide targeted assistance.
