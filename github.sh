#!/usr/bin/env bash

dir=~/.github-proj

function set-user() {
	if [ -f $dir/user ]; then
		user=$(cat $dir/user)
	else
		read -p "Enter a Github username: " user
	fi
	read -p "Is $user correct? (y/n) " -n 1 -r
	echo
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		echo "$user" > $dir/user
	else
		rm $dir/user 2>&-
		set-user
	fi
}

# Get an authentication token for the user's Github acount
# Unused in the final version
function set-token() {
	if [ -f $dir/token-$user ]; then
		token=$(cat $dir/token-$user )
	else
		json=$(curl -s https://api.github.com/authorizations --user "$user" --data '{"scopes":["repo"],"note":"owens-github-assignment3"}')
		token=$(echo "$json" | jq -r ".token")
		if [ $token = "null" ]; then
			echo "$json" >&2
			echo "Can't login to Github :(" >&2
			exit 1
		else
			echo $token > $dir/token-$user
		fi
	fi
}

mkdir -p $dir
set-user
repos=$(curl https://api.github.com/users/$user/repos?type=owner | jq 'sort_by(.created_at)')

