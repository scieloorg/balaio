Attempts API
============

List all attempts
-----------------

Request::

  GET /api/v1/attempts/

Parameters:

  **--**


Optional Parameters:

  **callback**

    *String* of the callback identifier to be returned when using JSONP.

  **articlepkg_id**

    *Integer* of the **article package ID** to be used as a filter param.

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
      "next": "/api/v1/attempts/?limit=20&offset=40",
      "offset": 20,
      "previous": "/api/v1/attempts/?limit=20&offset=0",
      "total_count": 100
    },
    "objects": [
      {
        "articlepkg_id": 1,
        "id": 1,
        "collection_uri": "/api/v1/collections/1/",
        "finished_at": "2012-07-24T21:59:23.909404",
        "filepath": "/files/ajfajfajfa",
        "is_valid": true,
        "package_checksum": "12345678901234567890123456789012",
        "resource_uri": "/api/v1/attempts/1/",
        "started_at": "2012-07-24T21:53:23.909404",
        "checkin": {
          "finished_at": "2012-07-24T21:53:23.909404",
          "started_at": "2012-07-24T21:53:23.909404",
          "notices": [
            {
              "label": "Checkin",
              "message": "",
              "status": "ok",
              "date": "2012-07-24T21:53:23.909404",
            },
          ],
        },
        "validations": {
          "finished_at": "2012-07-24T21:53:23.909404",
          "started_at": "2012-07-24T21:53:23.909404",
          "notices": [
            {
              "label": "journal",
              "message": "",
              "status": "ok",
              "date": "2012-07-24T21:53:23.909404",
            },
            {
              "label": "journal",
              "message": "",
              "status": "error",
              "date": "2012-07-24T21:53:23.909404",
            },
            {
              "label": "front",
              "message": "",
              "status": "warning",
              "date": "2012-07-24T21:53:23.909404",
            },
            {
              "label": "front",
              "message": "",
              "status": "ok",
              "date": "2012-07-24T21:53:23.909404",
            },
            {
              "label": "references",
              "message": "",
              "status": "ok",
              "date": "2012-07-24T21:53:23.909404",
            },
            {
              "label": "references",
              "message": "",
              "status": "ok",
              "date": "2012-07-24T21:53:23.909404",
            },
          ],
        }
      }
    ]
  }



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
    "id": 1,
    "collection_uri": "/api/v1/collections/1/",
    "finished_at": "2012-07-24T21:59:23.909404",
    "filepath": "/files/ajfajfajfa",
    "is_valid": true,
    "package_checksum": "12345678901234567890123456789012",
    "resource_uri": "/api/v1/attempts/1/",
    "started_at": "2012-07-24T21:53:23.909404",
    "checkin": {
      "finished_at": "2012-07-24T21:53:23.909404",
      "started_at": "2012-07-24T21:53:23.909404",
      "notices": [
        {
          "label": "Checkin",
          "message": "",
          "status": "ok",
          "date": "2012-07-24T21:53:23.909404",
        },
      ],
    },
    "validations": {
      "finished_at": "2012-07-24T21:53:23.909404",
      "started_at": "2012-07-24T21:53:23.909404",
      "notices": [
        {
          "label": "journal",
          "message": "",
          "status": "ok",
          "date": "2012-07-24T21:53:23.909404",
        },
        {
          "label": "journal",
          "message": "",
          "status": "error",
          "date": "2012-07-24T21:53:23.909404",
        },
        {
          "label": "front",
          "message": "",
          "status": "warning",
          "date": "2012-07-24T21:53:23.909404",
        },
        {
          "label": "front",
          "message": "",
          "status": "ok",
          "date": "2012-07-24T21:53:23.909404",
        },
        {
          "label": "references",
          "message": "",
          "status": "ok",
          "date": "2012-07-24T21:53:23.909404",
        },
        {
          "label": "references",
          "message": "",
          "status": "ok",
          "date": "2012-07-24T21:53:23.909404",
        },
      ],
    }
  }
