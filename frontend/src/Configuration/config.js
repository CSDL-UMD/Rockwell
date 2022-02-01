const config = {
  get_feed: 'http://127.0.0.1:5051/getfeed',
  like_tweet: 'http://127.0.0.1:5050/like',
  retweet_tweet: 'http://127.0.0.1:5050/retweet',
  authorizer: 'http://127.0.0.1:5000',
  error: 'http://127.0.0.1:3000/error',
  error_codes: {
    no_tweets_main_feed: 0,
    tweet_fetch_error_main_feed: 1,
    no_tweets_attn_check: 2,
    tweet_fetch_error_attn_check: 3
  }
}

export default config;
