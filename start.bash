#!/bin/bash
command="$0"
start="start"
stop="stop"
restart="restart"
if [$command == $start]
then
    tmux new-session -s NodeApp -d 'node ./app.js'
    tmux new-session -s Authorizer -d 'cd ./twitter_api/twauth-web-master/ && python3 ./twauth-web.py'
    tmux new-session -s FeedRendering -d 'cd ./twitter_api/guest_access_tweepy/ && python3 ./guest_access_twitter_flask.py'
    tmux new-session -s DatabaseAccess -d 'cd ./twitter_api/database_access/ && python3 ./database_access.py'
    tmux new-session -s Engagement -d 'cd ./twitter_api/engagement_servers/ && python3 ./Retweet.py'
elif [$command == $stop]
then
    tmux kill-session -t NodeApp
    tmux kill-session -t Authorizer
    tmux kill-session -t FeedRendering
    tmux kill-session -t DatabaseAccess
    tmux kill-session -t Engagement
elif [$command == $restart]
then
    tmux kill-session -t NodeApp
    tmux kill-session -t Authorizer
    tmux kill-session -t FeedRendering
    tmux kill-session -t DatabaseAccess
    tmux kill-session -t Engagement
    sleep 5
    tmux new-session -s NodeApp -d 'node ./app.js'
    tmux new-session -s Authorizer -d 'cd ./twitter_api/twauth-web-master/ && python3 ./twauth-web.py'
    tmux new-session -s FeedRendering -d 'cd ./twitter_api/guest_access_tweepy/ && python3 ./guest_access_twitter_flask.py'
    tmux new-session -s DatabaseAccess -d 'cd ./twitter_api/database_access/ && python3 ./database_access.py'
    tmux new-session -s Engagement -d 'cd ./twitter_api/engagement_servers/ && python3 ./Retweet.py'
else
    echo "No valid argument given, start,stop,restart."
fi