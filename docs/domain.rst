Objetos de domínio do negócio
=============================


:class:`models.ArticlePkg`
--------------------------

Representa um artigo em processo de ingresso no sistema. Uma instância de 
:class:`models.ArticlePkg` pode conter *n* :class:`models.Attempt` associadas,
dependendo de quantas iterações foram necessárias até que um pacote fosse
validado durante o processo. Instâncias de :class:`models.ArticlePkg` contém 
apenas metadados do artigo objeto de análise.


:class:`models.Attempt`
-----------------------

Representa a submissão de um pacote para validação. É marcada como válida ou 
inválida (*is_valid*) para sinalizar tentativas que possuem condições de 
serem submetidas ao processo de validação. 

Uma instância de :class:`models.Attempt` deve ser criada para cada pacote
de artigos depositado, exceto quando se tratar de um pacote duplicado.

