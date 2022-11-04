import logging
from enum import StrEnum

from exceptions import NewspyException
from http_client import HttpMethod, HttpClient
from models import (
    Publication,
    ArticlesRes,
    Category,
    Language,
    Country,
    ArticleSourceRes,
    Source,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://newsapi.org/v2"


class NewsapiEndpoint(StrEnum):
    EVERYTHING = "EVERYTHING"
    TOP_HEADLINES = "TOP_HEADLINES"
    SOURCES = "SOURCES"


def _create_url(endpoint: NewsapiEndpoint) -> str:
    match endpoint:
        case NewsapiEndpoint.EVERYTHING:
            return f"{BASE_URL}/everything"
        case NewsapiEndpoint.TOP_HEADLINES:
            return f"{BASE_URL}/top-headlines"
        case NewsapiEndpoint.SOURCES:
            return f"{BASE_URL}/top-headlines/sources"
        case _:
            raise NewspyException(
                status_code=400,
                msg=f"The endpoint has to be one of the following values: 'EVERYTHING' or 'TOP_HEADLINES' or 'SOURCES'",
            )


class NewsapiClient:
    def __init__(self, http_client: HttpClient, api_key: str) -> None:
        self._http_client = http_client
        self._api_key = api_key

    def fetch_publications(
        self,
        endpoint: NewsapiEndpoint,
        search_text: str,
        category: Category | None = None,
        country: Country | None = None,
        sources: list[Source] | None = None,
    ) -> list[Publication]:
        if category and sources:
            raise NewspyException(
                status_code=400,
                msg="Choose either the category and sources attributes. Not both.",
            )

        params = {"apiKey": self._api_key, "pageSize": 100, "page": 1}

        if search_text:
            params["q"] = search_text
        if category and endpoint == NewsapiEndpoint.TOP_HEADLINES:
            params["category"] = category.value
        if country and endpoint == NewsapiEndpoint.TOP_HEADLINES:
            params["country"] = country.value
        if sources and len(sources) > 0:
            params["sources"] = [source.id for source in sources]

        resp_json = self._http_client.send(
            method=HttpMethod.GET, url=_create_url(endpoint=endpoint), params=params
        )

        publications = []
        article_res = ArticlesRes.parse_obj(resp_json)
        for article in article_res.articles:
            publications.append(article.to_publications())

        return publications

    def fetch_sources(
        self,
        endpoint=NewsapiEndpoint.SOURCES,
        category: Category | None = None,
        language: Language | None = None,
        country: Country | None = None,
    ) -> list[str]:
        params = {"apiKey": self._api_key}

        if category:
            params["category"] = category.value
        if language:
            params["language"] = language.value
        if country:
            params["country"] = country.value

        resp_json = self._http_client.send(
            method=HttpMethod.GET, url=_create_url(endpoint=endpoint), params=params
        )

        sources = []
        source_res = ArticleSourceRes.parse_obj(resp_json)
        for source in source_res.sources:
            if source.id:
                sources.append(source.id)

        return sources
