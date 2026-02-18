import base64
import json
import os
import re
import subprocess
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Annotated, Any, Callable, Mapping

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
    raw_slug: bool = True
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
    post_processing: Mapping[str, Callable[[str], str]] = {},
) -> None:
    # load config
    with open(template_path, "r", encoding="utf-8") as file:
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
        if vars.path.is_file():
            with vars.path.open("r", encoding="utf-8") as file:
                var[vars.namespace] = json.load(file)
        if vars.path.is_dir():
            var[vars.namespace] = {}
            for entry in os.scandir(str(vars.path)):
                if entry.is_file():
                    try:
                        with open(entry, "r", encoding="utf-8") as file:
                            var[vars.namespace][entry.name] = json.load(file)
                    except json.JSONDecodeError:
                        pass

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
            if not options.raw_slug
            else var[options.slug_from]
        ) + options.file_extension
        output = env.get_template(template_path).render(**var)
        os.makedirs(os.path.join(output_dir, *options.write_to), exist_ok=True)
        if options.clear_previous:
            for entry in os.scandir(os.path.join(output_dir, *options.write_to)):
                if entry.is_file():
                    os.remove(entry)

        with Path(output_dir, *options.write_to, filename).open(
            "w", encoding="utf-8"
        ) as file:
            if options.file_extension in post_processing:
                out = post_processing[options.file_extension](output)
            else:
                out = output
            file.write(out)


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


def load_json(filepath: str) -> Any:
    with open(filepath, "r", encoding="utf-8") as file:
        return json.load(file)


def parse_iso_date_string(string: str, format: str = ""):
    return datetime.fromisoformat(string).strftime(format)


env.filters["pandoc"] = pandoc
env.filters["load_json"] = load_json
env.filters["slugify"] = partial(slugify, stopwords=STOPWORDS)
env.filters["parse_iso_date"] = parse_iso_date_string


def censor_addresses(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
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
            render_template(entry.path, "public", {".html": censor_addresses})
