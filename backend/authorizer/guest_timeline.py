import tweepy

cred = {}

f = open("./guest_credentials.txt")
for line in f:
    name, value = line.split(":")
    cred[name] = value.strip()
f.close()

auth = tweepy.OAuthHandler(cred["key"], cred["key_secret"])
auth.set_access_token(cred["token"], cred["token_secret"])
api = tweepy.API(auth)

public_tweets = api.home_timeline()

print(80 * "-")
for tweet in public_tweets:
    print(tweet.text)
    print(80 * "-")