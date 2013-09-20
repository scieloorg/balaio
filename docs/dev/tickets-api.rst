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
    "total_count": 1
  },
  "objects": [
    {
      "articlepkg_id": 1,
      "id": "1",
      "finished_at": "2012-07-24T21:59:23.909404",
      "is_open": true,
      "resource_uri": "/api/v1/tickets/1/",
      "started_at": "2012-07-24T21:53:23.909404",
      "comments": [
        "comments ...",
        "comments ...",
        "comments ... ",
      ],
      
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
      "is_open": true,
      "comments": "comments",
      "started_at": "2012-07-24T21:53:23.909404",
  }

Response::
  
  {
      "articlepkg_id": 1,
      "id": "1",
      "finished_at": null,
      "is_open": true,
      "resource_uri": "/api/v1/tickets/1/",
      "started_at": "2012-07-24T21:53:23.909404",
      "comments": [
        "comments",
      ],
      
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
      "is_open": false,
      "comments": "comments",
      "finished_at": "2012-07-24T21:53:23.909404",
  }

Response::
  
  HTTP STATUS CODE

  202 Accepted 


