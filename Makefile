WORKING_DIR = balaio
SETTINGS = config.ini


deps:
	@pip install -r requirements.txt

clean:
	@find . -name "*.pyc" -delete

test: clean
	@python setup.py test -q

dbsetup:
	@python $(WORKING_DIR)/balaio.py -c config.ini --syncdb

setup: deps dbsetup test 

reload:
	@circusctl reload logging_server --waiting
	@circusctl reload httpd --waiting
	@circusctl reload validator --waiting
	@circusctl reload monitor --waiting
        
dbupgrade:
	@alembic --config conf/alembic.ini upgrade head

upgrade: deps dbupgrade test

