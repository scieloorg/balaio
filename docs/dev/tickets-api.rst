Tickets API
============

List all tickets
-----------------

Request::

  GET /api/v1/tickets

Parameters:

  **--**

Required Parameters:

  **articlepkg_id**

    *Integer* of the **article package ID** to be used as a filter param.

Optional Parameters:

  **callback**

    *String* of the callback identifier to be returned when using JSONP.

  **is_open**

    *Boolean* of the **status** to be used as a filter param.

  

Response::

  {
  "meta": {
    "limit": 20,
    "next": null,
    "offset": 0,
    "previous": null,
    "total": 1
  },
  "objects": [
    {
      "articlepkg_id": 1,
      "id": 1,
      "finished_at": "2012-07-24T21:59:23.909404",
      "is_open": true,
      "resource_uri": "/api/v1/tickets/1/",
      "started_at": "2012-07-24T21:53:23.909404",
      "ticket_author": "user.name@scielo.org",
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
  ]


Open a ticket
-------------

Request::

  POST /api/v1/tickets/

Parameters:

  **--**

Required Parameters:

  **articlepkg_id**

    *Integer* of the **article package ID** to be used as a filter param.

Optional Parameters:

  **callback**

    *String* of the callback identifier to be returned when using JSONP.

Payload::
  
  {
      "articlepkg_id": 1,
      "ticket_author": "user.name@scielo.org",
      "title": "Correção de ...", 
      "message": 'Corrigir ...',
  }

Response::
  
  {
      "articlepkg_id": 1,
      "id": 1,
      "is_open": true,
      "resource_uri": "/api/v1/tickets/1/",
      "started_at": "2012-07-24T21:53:23.909404",
      "ticket_author": "user.name@scielo.org",
      "title": "Correção de ...", 
      "comments": [
        {
          "comment_author": "user.name@scielo.org",
          "comment_date": "2012-07-24T21:53:23.909404",
          "message": 'Corrigir ...',
          "ticket_id": 1,
        },
      ]
  }


Update a ticket
--------------

Request::

  PATCH /api/v1/tickets/:id/

Parameters:

  **--**

Required Parameters:

  **ticket_id**

    *Integer* of the **ticket  ID** to be used as a filter param.


Optional Parameters:

  **callback**

    *String* of the callback identifier to be returned when using JSONP.

Payload::

  {
      "id": 1,
      "is_open": false,
      "comment_author": "user.name@scielo.org",
      "message": 'Corrigir ...',
  }

Response::
  
  HTTP STATUS CODE

  202 Accepted 


