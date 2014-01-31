Instalação
==========

Guia de instalação do balaio e suas dependencias.

.. toctree::
   :maxdepth: 2
   
   requisitos


 .. note::

    Clonar o repositório: https://github.com/scieloorg/balaio

Instalar bibliotecas python::

    pip install -r requirements.txt

.. note::
    
    É possível que durante a instalação do *psycopg2* ocorra um erro relacionado ao pg_config.

    Solução:

    Nesse certifique-se de ter instalado os headers do postgres.

.. note::
    
    É possível que durante a instalação do *psycopg2* ocorra um erro relacionado ao python.h.

    Solução:

    Nesse certifique-se de ter instalado os headers do python.

.. note::
    
    É possível que durante a instalação do *lxml* ocorra um erro relacionado ao libxml2.

    Solução:

    Nesse certifique-se de ter instalado os headers do libxml.

.. note::
    
    É possível que durante a instalação do *lxml* ocorra um erro relacionado ao libxslt.

    Solução:

    Nesse certifique-se de ter instalado os headers do libxslt.

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
            virtualenv_path = /home/fabiobatalha/.virtualenvs/balaio
            BALAIO_SETTINGS_FILE = /home/fabiobatalha/Trabalho/balaio/conf/config.ini
            BALAIO_ALEMBIC_SETTINGS_FILE = /home/fabiobatalha/Trabalho/balaio/conf/alembic.ini
            app_working_dir = /home/fabiobatalha/Trabalho/balaio




Sincronizar banco de dados::

    python balaio/balaio.py -c conf/config.ini --syncdb

