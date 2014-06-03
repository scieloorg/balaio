Guia de Instalação
==================

Guia de instalação do balaio e suas dependencias.

Requisitos
----------

    * python2.7
    * git
    * circus
    * chaussette
    * postgres
    * Linux
    * virtualenv (opcional)


Instalação
----------

    Clonar o repositório: https://github.com/scieloorg/balaio

Instalar bibliotecas python::

    pip install -r requirements.txt

.. note::
    
    É possível que durante a instalação do **psycopg2** ocorra um erro relacionado ao **pg_config**. Nesse caso certifique-se de ter instalado os headers do **postgresql**.

.. note::
    
    É possível que durante a instalação do **psycopg2** ocorra um erro relacionado ao **python.h**. Nesse caso certifique-se de ter instalado os headers do **python**.

.. note::
    
    É possível que durante a instalação do **lxml** ocorra um erro relacionado ao **libxml2**. Nesse caso certifique-se de ter instalado os headers do **libxml**.

.. note::
    
    É possível que durante a instalação do **lxml** ocorra um erro relacionado ao **libxslt**. Nesse caso certifique-se de ter instalado os headers do **libxslt**.

Instalar aplicação::

    python setup.py [develop|install]

Configurar aplicação
--------------------

    alembic.ini::

        Configurar regras de conexão com banco de dados

        sqlalchemy.url = driver://user:pass@localhost/dbname

    config.ini::

        #. Configurar regras de conexão com banco de dados

            sqlalchemy.url = driver://user:pass@localhost/dbname

        #. Configurar conta de usuário da api do SciELO Manager

    circus.ini::

        #. Configurar variáveis de ambiente

            [env]
            ;---- absolute paths only
            virtualenv_path = 
            BALAIO_SETTINGS_FILE = 
            BALAIO_ALEMBIC_SETTINGS_FILE = 
            app_working_dir = 

    Sincronizar banco de dados::

        python balaio/balaio.py -c conf/config.ini --syncdb


Testar aplicação
----------------

    Criar banco de dados de testes no postgresql. O banco deve se chamar **app_balaio_tests**

    Executar testes::
    
        python setup.py nosetests


