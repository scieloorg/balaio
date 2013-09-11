Packages API
============

List all packages
--------------------

Request::

  GET /api/v1/packages

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
      "article_title": "Prevalence and risk factors for smoking among adolescents",
      "attempts": [
        "/api/v1/attemps/12345",
        "/api/v1/attemps/12355",
        "/api/v1/attemps/12445",
      ],
      "id": "1",
      "issue_number": "1",
      "issue_volume": "37",
      "issue_year": 2003,
      "issue_suplvol": null,
      "issue_suplnum": null,
      "journal_eissn": null,
      "journal_pissn": "0034-8910",
      "journal_title": "Revista de Saúde Pública",
      "resource_uri": "/api/v1/packages/1/",
      "tickets": [
        "/api/v1/tickets/100",
        "/api/v1/tickets/140",
      ],
    }
  ]

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
    "article_title": "Prevalence and risk factors for smoking among adolescents",
    "attempts": [
      "/api/v1/attemps/12345",
      "/api/v1/attemps/12355",
      "/api/v1/attemps/12445",
    ],
    "id": "1",
    "issue_number": "1",
    "issue_volume": "37",
    "issue_year": 2003,
    "issue_suplvol": null,
    "issue_suplnum": null,
    "journal_eissn": null,
    "journal_pissn": "0034-8910",
    "journal_title": "Revista de Saúde Pública",
    "resource_uri": "/api/v1/packages/1/",
    "tickets": [
        "/api/v1/tickets/100",
        "/api/v1/tickets/140",
      ],
  }
  