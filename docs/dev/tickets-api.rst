Tickets API
============

List all tickets
-----------------

Request::

  GET /api/v1/tickets/

Parameters:

  **--**

Optional Parameters:

  **callback**

    *String* of the callback identifier to be returned when using JSONP.

  **articlepkg_id**

    *Integer* of the **article package ID** to be used as a filter param.

  **is_open**

    *Boolean* of the **status** to be used as a filter param.

  **author**

    *String* of the **e-mail** of the user who created the ticket

  **id**

    *id* of the **id** of the user who created the ticket

  **title**

    *title* of the **title** of the user who created the ticket


Response::

  {
    "meta": {
      "limit": 20,
      "next": "/api/v1/tickets/?limit=20&offset=40",
      "offset": 20,
      "previous": "/api/v1/tickets/?limit=20&offset=0",
      "total": 100
    },
    "objects": [
      {
        "articlepkg_id": 1,
        "id": 1,
        "finished_at": "2012-07-24T21:59:23.909404",
        "is_open": true,
        "resource_uri": "/api/v1/tickets/1/",
        "started_at": "2012-07-24T21:53:23.909404",
        "author": "username@scielo.org",
        "title": "título para o ticket",
        "comments": [
          {
            "author": "user.name@scielo.org",
            "date": "2012-07-24T21:53:23.909404",
            "message": 'Corrigir ...',
          },
        ],
      }
    ]
  }


Get a single ticket
-------------------

Request::

  GET /api/v1/tickets/:id/

Parameters:

  **--**

Optional Parameters:

  **callback**

    *String* of the callback identifier to be returned when using JSONP.


Response::

  {
    "articlepkg_id": 1,
    "id": 1,
    "finished_at": "2012-07-24T21:59:23.909404",
    "is_open": true,
    "resource_uri": "/api/v1/tickets/1/",
    "started_at": "2012-07-24T21:53:23.909404",
    "ticket_author": "username@scielo.org",
    "title": "Correção de ...",
    "comments": [
        {
          "comment_author": "user.name@scielo.org",
          "comment_date": "2012-07-24T21:53:23.909404",
          "message": 'Corrigir ...',
          "ticket_id": 1,
        },
        {
          "comment_author": "user.name@scielo.org",
          "comment_date": "2012-07-24T21:53:23.909404",
          "message": 'Corrigir ...',
          "ticket_id": 1,
        },
      ]
  }


Open a ticket
-------------

Request::

  POST /api/v1/tickets/

Parameters:

  **--**


Optional Parameters:

  **callback**

    *String* of the callback identifier to be returned when using JSONP.

Payload::

  {
      "articlepkg_id": 1,
      "message": "comment",
      "author": "username@scielo.org",
      "title": "ticket title"
  }

  where **message** is optional


Response::

  HTTP STATUS CODE

  201 Created


Update a ticket
--------------

Request::

  PATCH /api/v1/tickets/:id/

Parameters:

  **--**


Optional Parameters:

  **callback**

    *String* of the callback identifier to be returned when using JSONP.

Payload::

  {
      "is_open": false,
      "comment_author": "user.name@scielo.org",
      "message": 'Corrigir ...',
  }

  where **message** and **comment_author** are optional


Response::

  HTTP STATUS CODE

  204 No Content


