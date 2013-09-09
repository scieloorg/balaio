Validations API
===============

List all validations
--------------------

Request::

  GET /api/v1/validations

Parameters:

  **--**

  **articlepkg_id**

    *Integer* of the **article package ID** to be used as a filter param.

Optional Parameters:

  **callback**

    *String* of the callback identifier to be returned when using JSONP.

  **format**

    *String* of the desired output format. The options are **xml, json,
    yml**.

  **attempt_id**

    *Integer* of the **attempt ID** to be used as a filter param.

  **started_at**

    *DateTime* of the **started_at** to be used as a filter param.

  **finished_at**

    *DateTime* of the **finished_at** to be used as a filter param.

  **stage**

    *String* of the **stage** to be used as a filter param.

  **message**

    *String* of the **message** to be used as a filter param.


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
      "attempt_id": 1,
      "id": "1",
      "finished_at": "2012-07-24T21:59:23.909404",
      "message": "...."
      "stage": "STAGE",
      "status": 1,
      "started_at": "2012-07-24T21:53:23.909404",
      
    }
  ]

Get a single validation
-----------------------

Request::

  GET /api/v1/validations/:id/

Parameters:

  **--**

Optional Parameters:

  **callback**

    *String* of the callback identifier to be returned when using JSONP.

  **format**

    *String* of the desired output format. The options are **xml, json,
    yml**.


Response::

  {
      "articlepkg_id": 1,
      "attempt_id": 1,
      "id": "1",
      "finished_at": "2012-07-24T21:59:23.909404",
      "message": "...."
      "stage": "STAGE",
      "status": 1,
      "started_at": "2012-07-24T21:53:23.909404",
      
  }
