from typing import Any, Generator, TypeAlias

Record: TypeAlias = dict[str, Any]
"""A string keyed dict"""

RecordGenerator: TypeAlias = Generator[Record, None, None]
"""A generator of [records][investigraph.types.Record]"""
