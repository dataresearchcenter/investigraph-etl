from investigraph.model import SourceContext
from investigraph.types import Record


def parse_record(ctx: SourceContext, record: Record, ix: int):
    slug = record.pop("URL name")
    id_ = ctx.make_slug(slug)
    body = ctx.make_entity("PublicBody", id_)
    body.add("name", record.pop("Name"))
    body.add("weakAlias", record.pop("Short name"))
    tags = record.pop("Tags").split()
    body.add("keywords", tags)
    body.add("legalForm", tags)
    body.add("website", record.pop("Home page"))
    body.add("description", record.pop("Notes"))
    body.add("sourceUrl", f"https://www.asktheeu.org/en/body/{slug}")
    body.add("jurisdiction", "eu")
    yield body
