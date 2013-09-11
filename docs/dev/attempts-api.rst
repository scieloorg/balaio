Attempts API
============

List all attempts
-----------------

Request::

  GET /api/v1/attempts

Parameters:

  **--**

Required Parameters:

  **articlepkg_id**

    *Integer* of the **article package ID** to be used as a filter param.

Optional Parameters:

  **callback**

    *String* of the callback identifier to be returned when using JSONP.

  **started_at**

    *DateTime* of the **started_at** to be used as a filter param.

  **finished_at**

    *DateTime* of the **finished_at** to be used as a filter param.

  **is_valid**

    *Boolean* of the **is valid** to be used as a filter param.


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
      "filepath": "/files/ajfajfajfa",
      "is_valid": true,
      "package_checksum": "12345678901234567890123456789012",
      "resource_uri": "/api/v1/attempts/1/",
      "started_at": "2012-07-24T21:53:23.909404",
      "validations": [
        "/api/v1/validations/12345",
        "/api/v1/validations/12355",
        "/api/v1/validations/12445",
      ],
      
    }
  ]

Get a single attempt
--------------------

Request::

  GET /api/v1/attempts/:id/

Parameters:

  **--**

Optional Parameters:

  **callback**

    *String* of the callback identifier to be returned when using JSONP.


Response::

  {
    "articlepkg_id": 1,
    "id": "1",
    "collection_uri": "/api/v1/collections/1/",
    "finished_at": "2012-07-24T21:59:23.909404",
    "filepath": "/files/ajfajfajfa",
    "is_valid": true,
    "package_checksum": "12345678901234567890123456789012",
    "resource_uri": "/api/v1/attempts/1/",
    "started_at": "2012-07-24T21:53:23.909404",
    "validations": [
      "/api/v1/validations/12345",
      "/api/v1/validations/12355",
      "/api/v1/validations/12445",
    ],
    
  }
