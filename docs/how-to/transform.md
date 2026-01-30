# Transform patterns

This guide covers patterns for writing effective transform handlers that convert extracted records into FollowTheMoney entities.

## Data handling

### Field tracking

Track which source fields you've processed to catch unmapped data:

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

### Address composition

Build addresses from individual fields:

```python
def handle(ctx, record, ix):
    entity = ctx.make_entity("Person")
    entity.id = ctx.make_slug(record["id"])
    entity.add("name", record["name"])

    # Compose address from parts
    entity.add("country", record.get("country"))
    entity.add("city", record.get("city"))
    entity.add("street", record.get("street"))
    entity.add("postalCode", record.get("postal_code"))

    yield entity
```

## Multiple entities per record

Emit multiple related entities from a single record:

```python
def handle(ctx, record, ix):
    # Create company
    company = ctx.make_entity("Company")
    company.id = ctx.make_slug(record["company_id"])
    company.add("name", record["company_name"])
    yield company

    # Create director
    director = ctx.make_entity("Person")
    director.id = ctx.make_slug(record["director_id"])
    director.add("name", record["director_name"])
    yield director

    # Create directorship relationship
    directorship = ctx.make_entity("Directorship")
    directorship.id = ctx.make_id(director.id, "director", company.id)
    directorship.add("director", director)
    directorship.add("organization", company)
    directorship.add("role", record.get("director_role"))
    yield directorship
```

## Using task context

For complex transformations with helper functions that emit multiple entities:

```python
def make_person(task_ctx, data):
    """Helper that emits multiple entities"""
    person = task_ctx.make_entity("Person")
    person.id = task_ctx.make_slug(data["id"])
    person.add("name", data["name"])

    # Create associated entities
    if data.get("passport"):
        passport = task_ctx.make_entity("Passport")
        passport.id = task_ctx.make_id(person.id, "passport", data["passport"])
        passport.add("holder", person)
        passport.add("number", data["passport"])
        task_ctx.emit(passport)  # emit via context

    return person


def handle(ctx, record, ix):
    task_ctx = ctx.task()

    # Use helper functions
    person = make_person(task_ctx, record)
    task_ctx.emit(person)

    # Yield all emitted entities
    yield from task_ctx
```

## Data validation

### Runtime assertions

Use assertions to catch data issues early:

```python
def handle(ctx, record, ix):
    entity = ctx.make_entity("Organization")

    # Ensure required fields exist
    assert record.get("id"), f"Missing ID at row {ix}"
    entity.id = ctx.make_slug(record["id"])

    # Validate data format
    assert len(record["country"]) == 2, f"Invalid country code: {record['country']}"
    entity.add("country", record["country"])

    yield entity
```

### Schema validation

Validate entities before yielding:

```python
def handle(ctx, record, ix):
    entity = ctx.make_entity("Person")
    entity.id = ctx.make_slug(record["id"])
    entity.add("name", record["name"])

    # Check if entity is valid
    if not entity.has("name"):
        ctx.log.warning("Person without name", id=entity.id, row=ix)
        return

    yield entity
```

## Text processing

### Normalization

Clean text data before adding to entities:

```python
from normality import slugify, squash_spaces

def handle(ctx, record, ix):
    entity = ctx.make_entity("Organization")

    # Remove extra whitespace
    name = squash_spaces(record["name"])
    entity.add("name", name)

    # Generate consistent slugs
    entity.id = ctx.make_slug(slugify(record["id"]))

    yield entity
```

### Language handling

Preserve original language when available:

```python
# FollowTheMoney supports language-tagged values
entity.add("name", record["name_en"], lang="eng")
entity.add("name", record["name_de"], lang="deu")
```

## Creating relationships

### Direct relationships

Link entities with relationship schemas:

```python
def handle(ctx, record, ix):
    # Create entities
    person = ctx.make_entity("Person")
    person.id = ctx.make_slug("person", record["person_id"])
    person.add("name", record["person_name"])

    company = ctx.make_entity("Company")
    company.id = ctx.make_slug("company", record["company_id"])
    company.add("name", record["company_name"])

    # Create ownership
    ownership = ctx.make_entity("Ownership")
    ownership.id = ctx.make_id(person.id, "owns", company.id)
    ownership.add("owner", person)
    ownership.add("asset", company)
    ownership.add("startDate", record.get("acquired_date"))
    ownership.add("percentage", record.get("stake"))

    yield person
    yield company
    yield ownership
```

### Family relationships

```python
def handle(ctx, record, ix):
    person1 = ctx.make_entity("Person")
    person1.id = ctx.make_slug("person", record["person1_id"])
    person1.add("name", record["person1_name"])

    person2 = ctx.make_entity("Person")
    person2.id = ctx.make_slug("person", record["person2_id"])
    person2.add("name", record["person2_name"])

    family = ctx.make_entity("Family")
    family.id = ctx.make_id(person1.id, "family", person2.id)
    family.add("person", person1)
    family.add("relative", person2)
    family.add("relationship", record["relationship_type"])

    yield person1
    yield person2
    yield family
```

## Conditional entity creation

### Skip records based on conditions

```python
def handle(ctx, record, ix):
    # Skip test records
    if record.get("status") == "TEST":
        return

    # Skip records without required data
    if not record.get("name") or not record.get("id"):
        ctx.log.warning("Skipping incomplete record", row=ix)
        return

    entity = ctx.make_entity("Organization")
    entity.id = ctx.make_slug(record["id"])
    entity.add("name", record["name"])

    yield entity
```

### Different schemas based on data

```python
def handle(ctx, record, ix):
    # Choose schema based on entity type
    entity_type = record.get("type", "").lower()

    if entity_type == "person":
        entity = ctx.make_entity("Person")
        entity.id = ctx.make_slug("person", record["id"])
        entity.add("name", record["name"])
        entity.add("birthDate", record.get("birth_date"))
    elif entity_type == "company":
        entity = ctx.make_entity("Company")
        entity.id = ctx.make_slug("company", record["id"])
        entity.add("name", record["name"])
        entity.add("incorporationDate", record.get("founded_date"))
    else:
        ctx.log.warning("Unknown entity type", type=entity_type, row=ix)
        return

    yield entity
```

## Caching within transforms

Cache computed values when processing related records:

```python
def handle(ctx, record, ix):
    task_ctx = ctx.task()

    # Cache organization IDs to avoid recomputation
    if record["org_id"] not in task_ctx.data:
        org = make_organization(task_ctx, record)
        task_ctx.data[record["org_id"]] = org.id
        task_ctx.emit(org)

    # Use cached ID
    person = make_person(task_ctx, record)
    membership = make_membership(
        task_ctx,
        person.id,
        task_ctx.data[record["org_id"]],
        record
    )

    yield from task_ctx


def make_organization(task_ctx, record):
    org = task_ctx.make_entity("Organization")
    org.id = task_ctx.make_slug("org", record["org_id"])
    org.add("name", record["org_name"])
    return org


def make_person(task_ctx, record):
    person = task_ctx.make_entity("Person")
    person.id = task_ctx.make_slug("person", record["person_id"])
    person.add("name", record["person_name"])
    return person


def make_membership(task_ctx, person_id, org_id, record):
    membership = task_ctx.make_entity("Membership")
    membership.id = task_ctx.make_id(person_id, "member", org_id)
    membership.add("member", person_id)
    membership.add("organization", org_id)
    membership.add("role", record.get("role"))
    return membership
```

## Performance optimization

### Memory management

Yield entities as you create them rather than accumulating:

```python
def handle(ctx, record, ix):
    # Don't do this - accumulates in memory
    # entities = []
    # for item in large_list:
    #     entities.append(make_entity(ctx, item))
    # return entities

    # Do this - yields immediately
    for item in parse_items(record):
        yield make_entity(ctx, item)
```

### Batch logging

For large datasets, log progress periodically:

```python
def handle(ctx, record, ix):
    # Log progress every 1000 records
    if ix % 1000 == 0:
        ctx.log.info("Progress", records_processed=ix)

    entity = ctx.make_entity("Organization")
    entity.id = ctx.make_slug(record["id"])
    entity.add("name", record["name"])

    yield entity
```

## Custom extract handlers

For sources beyond simple CSV/Excel:

```python
def handle(ctx):
    """Custom extract handler"""
    with ctx.open() as fh:
        # Parse custom format
        for line in fh:
            if line.startswith("#"):
                continue  # skip comments

            parts = line.strip().split("|")
            yield {
                "id": parts[0],
                "name": parts[1],
                "type": parts[2],
            }
```

### API pagination

Handle paginated APIs in extract stage:

```python
def handle(ctx):
    """Extract from paginated API"""
    import requests

    page = 1
    while True:
        resp = requests.get(
            ctx.source.uri,
            params={"page": page, "limit": 100}
        )
        resp.raise_for_status()
        data = resp.json()

        if not data["results"]:
            break

        for item in data["results"]:
            yield item

        page += 1
```

## Complex entity composition

### Building composite entities

Create complex entities from multiple record types:

```python
from ftmq.util import make_fingerprint
from followthemoney.util import make_entity_id

def parse_record(ctx, data: dict, body: StatementEntity):
    """Parse record and create related entities"""
    # Create persons from comma-separated lists
    involved = []
    for name, role in zip_things(
        data.pop("names"),
        data.pop("roles", ""),
        scream=True
    ):
        person = ctx.make_entity("Person")
        person.id = ctx.make_slug("person", make_entity_id(body.id, make_fingerprint(name)))
        person.add("name", name)
        person.add("description", role)
        involved.append(person)
        yield person

    # Create memberships
    for member in involved:
        membership = ctx.make_entity("Membership")
        membership.id = ctx.make_slug("membership", make_entity_id(body.id, member.id))
        membership.add("organization", body)
        membership.add("member", member)
        membership.add("role", member.get("description"))
        yield membership


def handle(ctx, record, ix):
    # Create main organization
    body = ctx.make_entity("PublicBody")
    body.id = ctx.make_slug(make_fingerprint(record.pop("name")))
    body.add("name", record["name"])
    body.add("jurisdiction", "eu")

    yield body
    yield from parse_record(ctx, record, body)
```

### Conditional parsing

Route records to different parsers based on source:

```python
from ftmq.util import make_fingerprint

def parse_record_ec(ctx, data: dict):
    """Parse EC representative meetings"""
    name = data.pop("cabinet_name")
    id_ = ctx.make_slug(make_fingerprint(name))
    body = ctx.make_entity("PublicBody", id_)
    body.add("name", name)
    body.add("jurisdiction", "eu")

    yield body
    yield from parse_common(ctx, data, body)


def parse_record_dg(ctx, data: dict):
    """Parse Director-General meetings"""
    acronym = data.pop("dg_acronym")
    id_ = ctx.make_slug("dg", acronym)
    body = ctx.make_entity("PublicBody", id_)
    body.add("name", data.pop("dg_full_name"))
    body.add("weakAlias", acronym)
    body.add("jurisdiction", "eu")

    yield body
    yield from parse_common(ctx, data, body)


def handle(ctx, record, ix):
    # Route based on source name
    if ctx.source.name.startswith("ec"):
        handler = parse_record_ec
    else:
        handler = parse_record_dg

    yield from handler(ctx, record)
```

### Using entity captions

Use entity captions for building descriptions:

```python
from followthemoney.util import join_text

def handle(ctx, record, ix):
    # Create participants
    participants = []
    for name in record["participant_names"].split(","):
        person = ctx.make_entity("Person")
        person.id = ctx.make_fingerprint_id(name.strip())
        person.add("name", name.strip())
        participants.append(person)

    # Create event with participant names in description
    event = ctx.make_entity("Event")
    event.id = ctx.make_slug("event", record["event_id"])

    # Use entity captions to build readable name
    label = join_text(*[p.caption for p in participants])
    event.add("name", f"{record['date']} - {label}")
    event.add("date", record["date"])

    # Add participants
    for p in participants:
        event.add("involved", p)

    yield from participants
    yield event
```

## Configuration patterns

### Organize transform queries logically

```yaml
transform:
  queries:
    # Primary entities first
    - entities:
        person:
          schema: Person
          keys: [person_id]
          properties:
            name:
              column: person_name

    # Related entities second
    - entities:
        company:
          schema: Company
          keys: [company_id]
          properties:
            name:
              column: company_name

    # Relationships last
    - entities:
        ownership:
          schema: Ownership
          keys: [person_id, company_id]
          properties:
            owner:
              entity: person
            asset:
              entity: company
```

## Real-world examples

### EC Meetings dataset

Transform meeting records with organizations and representatives:

```python
from ftmq.util import make_fingerprint
from followthemoney.util import join_text, make_entity_id

def handle(ctx, record, ix):
    # Create organizing body
    body = ctx.make_entity("PublicBody")
    body.id = ctx.make_slug(make_fingerprint(record["cabinet_name"]))
    body.add("name", record["cabinet_name"])

    # Create organizations from transparency register
    orgs = []
    for name, regId in zip_things(
        record["org_names"],
        record["transparency_ids"]
    ):
        org = ctx.make_entity("Organization")
        org.id = ctx.make_slug(regId, prefix="eu-tr")
        if make_fingerprint(name):
            org.add("name", name)
        org.add("idNumber", regId)
        orgs.append(org)

    # Create persons
    persons = []
    for name, role in zip_things(
        record["ec_rep_names"],
        record["ec_rep_titles"]
    ):
        person = ctx.make_entity("Person")
        person.id = ctx.make_slug("person", make_entity_id(body.id, make_fingerprint(name)))
        person.add("name", name)
        person.add("description", role)
        persons.append(person)

    # Create meeting event
    event = ctx.make_entity("Event")
    org_label = join_text(*[o.first("name") for o in orgs])
    event.id = ctx.make_slug(
        "meeting",
        record["date"],
        make_entity_id(body.id, *sorted([o.id for o in orgs]))
    )
    event.add("name", f"{record['date']} - {body.caption} x {org_label}")
    event.add("date", record["date"])
    event.add("summary", record["subject"])
    event.add("organizer", body)
    event.add("involved", persons)
    event.add("involved", orgs)

    yield body
    yield from orgs
    yield from persons
    yield event
```

## Further reading

- [Entity keys and IDs](keys.md) - ID generation strategies
- [Utility functions](utils.md) - Context helpers and advanced patterns
- [Context API reference](../reference/context.md) - Available methods
- [Transform stage](../stages/transform.md) - Transform configuration
