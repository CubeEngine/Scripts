#!/bin/bash

here="$(dirname "$(readlink -f "$0")")"
tx_client="/usr/local/bin/tx"

extractor_plugin_goal="de.cubeisland.maven.plugins:messageextractor-maven-plugin:2.0.0:update"

update_repo()
{
    repo_name="$1"
    
    echo "##########################"
    echo "# Repo: $repo_name"
    echo "##########################"

    if [[ -e "$repo_name" ]]
    then
        echo "$repo_name is already existing, skipping..."
        return 1
    fi
    
    repo_dir="$(mktemp -d)"

    if git clone --depth 1 "ssh://git@github/CubeEngine/${repo_name}.git" "$repo_dir"
    then
        pushd "$repo_dir"

        date

        if mvn $extractor_plugin_goal
        then
            echo "Updating the catalog templates..."
            git add **/*.pot
            git commit -m "Updated the message catalog templates"
            git reset --hard HEAD
            echo "...done"
            
            echo "Pushing new source files to transifex..."
            $tx_client push -s
            echo "...done"

            echo "Getting the new catalogs..."
            $tx_client pull -a
            git add **/*.po
            git commit -m "Updated the translations"
            git reset --hard HEAD
            echo "...done"
        else
            echo "Maven failed..."
        fi

        git push

        popd > /dev/null
    else
        echo "Failed to pull the repo ${repo_name}..."
    fi

    rm -Rf "$repo_dir"
}

repos=(core modules-main modules-extra)

if [[ ! "$1" == "" ]]
then
    update_repo $1
else
    for i in ${repos[@]}
    do
        update_repo $i
    done
fi
