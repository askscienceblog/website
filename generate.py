import base64
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Annotated, Callable

from bs4 import BeautifulSoup
from jinja2 import Environment, FunctionLoader, StrictUndefined
from markupsafe import Markup
from pydantic import BaseModel, Field
from slugify import slugify

CONFIG_JSON = re.compile(r"{#(?:\+|-)*\s*({.*?})\s*(?:\+|-)*#}", re.DOTALL)
STOPWORDS = [
    "i",
    "me",
    "my",
    "myself",
    "we",
    "our",
    "ours",
    "ourselves",
    "you",
    "your",
    "yours",
    "yourself",
    "yourselves",
    "he",
    "him",
    "his",
    "himself",
    "she",
    "her",
    "hers",
    "herself",
    "it",
    "its",
    "itself",
    "they",
    "them",
    "their",
    "theirs",
    "themselves",
    "what",
    "which",
    "who",
    "whom",
    "this",
    "that",
    "these",
    "those",
    "am",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "having",
    "do",
    "does",
    "did",
    "doing",
    "a",
    "an",
    "the",
    "and",
    "but",
    "if",
    "or",
    "because",
    "as",
    "until",
    "while",
    "of",
    "at",
    "by",
    "for",
    "with",
    "about",
    "against",
    "between",
    "into",
    "through",
    "during",
    "before",
    "after",
    "above",
    "below",
    "to",
    "from",
    "up",
    "down",
    "in",
    "out",
    "on",
    "off",
    "over",
    "under",
    "again",
    "further",
    "then",
    "once",
    "here",
    "there",
    "when",
    "where",
    "why",
    "how",
    "all",
    "any",
    "both",
    "each",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "no",
    "nor",
    "not",
    "only",
    "own",
    "same",
    "so",
    "than",
    "too",
    "very",
    "s",
    "t",
    "can",
    "will",
    "just",
    "don",
    "should",
    "now",
]


class RenderVariable(BaseModel):
    namespace: str
    path: Path


class TemplateOptions(BaseModel):
    read_from: Path | None = None
    write_to: list[Annotated[str, Field(pattern=r"[a-zA-Z0-9.\-_~]*")]] = []
    file_extension: str = Field(default="", pattern=r"^$|^\..*")
    variables: list[RenderVariable] = []
    slug_from: str = "title"
    clear_previous: bool = False


def load_from_path(path: str) -> str:
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


env = Environment(
    loader=FunctionLoader(load_from_path), autoescape=True, undefined=StrictUndefined
)


def render_template(
    template_path: str,
    output_dir: str,
    post_processing: Callable[[str], str] = lambda x: x,
) -> None:
    # load config
    with open(template_path, "r") as file:
        template = file.read()
    mat = CONFIG_JSON.search(template)
    if mat is None:
        mat = r"{}"
    else:
        mat = mat.group(1)

    options = TemplateOptions.model_validate_json(mat)
    if options.read_from is None:  # return if no need to render
        return

    var = {}
    for vars in options.variables:
        with vars.path.open("r", encoding="utf-8") as file:
            var[vars.namespace] = json.load(file)

    for entry in os.scandir(options.read_from):
        if not entry.is_file():
            continue

        with open(entry, "r", encoding="utf-8") as file:
            var.update(json.load(file))

        filename = (
            slugify(
                var[options.slug_from],
                stopwords=STOPWORDS,
            )
            + options.file_extension
        )
        output = env.get_template(template_path).render(**var)
        os.makedirs(os.path.join(output_dir, *options.write_to), exist_ok=True)
        if options.clear_previous:
            for entry in os.scandir(os.path.join(output_dir, *options.write_to)):
                if entry.is_file():
                    os.remove(entry)

        with Path(output_dir, *options.write_to, filename).open(
            "w", encoding="utf-8"
        ) as file:
            file.write(post_processing(output))


def pandoc(
    value,
    arguments=["-f", "markdown", "-t", "html"],
):
    res = subprocess.run(
        ["pandoc"] + arguments,
        capture_output=True,
        text=True,
        encoding="utf-8",
        input=value,
    )
    print(res.stderr)
    return Markup(res.stdout)


env.filters["pandoc"] = pandoc


def censor_addresses(html: str) -> str:
    soup = BeautifulSoup(html, "html5lib")
    for address in soup.find_all("address"):
        inner_html = address.encode_contents(encoding="utf-8")
        address.string = (
            "Contact information is protected. Please enable JavaScript to view."
        )
        address["enc-addr"] = base64.b64encode(base64.b64encode(inner_html)).decode(
            "utf-8"
        )

    return str(soup)


if __name__ == "__main__":
    for entry in os.scandir("templates"):
        if entry.is_file():
            render_template(entry.path, "public", censor_addresses)
