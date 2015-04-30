============
INSTALLATION
============

Installation instructions for centos 6.4+

**General prerequisites** needed mostly by python and pip.

.. code-block:: bash

	sudo yum install -y python2-devel
	sudo yum install -y python-pip
	sudo yum install -y wget
	sudo yum install -y gcc

-------------------
Installing Mongo DB
-------------------

For more info : http://docs.mongodb.org/manual/tutorial/install-mongodb-on-red-hat-centos-or-fedora-linux/

.. code-block:: bash

	sudo vi /etc/yum.repos.d/mongodb.repo
	sudo yum install mongodb-org

Start mongo service

.. code-block:: bash

	sudo service mongod start

---------------
Installing JASS
---------------

Unpack the project in a directory. We will use $ANNO_STO_HOME to designate it.
In a shell

.. code-block:: bash

	export ANNO_STO_HOME=/usr/local/Service_Storage_Annotations_1_1_0
	cd $ANNO_STO_HOME

Install requirements

.. code-block:: bash

	sudo pip install -r requirements.pip

Creating initial MongoDB structures for annotations
IMPORTANT only run it once. It deletes all contents of in mongo db. 

.. code-block:: bash

	python $ANNO_STO_HOME/migrations/create_db.py $ANNO_STO_HOME/configs/dev/config.ini

*********************************************************************
Optional running the service stand alone with gunicorn and supervisor
*********************************************************************

Installing supervisor

.. code-block:: bash

	sudo yum install supervisor

Upgrading it to the latest version. The reason to use yum first is to create init.d scripts. 

.. code-block:: bash

	sudo pip install --upgrade supervisor

Change init.d scripts for supervsord
change /etc/init.d/supervisord file to point to /etc/supervisord.conf
**daemon supervisord -c /etc/supervisord.conf**

Copy the example supervisord.conf to /etc/supervisord.conf

.. code-block:: bash
	
	sudo cp $ANNO_STO_HOME/configs/dev  /etc/supervisord.conf

Installing gunicorn

.. code-block:: bash
	
	sudo pip install gunicorn

Change **supervisor.conf**, to point to local files

::

  directory=path_to_install_directory
  environment=JASS_CONFIG_PATH=path_to_install_directory/configs/dev/config.ini

Start supervisor

.. code-block:: bash
	
	sudo service supervisord start

************************
Reverse proxy with NGINX
************************

An example file NGIXN config file supplied in the **config/dev** directory.