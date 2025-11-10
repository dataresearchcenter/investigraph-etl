# thanks, zavod: https://zavod.opensanctions.org/helpers/#zavod.helpers.make_address

from typing import Optional

from followthemoney import StatementEntity, registry
from ftmq.util import lru_cache
from rigour.addresses import format_address_line

from investigraph.model import SourceContext
from investigraph.util import join_text


@lru_cache(maxsize=10000)
def format_address(
    summary: Optional[str] = None,
    po_box: Optional[str] = None,
    street: Optional[str] = None,
    street2: Optional[str] = None,
    street3: Optional[str] = None,
    house: Optional[str] = None,
    house_number: Optional[str] = None,
    postal_code: Optional[str] = None,
    city: Optional[str] = None,
    county: Optional[str] = None,
    state: Optional[str] = None,
    state_district: Optional[str] = None,
    state_code: Optional[str] = None,
    country: Optional[str] = None,
    country_code: Optional[str] = None,
) -> str:
    """Given the components of a postal address, format it into a single line
    using some country-specific templating logic.

    Args:
        summary: A short description of the address.
        po_box: The PO box/mailbox number.
        street: The street or road name.
        street2: The street or road name, line 2.
        street3: The street or road name, line 3.
        house: The descriptive name of the house.
        house_number: The number of the house on the street.
        postal_code: The postal code or ZIP code.
        city: The city or town name.
        county: The county or district name.
        state: The state or province name.
        state_district: The state or province district name.
        state_code: The state or province code.
        country: The name of the country (words, not ISO code).
        country_code: A pre-normalized country code.

    Returns:
        A single-line string with the formatted address."""
    if country_code is None and country is not None:
        country_code = registry.country.clean_text(country)
    street = join_text(street, street2, street3, sep=", ")
    data = {
        "attention": summary,
        "road": street,
        "house": po_box or house,
        "house_number": house_number,
        "postcode": postal_code,
        "city": city,
        "county": county,
        "state": state,
        "state_district": state_district,
        "state_code": state_code,
        "country": country,
    }
    return format_address_line(data, country=country_code)


def make_address(
    context: SourceContext,
    full: Optional[str] = None,
    remarks: Optional[str] = None,
    summary: Optional[str] = None,
    po_box: Optional[str] = None,
    street: Optional[str] = None,
    street2: Optional[str] = None,
    street3: Optional[str] = None,
    city: Optional[str] = None,
    place: Optional[str] = None,
    postal_code: Optional[str] = None,
    state: Optional[str] = None,
    region: Optional[str] = None,
    country: Optional[str] = None,
    country_code: Optional[str] = None,
    key: Optional[str] = None,
    lang: Optional[str] = None,
) -> Optional[StatementEntity]:
    """Generate an address schema object adjacent to the main entity.

    Args:
        context: The runner context used for making and emitting entities.
        full: The full address as a single string.
        remarks: Delivery remarks for the address.
        summary: A short description of the address.
        po_box: The PO box/mailbox number.
        street: The street or road name.
        street2: The street or road name, line 2.
        street3: The street or road name, line 3.
        city: The city or town name.
        place: The name of a smaller locality (same as city).
        postal_code: The postal code or ZIP code.
        state: The state or province name.
        region: The region or district name.
        country: The country name (words, not ISO code).
        country_code: A pre-normalized country code.
        key: An optional key to be included in the ID of the address.
        lang: The language of the address details.

    Returns:
        A new entity of type `Address`."""
    city = join_text(place, city, sep=", ")
    street = join_text(street, street2, street3, sep=", ")

    # This is meant to handle cases where the country field contains a country code
    # in a subset of the given records:
    if country is not None and len(country.strip()) == 2:
        context.log.warn(
            "Country name looks like a country code",
            country=country,
            country_code=country_code,
        )
        if country_code is None:
            country_code = country
            country = None

    if country is not None:
        parsed_code = registry.country.clean(country)
        if parsed_code is not None:
            if country_code is not None and country_code != parsed_code:
                context.log.warn(
                    "Country code mismatch",
                    country=country,
                    country_code=country_code,
                )
            country_code = parsed_code

    if country_code is None:
        country_code = registry.country.clean(full)

    if not full:
        full = format_address(
            summary=summary,
            po_box=po_box,
            street=street,
            postal_code=postal_code,
            city=city,
            state=state,
            state_district=join_text(region, state, sep=", "),
            country=country,
            country_code=country_code,
        )

    if full == country:
        full = None

    address = context.make_entity("Address")
    try:
        address.id = context.make_fingerprint_id(full, prefix=f"addr-{country_code}")
    except ValueError:
        return

    address.add("full", full, lang=lang)
    address.add("remarks", remarks, lang=lang)
    address.add("summary", summary, lang=lang)
    address.add("postOfficeBox", po_box, lang=lang)
    address.add("street", street, lang=lang)
    address.add("city", city, lang=lang)
    address.add("postalCode", postal_code, lang=lang)
    address.add("region", region, lang=lang)
    address.add("state", state, quiet=True, lang=lang)
    address.add("country", country_code, lang=lang, original_value=country)
    return address


def assign_address(entity: StatementEntity, address: StatementEntity | None) -> None:
    """Assign an Address entity to a given Entity. This sets `address` property
    to the "full" property of the Address, assigns countries and sets
    `addressEntity`.

    Args:
        entity: Any Entity that can have an address assigned to it
        address: The Address entity

    Examples:
        ```python
        from investigraph.helpers.addresses import assign_address

        assign_addres(entity, address)
        ```

    Returns: None
    """
    if address is not None:
        entity.add("address", address.caption)
        entity.add("addressEntity", address)
        entity.add("country", address.countries)
