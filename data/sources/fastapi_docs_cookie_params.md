---
source_ref_id: fastapi_docs_cookie_params
url_or_locator: https://fastapi.tiangolo.com/tutorial/cookie-params/
provenance: fetch
fetched_at: '2026-09-06T02:25:03+00:00'
char_count: 6796
---

Skip to content

Deploy on FastAPI Cloud 🚀

FastAPI Conf '26 — Oct 28, 2026, Amsterdam 🎤

Follow @fastapi on X (Twitter) to stay updated

Follow FastAPI on LinkedIn to stay updated

Subscribe to the FastAPI and friends newsletter 🎉

sponsor

sponsor

sponsor

sponsor

sponsor

sponsor

sponsor

sponsor

FastAPI

Cookie Parameters

en - English

de - Deutsch

es - español

fr - français

hi - हिन्दी

ja - 日本語

ko - 한국어

pt - português

ru - русский язык

tr - Türkçe

uk - українська мова

zh - 简体中文

zh-hant - 繁體中文

Search

fastapi/fastapi

FastAPI

Features

Learn

Reference

Resources

About

Release Notes

FastAPI

fastapi/fastapi

FastAPI

Features

Learn

Python Types Intro

Concurrency and async / await

Tutorial - User Guide

First Steps

Path Parameters

Query Parameters

Request Body

Query Parameters and String Validations

Path Parameters and Numeric Validations

Query Parameter Models

Body - Multiple Parameters

Body - Fields

Body - Nested Models

Declare Request Example Data

Extra Data Types

Cookie Parameters

Cookie Parameters

On this page

Import Cookie

Declare Cookie parameters

Recap

Header Parameters

Cookie Parameter Models

Header Parameter Models

Response Model - Return Type

Extra Models

Response Status Code

Form Data

Form Models

Request Files

Request Forms and Files

Handling Errors

Path Operation Configuration

JSON Compatible Encoder

Body - Updates

Dependencies

Classes as Dependencies

Sub-dependencies

Dependencies in path operation decorators

Global Dependencies

Dependencies with yield

Security

Security - First Steps

Get Current User

Simple OAuth2 with Password and Bearer

OAuth2 with Password (and hashing), Bearer with JWT tokens

Middleware

CORS (Cross-Origin Resource Sharing)

SQL (Relational) Databases

Bigger Applications - Multiple Files

Stream JSON Lines

Server-Sent Events (SSE)

Background Tasks

Metadata and Docs URLs

Frontend

Static Files

Testing

Debugging

Advanced User Guide

Stream Data

Path Operation Advanced Configuration

Additional Status Codes

Return a Response Directly

Custom Response - HTML, Stream, File, others

Additional Responses in OpenAPI

Response Cookies

Response Headers

Response - Change Status Code

Advanced Dependencies

Advanced Security

OAuth2 scopes

HTTP Basic Auth

Using the Request Directly

Using Dataclasses

Advanced Middleware

Sub Applications - Mounts

Behind a Proxy

Templates

WebSockets

Lifespan Events

Testing WebSockets

Testing Events: lifespan and startup - shutdown

Testing Dependencies with Overrides

Async Tests

Settings and Environment Variables

OpenAPI Callbacks

OpenAPI Webhooks

Including WSGI - Flask, Django, others

Generating SDKs

Advanced Python Types

JSON with Bytes as Base64

Strict Content-Type Checking

FastAPI CLI

Editor Support

Deployment

About FastAPI versions

FastAPI Cloud

About HTTPS

Run a Server Manually

Deployments Concepts

Deploy FastAPI on Cloud Providers

Server Workers - Uvicorn with Workers

FastAPI in Containers - Docker

How To - Recipes

General - How To - Recipes

Migrate from Pydantic v1 to Pydantic v2

GraphQL

Custom Request and APIRoute class

Conditional OpenAPI

Extending OpenAPI

Separate OpenAPI Schemas for Input and Output or Not

Custom Docs UI Static Assets (Self-Hosting)

Configure Swagger UI

Testing a Database

Use Old 403 Authentication Error Status Codes

Reference

FastAPI class

Request Parameters

Status Codes

UploadFile class

Exceptions - HTTPException and WebSocketException

Dependencies - Depends() and Security()

APIRouter class

Background Tasks - BackgroundTasks

Request class

WebSockets

HTTPConnection class

Response class

Custom Response Classes - File, HTML, Redirect, Streaming, etc.

Server-Sent Events - EventSourceResponse and ServerSentEvent

Middleware

OpenAPI

OpenAPI docs

OpenAPI models

Security Tools

Encoders - jsonable_encoder

Static Files - StaticFiles

Templating - Jinja2Templates

Test Client - TestClient

Resources

FastAPI People

Help

Contributing

Translations

Full Stack FastAPI Template

External Links

FastAPI and friends newsletter

About

Alternatives, Inspiration and Comparisons

History, Design and Future

Benchmarks

Repository Management

Release Notes

On this page

Import Cookie

Declare Cookie parameters

Recap

FastAPI

Learn

Tutorial - User Guide

Cookie Parameters¶

You can define Cookie parameters the same way you define Query and Path parameters.

Import Cookie¶

First import Cookie:

Python 3.10+

from typing import Annotated

from fastapi import Cookie, FastAPI

app = FastAPI()

@app.get("/items/")
async def read_items(ads_id: Annotated[str | None, Cookie()] = None):
return {"ads_id": ads_id}

🤓 Other versions and variants

Python 3.10+ - non-Annotated

Tip

Prefer to use the Annotated version if possible.

from fastapi import Cookie, FastAPI

app = FastAPI()

@app.get("/items/")
async def read_items(ads_id: str | None = Cookie(default=None)):
return {"ads_id": ads_id}

Declare Cookie parameters¶

Then declare the cookie parameters using the same structure as with Path and Query.

You can define the default value as well as all the extra validation or annotation parameters:

Python 3.10+

from typing import Annotated

from fastapi import Cookie, FastAPI

app = FastAPI()

@app.get("/items/")
async def read_items(ads_id: Annotated[str | None, Cookie()] = None):
return {"ads_id": ads_id}

🤓 Other versions and variants

Python 3.10+ - non-Annotated

Tip

Prefer to use the Annotated version if possible.

from fastapi import Cookie, FastAPI

app = FastAPI()

@app.get("/items/")
async def read_items(ads_id: str | None = Cookie(default=None)):
return {"ads_id": ads_id}

Technical Details

Cookie is a "sister" class of Path and Query. It also inherits from the same common Param class.

But remember that when you import Query, Path, Cookie and others from fastapi, those are actually functions that return special classes.

Note

To declare cookies, you need to use Cookie, because otherwise the parameters would be interpreted as query parameters.

Note

Have in mind that, as browsers handle cookies in special ways and behind the scenes, they don't easily allow JavaScript to touch them.

If you go to the API docs UI at /docs you will be able to see the documentation for cookies for your path operations.

But even if you fill the data and click "Execute", because the docs UI works with JavaScript, the cookies won't be sent, and you will see an error message as if you didn't write any values.

Recap¶

Declare cookies with Cookie, using the same common pattern as Query and Path.

Back to top

Previous

Extra Data Types

Next

Header Parameters

The FastAPI trademark is owned by @tiangolo and is registered in the US and across other regions

Made with

Zensical
