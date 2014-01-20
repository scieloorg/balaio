Packages API
============

List all packages
-----------------

Request::

  GET /api/v1/packages/

Parameters:

  **--**

Optional Parameters:

  **callback**

    *String* of the callback identifier to be returned when using JSONP.

  **journal_pissn**

    *String* of the **journal_pissn** to be used as a filter param.

  **journal_eissn**

    *String* of the **journal_eissn** to be used as a filter param.

  **issue_volume**

    *String* of the **issue volume** to be used as a filter param.

  **issue_number**

    *String* of the **issue number** to be used as a filter param.

  **issue_suppl_volume**

    *String* of the **issue volume supplement** to be used as a filter param.

  **issue_suppl_number**

    *String* of the **issue number supplement** to be used as a filter param.

  **issue_year**

     *String* of the **issue year**  to be used as a filter param.

  **article_title**

     *String* of the **artile title**  to be used as a filter param.

  **journal_title**

     *String* of the **journal title**  to be used as a filter param.

  **id**

     *Integer* of the **id**  to be used as a filter param.

  **aid**

     *String* of the **article-id**  to be used as a filter param.

Response::

    {
      "meta": {
        "limit": 20,
        "next": "/api/v1/packages/?limit=20&offset=40",
        "offset": 20,
        "previous": "/api/v1/packages/?limit=20&offset=0",
        "total": 100
      },
      objects: [
          {
            article_title: "Article Title",
            tickets: [
              "/api/v1/tickets/100",
              "/api/v1/tickets/140",
            ],
            issue_year: 2010,
            journal_title: "Journal Title",
            journal_pissn: "1234-1234",
            journal_eissn: "1234-1234",
            issue_suppl_number: "1",
            attempts: [
              "/api/v1/attempts/1/"
            ],
            issue_suppl_volume: "1",
            issue_volume: "1",
            aid: "yp4529bp8g",
            resource_uri: "/api/v1/packages/3/",
            id: 3,
            issue_number: "1"
          },
          {
            article_title: "Article Title",
            tickets: [
              "/api/v1/tickets/100",
              "/api/v1/tickets/140",
            ],
            issue_year: 1998,
            journal_title: "Journal Title",
            journal_pissn: "2349-2309",
            journal_eissn: "9832-1987",
            issue_suppl_number: "8",
            attempts: [
              "/api/v1/attempts/1/"
            ],
            issue_suppl_volume: "7",
            issue_volume: "11",
            aid: "jp4599bq8g",
            resource_uri: "/api/v1/packages/4/",
            id: 4,
            issue_number: "3"
          }
        ]
      }


Get a single package
--------------------

Request::

  GET /api/v1/packages/:id/

Parameters:

  **--**

Optional Parameters:

  **callback**

    *String* of the callback identifier to be returned when using JSONP.


Response::

    {
      article_title: "Article Title",
      tickets: [
        "/api/v1/tickets/100",
        "/api/v1/tickets/140",
      ],
      issue_year: 2013,
      journal_title: "Journal Title",
      journal_pissn: "1234-1234",
      journal_eissn: "1234-1234",
      issue_suppl_number: "1",
      attempts: [
          "/api/v1/attempts/1/"
      ],
      issue_suppl_volume: "1",
      issue_volume: "1",
      aid: "yp4529bp8g",
      resource_uri: "/api/v1/packages/3/",
      id: 3,
      issue_number: "1"
    }

