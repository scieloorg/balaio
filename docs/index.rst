Documentação técnica do projeto Balaio
======================================

Balaio é uma ferramenta automatizada para apoiar o processo 
de ingresso de artigos em coleções SciELO.

Esta aplicação foi projetada para operar no contexto da nova
plataforma tecnológica de gestão de dados, e suas funcionalidades
serão expostas aos usuários por meio do `SciELO Manager <http://manager.scielo.org>`_.


Funcionalidades
---------------

* Monitoramento do sistema de arquivos para novos depósitos.
* Validação automática de diversos aspectos do pacote.
    * Metadados.
* Criação de tickets com pendências associadas ao artigo em processo de submissão.


Funcionalidades pendentes
-------------------------

* Validação automática de arquivos complementares (imagens, pdf etc).
* Integração do sistema de notificações com o SciELO Manager (painel de controle do usuário).


Guias de desenvolvimento
========================

Technical guides and artifacts explaining software components
and design decisions.

.. toctree::
   :maxdepth: 2
   
   dev/gateway_http_api
   design
   domain

