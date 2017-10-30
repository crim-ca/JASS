Installation
============

Installation instructions for CentOS 6.6+

**External Requirements** :
    MongoDB 3.4
    Python 3.6


Installing JASS via docker compose
----------------------------------
The first possibility is to install and run jass via docker-compose. Docker-compose enables to start multiple services,
as separate docker containers.
**Requirements**
  * Docker (see https://www.docker.com/ for installing and using docker)
  * Docker compose (see https://docs.docker.com/compose/ for installing and using compose)

Containers will be automatically build once docker compose is executed for the first time.

Installing JASS / MongoDB standalone
------------------------------------

**JASS**
For installing JASS copy the instrcutions from Dockerfile.
JASS connection to MongoDB is defined by 'MONGO_HOST' environment variable.
For connecting jass to MongoDB refer to docker-compose.yml
To see enviroment variables used by both JASS and MongoDB refer to .env file.

**MongoDB**
Refert to the section: jass_mongo in docker-compose.
***Important*** JASS was tested with MongoDB 2.6

Installing JASS standalone
--------------------------
External Requirements** :
    MongoDB 3.4
    Python 3.6

