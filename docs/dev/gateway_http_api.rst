=======================
Balaio Gateway HTTP API
=======================

This API is a RESTful API which provides services related to the XML packages, 
their attemps and the validations reports.


**Current version:** API v1


Available endpoints
-------------------

.. toctree::
  :maxdepth: 2

  packages-api
  attempts-api
  pipes-api
  tickets-api
  

.. note::

  The API uses the ``Accepts`` HTTP headers in order to decide which one is
  the best format to be used. Options are: ``application/xml``,
  ``application/json`` and ``application/yaml``.

  If you try these requests in your browser, you will need to use the
  parameter ``format`` with one of the valid format types (xml, json or yaml).


