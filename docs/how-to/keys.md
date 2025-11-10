# Entity keys and IDs

This guide covers strategies for generating stable, deterministic entity identifiers in investigraph.

## Why stable IDs matter

Entity IDs must be:

- **Deterministic** - Same input data always produces the same ID
- **Unique** - No collisions between different entities
- **Stable** - IDs don't change across pipeline runs
- **Privacy-safe** - Don't expose personally-identifying information

## ID generation methods

Investigraph provides three main methods for generating entity IDs:

### `make_slug()`

Creates deterministic, prefixed IDs from values. Use for dataset-native identifiers.

```python
def handle(ctx, record, ix):
    entity = ctx.make_entity("Company")

    # Simple slug
    entity.id = ctx.make_slug(record["registration_number"])
    # Result: "dataset-12345"

    # With type prefix
    entity.id = ctx.make_slug("company", record["registration_number"])
    # Result: "dataset-company-12345"

    # Multiple components
    entity.id = ctx.make_slug("company", record["country"], record["reg_number"])
    # Result: "dataset-company-gb-12345"

    yield entity
```

**When to use:**

- Source has stable, unique identifiers
- You want readable IDs for debugging
- IDs should be consistent across dataset updates

### `make_id()`

Generates SHA1 hash IDs from values. Use for composite identifiers.

```python
def handle(ctx, record, ix):
    entity = ctx.make_entity("Person")

    # Hash multiple attributes
    entity.id = ctx.make_id(
        record["name"],
        record["birth_date"],
        record["country"]
    )
    # Result: "dataset-abc123def456..." (SHA1 hash)

    yield entity
```

**When to use:**

- No stable source identifier
- Need to combine multiple attributes
- IDs should hide sensitive information
- Want collision-resistant IDs

### `make_fingerprint_id()`

Generates IDs based on normalized fingerprints. Use when data has variations.

```python
def handle(ctx, record, ix):
    entity = ctx.make_entity("Person")

    # Handles name variations automatically
    entity.id = ctx.make_fingerprint_id(record["name"])
    # "John Smith" and "JOHN SMITH" produce same ID

    yield entity
```

**When to use:**

- Data has inconsistent formatting
- Names need normalization
- Want to deduplicate similar entities

## Relationship IDs

Generate IDs for relationships by combining entity IDs:

### Ownership

```python
def handle(ctx, record, ix):
    owner = ctx.make_entity("Person")
    owner.id = ctx.make_slug("person", record["person_id"])

    company = ctx.make_entity("Company")
    company.id = ctx.make_slug("company", record["company_id"])

    ownership = ctx.make_entity("Ownership")
    ownership.id = ctx.make_id(owner.id, "owns", company.id)
    ownership.add("owner", owner)
    ownership.add("asset", company)

    yield owner
    yield company
    yield ownership
```

### Membership

```python
def handle(ctx, record, ix):
    person = ctx.make_entity("Person")
    person.id = ctx.make_slug("person", record["person_id"])

    org = ctx.make_entity("Organization")
    org.id = ctx.make_slug("org", record["org_id"])

    membership = ctx.make_entity("Membership")
    membership.id = ctx.make_id(person.id, "member", org.id)
    membership.add("member", person)
    membership.add("organization", org)

    yield person
    yield org
    yield membership
```

### With temporal data

Include dates in relationship IDs when relationships can change over time:

```python
def handle(ctx, record, ix):
    person = ctx.make_entity("Person")
    person.id = ctx.make_slug("person", record["person_id"])

    position = ctx.make_entity("Position")
    position.id = ctx.make_slug("position", record["position_id"])

    # Include start date in ID
    occupancy = ctx.make_entity("Occupancy")
    occupancy.id = ctx.make_id(
        person.id,
        "holds",
        position.id,
        record.get("start_date", "unknown")
    )
    occupancy.add("holder", person)
    occupancy.add("post", position)
    occupancy.add("startDate", record.get("start_date"))

    yield person
    yield position
    yield occupancy
```

## Avoiding ID collisions

### Include entity type in ID

```python
# Wrong - may collide between persons and companies
person.id = ctx.make_slug(record["id"])
company.id = ctx.make_slug(record["id"])

# Correct - distinct ID spaces
person.id = ctx.make_slug("person", record["id"])
company.id = ctx.make_slug("company", record["id"])
```

### Privacy considerations

Never expose personally-identifying information in IDs:

```python
# Wrong - exposes SSN
entity.id = ctx.make_slug(record["social_security_number"])

# Correct - hash sensitive data
entity.id = ctx.make_id(record["social_security_number"])
```

## Key literals in YAML mappings

Use `key_literal` for static ID prefixes in YAML configuration:

```yaml
transform:
  queries:
    - entities:
        org:
          schema: Organization
          key_literal: gdho  # adds "gdho" prefix to all IDs
          keys:
            - Id
          properties:
            name:
              column: Name
```

This is equivalent to:

```python
entity.id = ctx.make_slug("gdho", record["Id"])
```

## Best practices

1. **Be consistent** - Use the same ID strategy across your dataset
2. **Include type prefixes** - Prevent collisions between entity types
3. **Use enough attributes** - Include sufficient data to ensure uniqueness
4. **Handle missing data** - Use placeholders like "unknown" for missing values
5. **Hash sensitive data** - Use `make_id()` for personally-identifying information
6. **Validate source IDs** - Check format before using as entity ID
7. **Document ID strategy** - Explain ID generation in dataset documentation
8. **Test stability** - Ensure IDs don't change across runs with same data

## Further reading

- [Context API reference](../reference/context.md) - `make_slug()`, `make_id()`, `make_fingerprint_id()` documentation
- [Transform patterns](transform.md) - Using IDs in transform handlers
- [FollowTheMoney](../stack/followthemoney.md) - Entity model and ID requirements
