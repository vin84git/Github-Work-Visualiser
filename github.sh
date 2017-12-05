#!/usr/bin/env bash

json=$(curl -s https://api.github.com/authorizations --user "414owen" --data '{"scopes":["gist"],"note":"Demo6"}')

token=$(echo "$json" | jq -r ".token")
if [ $token = "null" ]; then
	echo "$json" >&2
	echo "Can't login to Github :(" >&2
fi


