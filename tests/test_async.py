import asyncio
from types import GeneratorType
from unittest.mock import AsyncMock

from zyte_api import AsyncZyteAPI
from zyte_api.apikey import NoApiKey

import pytest


def test_api_key():
    AsyncZyteAPI(api_key="a")
    with pytest.raises(NoApiKey):
        AsyncZyteAPI()


@pytest.mark.asyncio
async def test_get(mockserver):
    client = AsyncZyteAPI(api_key="a", api_url=mockserver.urljoin("/"))
    expected_result = {"url": "https://a.example", "httpResponseBody": "PGh0bWw+PGJvZHk+SGVsbG88aDE+V29ybGQhPC9oMT48L2JvZHk+PC9odG1sPg=="}
    actual_result = await client.get({"url": "https://a.example", "httpResponseBody": True})
    assert actual_result == expected_result


@pytest.mark.asyncio
async def test_iter(mockserver):
    client = AsyncZyteAPI(api_key="a", api_url=mockserver.urljoin("/"))
    queries = [
        {"url": "https://a.example", "httpResponseBody": True},
        {"url": "https://exception.example", "httpResponseBody": True},
        {"url": "https://b.example", "httpResponseBody": True},
    ]
    expected_results = [
        {"url": "https://a.example", "httpResponseBody": "PGh0bWw+PGJvZHk+SGVsbG88aDE+V29ybGQhPC9oMT48L2JvZHk+PC9odG1sPg=="},
        Exception,
        {"url": "https://b.example", "httpResponseBody": "PGh0bWw+PGJvZHk+SGVsbG88aDE+V29ybGQhPC9oMT48L2JvZHk+PC9odG1sPg=="},
    ]
    actual_results = []
    for future in client.iter(queries):
        try:
            actual_result = await future
        except Exception as exception:
            actual_result = exception
        actual_results.append(actual_result)
    assert len(actual_results) == len(expected_results)
    for actual_result in actual_results:
        if isinstance(actual_result, Exception):
            assert Exception in expected_results
        else:
            assert actual_result in expected_results


@pytest.mark.asyncio
async def test_semaphore(mockserver):
    client = AsyncZyteAPI(api_key="a", api_url=mockserver.urljoin("/"))
    client._semaphore = AsyncMock(wraps=client._semaphore)
    queries = [
        {"url": "https://a.example", "httpResponseBody": True},
        {"url": "https://b.example", "httpResponseBody": True},
        {"url": "https://c.example", "httpResponseBody": True},
    ]
    futures = [
        client.get(queries[0]),
        next(iter(client.iter(queries[1:2]))),
        client.get(queries[2]),
    ]
    for future in asyncio.as_completed(futures):
        actual_result = await future
    assert client._semaphore.__aenter__.call_count == len(queries)
    assert client._semaphore.__aexit__.call_count == len(queries)
