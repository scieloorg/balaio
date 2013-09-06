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

  **format**

    *String* of the desired output format. The options are **xml, json,
    yml**.

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
      "collection_uri": "/api/v1/collections/1/",
      "finished_at": "2012-07-24T21:59:23.909404",
      "is_open": True,
      "resource_uri": "/api/v1/tickets/1/",
      "started_at": "2012-07-24T21:53:23.909404",
      "comments": [
        "djaja;ljfa",
        "jajfaljfadljfa",
        "adjfdajf;aj",
      ],
      
    }
  ]


Open a ticket
-------------

Request::

  POST /api/v1/tickets/new/

Parameters:

  **--**

Required Parameters:

  **articlepkg_id**

    *Integer* of the **article package ID** to be used as a filter param.

Optional Parameters:

  **callback**

    *String* of the callback identifier to be returned when using JSONP.

  **format**

    *String* of the desired output format. The options are **xml, json,
    yml**.


Response::

  {
      "articlepkg_id": 1,
      "id": "1",
      "collection_uri": "/api/v1/collections/1/",
      "finished_at": null,
      "is_open": True,
      "resource_uri": "/api/v1/tickets/1/",
      "started_at": "2012-07-24T21:53:23.909404",
      "comments": [
        "djaja;ljfa",
      ],
      
    }


Close a ticket
--------------

Request::

  PUT /api/v1/tickets/:id/close/

Parameters:

  **--**

Required Parameters:

  **ticket_id**

    *Integer* of the **ticket  ID** to be used as a filter param.

Optional Parameters:

  **callback**

    *String* of the callback identifier to be returned when using JSONP.

  **format**

    *String* of the desired output format. The options are **xml, json,
    yml**.


Response::

  {
      "articlepkg_id": 1,
      "id": "1",
      "collection_uri": "/api/v1/collections/1/",
      "finished_at": "2012-07-24T21:59:23.909404",
      "is_open": False,
      "resource_uri": "/api/v1/tickets/1/",
      "started_at": "2012-07-24T21:53:23.909404",
      "comments": [
        "djaja;ljfa",
        "jajfaljfadljfa",
        "adjfdajf;aj",
      ],
      
    }


Update a ticket
---------------

Request::

  POST /api/v1/tickets/:id/update/

Parameters:

  **--**

Required Parameters:

  **ticket_id**

    *Integer* of the **ticket  ID** to be used as a filter param.

Optional Parameters:

  **callback**

    *String* of the callback identifier to be returned when using JSONP.

  **format**

    *String* of the desired output format. The options are **xml, json,
    yml**.

  **comment**

    *String* of the comment.

Response::

  {
      "articlepkg_id": 1,
      "id": "1",
      "collection_uri": "/api/v1/collections/1/",
      "finished_at": "2012-07-24T21:59:23.909404",
      "is_open": True,
      "resource_uri": "/api/v1/tickets/1/",
      "started_at": "2012-07-24T21:53:23.909404",
      "comments": [
        "djaja;ljfa",
        "jajfaljfadljfa",
        "adjfdajf;aj",
      ],
      
    }