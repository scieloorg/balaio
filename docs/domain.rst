Objetos de domínio do negócio
=============================


:class:`lib.models.ArticlePkg`
------------------------------

Representa um artigo em processo de ingresso no sistema. Uma instância de 
:class:`lib.models.ArticlePkg` pode conter *n* :class:`lib.models.Attempt` associadas,
dependendo de quantas iterações foram necessárias até que um pacote fosse
validado durante o processo. Instâncias de :class:`lib.models.ArticlePkg` contém 
apenas metadados do artigo objeto de análise.


:class:`lib.models.Attempt`
---------------------------

Representa a submissão de um pacote para validação. É marcada como válida ou 
inválida (*is_valid*) para sinalizar tentativas que possuem condições de 
serem submetidas ao processo de validação. 

Uma instância de :class:`lib.models.Attempt` deve ser criada para cada pacote
de artigos depositado, exceto quando se tratar de um pacote duplicado.


Status de notificação
=====================

Durante a operação, o `balaio` dispara uma série de notificações para o 
SciELO Manager, para noticiar a chegada de um novo pacote, erros ou 
resultados de validação automática.

Uma notificação deve sempre acompanhar um instância enumerável de 
:class:`lib.models.Status`, que são divididas em:


Status de validação
-------------------

Qualificam as notificações sobre validações automáticas, que podem ser:

* `lib.models.Status.ok`: A tag referida está presente e/ou seu conteúdo está correto.
* `lib.models.Status.warning`: Existem pequenos problemas que é bom saber, mas podemos seguir em frente.
* `lib.models.Status.error`: Alguma tag/dado essencial está faltando, ou o dado está expresso de maneira inválida.


Status de validação podem ocupar valores de 1 a 49 (inclusive), que uma vez atribuídos não podem ser alterados


Status de serviço
-----------------

Forma limitada de comunicação inter-aplicações. Atualmente é usado apenas para delimitar conjuntos de mensagens 
correlatas.

* `lib.models.Status.SERV_BEGIN`: Sinaliza o início de um bloco de mensagens correlatas.
* `lib.models.Status.SERV_END`: Sinaliza o término de um bloco de mensagens correlatas.

Status de serviço podem ocupar valores de 50 a 99 (inclusive), que uma vez atribuídos não podem ser alterados

