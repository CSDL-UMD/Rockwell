#!/bin/bash
tmux new-session -s NodeApp -d 'node ./app.js'

tmux new-session -s Authorizer -d 'cd ./twitter_api/twauth-web-master/ && python3 ./twauth-web.py'

tmux new-session -s FeedRendering -d 'cd ./twitter_api/guest_access_tweepy/ && python3 ./guest_access_twitter_flask.py'

tmux new-session -s DatabaseAccess -d 'cd ./twitter_api/database_access/ && python3 ./database_access.py'

tmux new-session -s Engagement -d 'cd ./twitter_api/engagement_servers/ && python3 ./Retweet.py'