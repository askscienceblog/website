from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, NonNegativeInt, StringConstraints


class Author(BaseModel):
    given_name: str | None
    surname: str
    suffix: str | None
    orcid: (
        Annotated[
            str,
            StringConstraints(
                pattern=r"https?://orcid.org/[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{3}[X0-9]{1}"
            ),
        ]
        | None
    )
    sequence: Literal["first", "additional"]
    name_style: Literal["western", "eastern", "islensk", "given-only"]

    def __str__(self) -> str:
        match self.name_style:
            case "western" | "islensk":
                return (
                    (self.given_name + " " if self.given_name is not None else "")
                    + self.surname
                    + (" " + self.suffix if self.suffix is not None else "")
                )
            case "eastern":
                return (
                    self.surname
                    + (" " + self.given_name if self.given_name is not None else "")
                    + (" " + self.suffix if self.suffix is not None else "")
                )
            case "given-only":
                return self.given_name if self.given_name is not None else ""


class Abstract(BaseModel):
    type: str | None
    paragraphs: list[str]


class Update(BaseModel):
    doi: Annotated[str, StringConstraints(pattern=r"10\.[0-9]{4,9}/.{1,200}")]
    date: date
    type: Literal[
        "addendum",
        "clarification",
        "correction",
        "corrigendum",
        "erratum",
        "expression_of_concern",
        "new_edition",
        "new_version",
        "partial_retraction",
        "removal",
        "retraction",
        "withdrawal",
    ]


class Crossmark(BaseModel):
    updates: list[Update]


class DoiData(BaseModel):
    doi: Annotated[str, StringConstraints(pattern=r"10\.[0-9]{4,9}/.{1,200}")]
    timestamp: NonNegativeInt
    resource: Annotated[
        str,
        StringConstraints(
            pattern="([hH][tT][tT][pP]|[hH][tT][tT][pP][sS]|[fF][tT][pP])://.*"
        ),
    ]


class Citation(BaseModel):
    xml_data: str


class Article(BaseModel):
    title: str
    contributors: list[Author]
    abstract: Abstract
    publication_date: date
    crossmark: Crossmark | None
    doi_data: DoiData
    citations: list[Citation]


class DoiBatch(BaseModel):
    batch_id: Annotated[str, StringConstraints(min_length=4, max_length=100)]
    timestamp: NonNegativeInt
    articles: list[Article]
