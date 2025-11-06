# Dataset metadata

This guide covers best practices for writing excellent dataset metadata. Good metadata demonstrates transparency, helps users understand your data, and makes datasets discoverable.

## Why metadata matters

Dataset metadata serves multiple audiences:

- **Developers** - Need technical details about data structure and updates
- **Journalists** - Need context about what the data contains
- **Researchers** - Need to understand scope, coverage, and limitations
- **International users** - May be unfamiliar with the source country's systems

Good metadata is a low-effort way to demonstrate data provenance and build trust.

## Required fields

### `name` (required)

Dataset identifier as a slug. Use lowercase with underscores or hyphens.

```yaml
name: eu_sanctions
```

**Guidelines:**

- Use clear, descriptive names
- Include country/region prefix for regional datasets
- Keep it short but meaningful

**Examples:**

- `gb_companies_house` - UK company register
- `us_ofac_sdn` - US sanctions list
- `eu_transparency_register` - EU lobbying register

### `title` (required)

Human-readable title of the dataset.

```yaml
title: EU Financial Sanctions
```

**Guidelines:**

- Use official name when available
- Note any subsets or limitations in parentheses
- Capitalize properly

**Examples:**

- `European Commission - Meetings with interest representatives`
- `UK Companies House (Active companies only)`
- `OFAC Specially Designated Nationals`

### `prefix`

Short identifier used for entity IDs. If not specified, uses `name`.

```yaml
prefix: eu-sanctions
```

**Guidelines:**

- Keep it short (2-10 characters)
- Use hyphens for readability
- Make it unique across your catalog
- Consider using country codes (ISO 3166-1 Alpha-2)

**Examples:**

- `gb-coh` - Great Britain Companies House
- `ofac` - Office of Foreign Assets Control
- `eu-tr` - EU Transparency Register

## Descriptive fields

### `summary`

Single clear sentence describing the dataset. Appears in search results.

```yaml
summary: |
  EU financial sanctions against individuals and entities involved in
  activities threatening international peace and security.
```

**Guidelines:**

- One to two sentences maximum
- Explain what users need to know first
- Focus on who/what is in the dataset
- Avoid jargon

**Examples:**
```yaml
# Good
summary: |
  List of individuals and organizations sanctioned by the European Union
  for involvement in terrorism, human rights violations, and other activities.

# Too vague
summary: EU sanctions data

# Too technical
summary: |
  CFSP sanctions extracted from the consolidated XML feed published by
  the European External Action Service.
```

### `description`

Detailed explanation of the dataset (1-3 paragraphs).

```yaml
description: |
  The EU Financial Sanctions list contains individuals, entities, and vessels
  subject to restrictive measures imposed by the European Union. Sanctions are
  imposed for various reasons including terrorism, human rights violations,
  and threats to international peace and security.

  The dataset includes names, dates of birth, addresses, and identification
  numbers where available. It is updated regularly as the EU adds, modifies,
  or removes sanctions.

  This dataset is published by the European External Action Service (EEAS)
  and represents the consolidated EU sanctions regime.
```

**Guidelines:**

- First paragraph: What the dataset contains
- Second paragraph: What data fields are included
- Third paragraph: Update frequency and source authority
- Explain inclusions and exclusions
- Note any data quality issues
- Provide context for international users

### `url`

Link to authoritative source documentation or homepage.

```yaml
url: https://www.opensanctions.org/datasets/eu_fsf/
```

**Guidelines:**

- Link to official source when possible
- Prefer documentation over raw data URLs
- Use stable, permanent URLs

## Publisher information

### `publisher`

Information about the organization that publishes the source data.

```yaml
publisher:
  name: European External Action Service
  description: |
    The EEAS is the diplomatic service of the European Union, responsible
    for the Common Foreign and Security Policy including sanctions.
  url: https://eeas.europa.eu
  country: eu
  official: true
```

**Fields:**

- `name` (required) - Official name in original language
- `description` - Who they are and why they publish this data
- `url` - Official website
- `country` - ISO 3166-1 Alpha-2 country code
- `official` - Boolean indicating if it's a government source

**Guidelines:**

- Use official name from the source
- Explain the publisher's role/authority
- Note if it's an official government source
- For international audiences, explain the organization

### `maintainer`

Information about who maintains this dataset implementation.

```yaml
maintainer:
  name: Data Research Center
  url: https://dataresearchcenter.org
```

**Use when:**

- You're re-publishing someone else's data
- Multiple organizations are involved
- You want to distinguish source from implementation

## Coverage information

### `frequency`

How often the dataset is updated.

```yaml
frequency: daily
```

**Values:**

- `daily` - Updated every day
- `weekly` - Updated weekly
- `monthly` - Updated monthly
- `quarterly` - Updated quarterly
- `annually` - Updated yearly
- `never` - Historical/archived dataset

### Temporal coverage

For time-limited datasets, specify the date range.

```yaml
coverage:
  start: "2020-01-01"
  end: "2023-12-31"
```

**Use for:**

- Historical datasets
- Time-limited data collections
- Archived snapshots

**Format:** ISO 8601 dates (YYYY-MM-DD)

## Resources

List of data resources (output files).

```yaml
resources:
  - name: entities.ftm.json
    url: https://data.ftm.store/eu_sanctions/entities.ftm.json
    mime_type: application/json+ftm
```

**Fields:**

- `name` - Filename
- `url` - Download URL
- `mime_type` - MIME type

**Common MIME types:**

- `application/json+ftm` - FollowTheMoney JSON
- `application/json` - Generic JSON
- `text/csv` - CSV files

## License and legal

### `license`

License identifier for the dataset.

```yaml
license: CC-BY-4.0
```

**Common licenses:**

- `CC0-1.0` - Public domain
- `CC-BY-4.0` - Attribution required
- `ODbL-1.0` - Open Database License
- `other-pd` - Other public domain
- `other-open` - Other open license

**Guidelines:**

- Use SPDX identifiers when possible
- Check source data license
- Be conservative if unclear

## Tags and categorization

### `category`

Dataset category.

```yaml
category: sanctions
```

**Common categories:**

- `sanctions` - Sanctions lists
- `crime` - Crime and law enforcement
- `corp` - Corporate data
- `role.pep` - Politically exposed persons
- `gov` - Government data
- `finance` - Financial data

### `tags`

Additional categorization tags.

```yaml
tags:
  - sanctions
  - eu
  - terrorism
  - human-rights
```

**Guidelines:**

- Use lowercase
- Use hyphens for multi-word tags
- Be specific
- Include geographic tags
- Include topic tags

## Technical metadata

### `version`

Dataset version.

```yaml
version: "2024.01.15"
```

**Formats:**

- Date-based: `YYYY.MM.DD`
- Semantic: `1.2.3`
- Incremental: `v1`, `v2`

### `updated_at`

Last update timestamp.

```yaml
updated_at: "2024-01-15T10:30:00Z"
```

**Format:** ISO 8601 with timezone (UTC recommended)

## Complete example

```yaml
name: eu_fsf
title: EU Financial Sanctions
prefix: eu-sanctions

summary: |
  Individuals and entities subject to European Union financial sanctions for
  terrorism, human rights violations, and threats to international peace.

description: |
  The EU Financial Sanctions list contains individuals, entities, and vessels
  subject to restrictive measures imposed by the European Union. Sanctions are
  imposed for various reasons including terrorism, human rights violations,
  undermining democracy, and threats to international peace and security.

  The dataset includes names, dates of birth, nationalities, addresses, and
  identification numbers where available. Relationships between individuals
  and entities are captured when explicitly stated in the source data.

  This dataset is published by the European External Action Service (EEAS)
  and represents the consolidated EU sanctions regime across all member states.
  It is updated regularly, typically within 24 hours of any changes to EU
  sanctions measures.

url: https://www.opensanctions.org/datasets/eu_fsf/

publisher:
  name: European External Action Service
  description: |
    The European External Action Service (EEAS) is the diplomatic service
    of the European Union, responsible for implementing the Common Foreign
    and Security Policy including the EU sanctions regime.
  url: https://eeas.europa.eu
  country: eu
  official: true

maintainer:
  name: OpenSanctions
  url: https://opensanctions.org

frequency: daily

category: sanctions

tags:
  - sanctions
  - eu
  - terrorism
  - human-rights
  - corruption

license: other-open

resources:
  - name: entities.ftm.json
    url: https://data.ftm.store/eu_fsf/entities.ftm.json
    mime_type: application/json+ftm
  - name: index.json
    url: https://data.ftm.store/eu_fsf/index.json
    mime_type: application/json

version: "2024.01.15"

extract:
  sources:
    - uri: https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList/content
      # ... extraction config

transform:
  # ... transformation config
```

## Best practices

### Write for your audience

Consider who will read the metadata:

**For developers:**

- Include technical details about data structure
- Note any data quality issues
- Specify update frequency clearly

**For journalists:**

- Explain what stories the data can tell
- Provide context about the source
- Note any limitations or gaps

**For international users:**

- Don't assume familiarity with local systems
- Explain acronyms and institutions
- Provide context for country-specific data

### Example: Explaining for international users

```yaml
# Less helpful
description: |
  Data from Companies House about UK companies.

# More helpful
description: |
  Companies House is the United Kingdom's official registrar of companies.
  All companies operating in the UK must register with Companies House and
  file annual reports. This dataset contains basic company information
  including names, addresses, directors, and registration details.

  The dataset is updated daily with new company registrations and changes
  to existing companies. Historical dissolved companies are excluded.
```

### Demonstrate transparency

Use metadata to show data provenance:

```yaml
description: |
  This dataset is extracted from the official EU sanctions XML feed
  published by the European External Action Service. Data is processed
  daily and transformed into the FollowTheMoney format for easier analysis.

  Known limitations:
  - Historical sanctions (removed before 2020) are not included
  - Some entity relationships may be inferred from narrative descriptions
  - Address data is often incomplete in the source
```

### Set expectations with assertions

Document expected data ranges to catch anomalies:

```yaml
description: |
  The dataset typically contains 1,500-2,000 sanctioned individuals and
  500-800 sanctioned entities. If the entity count falls outside this range,
  it may indicate a data quality issue.
```

### Keep it current

Update metadata when:

- Source URLs change
- Data structure changes
- Update frequency changes
- You discover limitations
- Source authority changes

## Common mistakes to avoid

### Too vague

```yaml
# Bad
summary: European sanctions data

# Good
summary: |
  EU sanctions against individuals and entities involved in terrorism,
  human rights violations, and threats to international peace.
```

### Too technical

```yaml
# Bad
summary: |
  CFSP sanctions extracted from the consolidated XML feed using XPath
  queries and transformed via the FtM mapping specification.

# Good
summary: |
  EU sanctions list published by the European External Action Service,
  updated daily with information about sanctioned individuals and entities.
```

### Missing context

```yaml
# Bad
publisher:
  name: EEAS
  url: https://eeas.europa.eu

# Good
publisher:
  name: European External Action Service
  description: |
    The EEAS is the EU's diplomatic service, responsible for implementing
    the Common Foreign and Security Policy including sanctions.
  url: https://eeas.europa.eu
  country: eu
```

### Outdated information

```yaml
# Bad - outdated
frequency: daily
description: Updated daily...
# (but hasn't been updated in 6 months)

# Good - accurate
frequency: never
description: |
  Historical snapshot from 2023. This dataset is no longer updated.
  See eu_sanctions_current for the current sanctions list.
```

## Tools for validation

Check metadata completeness:

```bash
# Inspect dataset configuration
investigraph inspect -c datasets/my_dataset/config.yml
```

Validate required fields are present:

- `name` - Dataset identifier
- `title` - Human-readable name
- At least one source in `extract.sources`
- At least one transform query or handler

## Further reading

- [Config reference](../build/config.md) - Full configuration options
- [Dataset concepts](../concepts/dataset.md) - Understanding datasets
- [OpenSanctions metadata guidelines](https://www.opensanctions.org/docs/metadata/) - Original inspiration
- [Dublin Core metadata](https://www.dublincore.org/specifications/dublin-core/) - Metadata standards
