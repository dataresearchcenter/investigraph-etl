# Utility functions

This guide covers helper functions and utilities available in investigraph for common data processing tasks.

## Context utilities

The context object (`ctx`) provides helper methods for common operations:

### Entity creation

```python
def handle(ctx, record, ix):
    # Create entity with schema
    entity = ctx.make_entity("Organization")
    entity.id = ctx.make_slug(record["id"])
    entity.add("name", record["name"])

    yield entity
```

### ID generation

See [Entity keys and IDs](keys.md) for detailed ID generation patterns.

```python
# Slug-based ID
entity.id = ctx.make_slug("prefix", value)

# Hash-based ID
entity.id = ctx.make_id(value1, value2, value3)

# Fingerprint-based ID
entity.id = ctx.make_fingerprint_id(name)
```

### Logging

```python
def handle(ctx, record, ix):
    # Debug logging
    ctx.log.debug("Processing record", record_id=record["id"])

    # Info logging
    ctx.log.info("Creating entity", type="Organization")

    # Warning logging
    ctx.log.warning("Missing field", field="country", row=ix)

    # Error logging
    ctx.log.error("Invalid data", value=record["date"])

    # ... process record
```

### Opening source files

Access the source file directly:

```python
def handle(ctx):
    """Custom extract handler"""
    with ctx.open() as fh:
        # fh is a file-like object
        for line in fh:
            yield process_line(line)
```

With specific mode:

```python
def handle(ctx):
    # Open in text mode
    with ctx.open(mode='r') as fh:
        content = fh.read()
        yield parse_content(content)
```

## Text processing

### Name cleaning

Use `ftmq.util.clean_name` for cleaning names:

```python
from ftmq.util import clean_name

def handle(ctx, record, ix):
    entity = ctx.make_entity("Person")
    entity.id = ctx.make_slug(record["id"])

    # Clean name (removes excess whitespace, normalizes)
    entity.add("name", clean_name(record["name"]))

    yield entity
```

### Text normalization

Use `normality` for text cleaning:

```python
from normality import slugify, collapse_spaces, stringify

def handle(ctx, record, ix):
    entity = ctx.make_entity("Person")

    # Remove extra whitespace
    name = collapse_spaces(record["name"])
    entity.add("name", name)

    # Convert to string safely
    age = stringify(record.get("age"))

    # Generate slug
    slug = slugify(record["id"])
    entity.id = ctx.make_slug(slug)

    yield entity
```

### Joining text

Use `investigraph.util.join_text` to join text with automatic cleaning:

```python
from investigraph.util import join_text

def handle(ctx, record, ix):
    entity = ctx.make_entity("Event")
    entity.id = ctx.make_slug(record["id"])

    # Join multiple text fields with automatic cleaning
    description = join_text(
        record.get("summary"),
        record.get("details"),
        sep=" - "
    )
    entity.add("summary", description)

    # Join names for caption
    participants = join_text(
        record.get("person1"),
        record.get("person2"),
        sep=", "
    )

    yield entity
```

### Fingerprinting

Use `ftmq.util.make_fingerprint` for name normalization and matching:

```python
from ftmq.util import make_fingerprint

def handle(ctx, record, ix):
    entity = ctx.make_entity("Person")

    name = record["name"]

    # Check if name has content after fingerprinting
    if make_fingerprint(name):
        entity.id = ctx.make_fingerprint_id(name)
        entity.add("name", name)

        yield entity
```

## Date handling

### Parsing dates

```python
from datetime import datetime

def parse_date(date_str):
    """Parse date from various formats"""
    if not date_str:
        return None

    # Try common formats
    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y%m%d",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.date().isoformat()
        except ValueError:
            continue

    return None
```

## Country handling

### Country code normalization

Use `ftmq.util` for country code conversion:

```python
from ftmq.util import get_country_code, get_country_name

def handle(ctx, record, ix):
    entity = ctx.make_entity("Organization")
    entity.id = ctx.make_slug(record["id"])
    entity.add("name", record["name"])

    # Convert country name to ISO 2-letter code
    country_code = get_country_code(record.get("country"))
    if country_code:
        entity.add("country", country_code)

    # Or convert code to name
    country_name = get_country_name(record.get("country_code"))
    if country_name:
        entity.add("notes", f"Country: {country_name}")

    yield entity
```

### Manual country mapping

For custom mappings:

```python
from normality import slugify

# Common country name mappings
COUNTRY_NAMES = {
    "united kingdom": "GB",
    "united states": "US",
    "united states of america": "US",
    "usa": "US",
    "uk": "GB",
    "great britain": "GB",
}

def normalize_country(country):
    """Normalize country to ISO 2-letter code"""
    if not country:
        return None

    # Already a 2-letter code
    if len(country) == 2:
        return country.upper()

    # Look up in mapping
    slug = slugify(country)
    return COUNTRY_NAMES.get(slug)
```

## Value mapping

### Simple mappings

```python
# Define mapping
STATUS_MAPPING = {
    "active": "active",
    "inactive": "inactive",
    "suspended": "inactive",
    "dissolved": "dissolved",
    "closed": "dissolved",
}

def handle(ctx, record, ix):
    entity = ctx.make_entity("Company")
    entity.id = ctx.make_slug(record["id"])
    entity.add("name", record["name"])

    # Map status value
    status = record.get("status", "").lower()
    mapped_status = STATUS_MAPPING.get(status)
    if mapped_status:
        entity.add("status", mapped_status)

    yield entity
```

## Error handling

### Graceful degradation

```python
def handle(ctx, record, ix):
    try:
        entity = ctx.make_entity("Organization")
        entity.id = ctx.make_slug(record["id"])
        entity.add("name", record["name"])

        # Try to parse optional date
        try:
            date = parse_date(record.get("founded"))
            entity.add("incorporationDate", date)
        except Exception as e:
            ctx.log.warning("Date parsing failed", value=record.get("founded"))

        yield entity

    except Exception as e:
        ctx.log.error("Failed to process record", row=ix, error=str(e))
```

## Advanced patterns

### Entity factories

Create reusable helper functions for common entity types:

```python
from ftmq.util import make_fingerprint
from followthemoney import StatementEntity
from followthemoney.util import make_entity_id

def make_address(ctx, data: dict) -> StatementEntity:
    """Factory for creating address entities"""
    location = data.pop("Location")
    id_ = ctx.make_id(location, prefix="addr")
    proxy = ctx.make_entity("Address", id_)
    proxy.add("full", location)
    return proxy


def make_person(ctx, name: str, role: str, body: StatementEntity) -> StatementEntity:
    """Factory for creating person entities linked to an organization"""
    id_ = ctx.make_slug("person", make_entity_id(body.id, make_fingerprint(name)))
    proxy = ctx.make_entity("Person", id_)
    proxy.add("name", name)
    proxy.add("description", role)
    return proxy


def make_organization(ctx, regId: str, name: str | None = None) -> StatementEntity:
    """Factory for creating organization entities"""
    id_ = ctx.make_slug(regId, prefix="eu-tr")
    proxy = ctx.make_entity("Organization", id_)
    if make_fingerprint(name):  # Check if name has content after fingerprinting
        proxy.add("name", name)
    proxy.add("idNumber", regId)
    return proxy


def handle(ctx, record, ix):
    # Use factories
    org = make_organization(ctx, record["org_id"], record.get("org_name"))
    person = make_person(ctx, record["person_name"], record["role"], org)

    yield org
    yield person
```

### Building complex events

Create complex entities with multiple relationships:

```python
from followthemoney.util import join_text, make_entity_id

def make_event(
    ctx, data: dict, organizer: StatementEntity, involved: list[StatementEntity]
) -> Generator[StatementEntity, None, None]:
    """Create an event with organizer, participants, and location"""
    date = data.pop("date")
    participants = list(make_organizations(ctx, data))

    # Generate ID from organizer and sorted participant IDs
    id_ = ctx.make_slug(
        "meeting",
        date,
        make_entity_id(organizer.id, *sorted([p.id for p in participants])),
    )

    event = ctx.make_entity("Event", id_)

    # Build event name from participants
    label = join_text(*[p.first("name") for p in participants])
    event.add("name", f"{date} - {organizer.caption} x {label}")
    event.add("date", date)
    event.add("summary", data.pop("subject"))

    # Add location
    address = make_address(ctx, data)
    event.add("location", address.caption)
    event.add("addressEntity", address)

    # Add participants
    event.add("organizer", organizer)
    event.add("involved", involved)
    event.add("involved", participants)

    # Yield all entities
    yield from participants
    yield address
    yield event


def handle(ctx, record, ix):
    organizer = make_organization(ctx, record["org_id"], record["org_name"])
    persons = [make_person(ctx, name, role, organizer)
               for name, role in zip_things(record["names"], record["roles"])]

    yield organizer
    yield from make_event(ctx, record, organizer, persons)
    yield from persons
```

### Safe string conversion

Use `investigraph.util.str_or_none` for safe conversion:

```python
from investigraph.util import str_or_none

def handle(ctx, record, ix):
    entity = ctx.make_entity("Organization")
    entity.id = ctx.make_slug(record["id"])

    # Safely convert values to strings, filtering out empty/None
    entity.add("name", str_or_none(record.get("name")))
    entity.add("idNumber", str_or_none(record.get("registration")))

    # Returns None for empty strings, 0, None, etc.
    phone = str_or_none(record.get("phone"))
    if phone:
        entity.add("phone", phone)

    yield entity
```

## Available utilities reference

### From `investigraph.util`

- `make_entity(schema, id, dataset, **properties)` - Create entity with properties
- `make_string_id(*parts)` - Generate string ID from parts
- `make_fingerprint(text)` - Generate fingerprint from text
- `make_fingerprint_id(*parts)` - Generate ID from fingerprints
- `clean_name(name)` - Clean and normalize name
- `join_text(*parts, sep=" ")` - Join text with automatic cleaning
- `str_or_none(value)` - Safe string conversion returning None for empty
- `make_data_checksum(data)` - Generate checksum for data

### From `ftmq.util`

- `clean_name(name)` - Clean and normalize names
- `get_country_code(name)` - Convert country name to ISO code
- `get_country_name(code)` - Convert ISO code to country name
- `join_slug(*parts, prefix=None)` - Join parts into slug
- `make_entity(data, entity_type, dataset)` - Create entity from dict
- `make_entity_id(*parts)` - Generate SHA1 ID from parts
- `make_fingerprint(text)` - Generate text fingerprint
- `make_fingerprint_id(*parts)` - Generate ID from fingerprints
- `normalize_name(name)` - Normalize name for matching
- `sanitize_text(text)` - Clean text for storage

### From `followthemoney.util`

- `make_entity_id(*parts)` - Generate SHA1 entity ID
- `join_text(*parts, sep=" ")` - Join text parts with separator


### From `normality`

- `slugify(text, sep="-")` - Generate URL-safe slug
- `collapse_spaces(text)` - Remove extra whitespace
- `stringify(value)` - Safe conversion to string

## Further reading

- [Transform patterns](transform.md) - Using utilities in transform handlers
- [Entity keys and IDs](keys.md) - ID generation utilities
- [Context API reference](../reference/context.md) - Full context API
- [Extract stage](../stages/extract.md) - Extract configuration
