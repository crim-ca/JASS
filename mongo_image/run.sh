#!/bin/bash

if [ -n "$MONGODB_DATABASE" ] && [ -n "$MONGODB_USER" ] && [ -n "$MONGODB_PASS" ]; then
        /usr/local/bin/docker-entrypoint.sh mongod --fork --logpath /tmp/mongolog.txt
        OUTPUT=$(echo -e "use $MONGODB_DATABASE\ndb.getUser('$MONGODB_USER')" | mongo)
        if [[ $OUTPUT == *"null"* ]]; then
                # User not there create it
                echo "Create user $MONGODB_USER for db $MONGODB_DATABASE"
                echo -e "use $MONGODB_DATABASE\ndb.createUser({ user: '$MONGODB_USER', pwd: '$MONGODB_PASS', roles: [ { role: 'dbOwner', db: '$MONGODB_DATABASE' } ] });" | mongo
                echo "Create text index for annotations"
                echo -e "use $MONGODB_DATABASE\ndb.humanAnno.createIndex({text:'text',motionName:'text',shotName:'text',speakerId:'text',speakerSubtype:'text', words:'text'}, {name: 'TextIndex'});" | mongo
        else
                # User already here do nothing
                echo "User $MONGODB_USER already exists for db $MONGODB_DATABASE"
        fi
        # restart mongo with permissions enabled
        mongod --shutdown
        /usr/local/bin/docker-entrypoint.sh mongod --fork --auth --logpath /tmp/mongolog.txt
        tail -f /tmp/mongolog.txt
else
        echo "User not specified DB will not be accessible"
fi