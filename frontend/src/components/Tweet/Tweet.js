import React from 'react';
import './Tweet.css';
import { useEffect, useState } from 'react';
import configuration from '../../Configuration/config';

function Tweet(props) {
  const [localTweet, setLocalTweet] = useState({});
  const [likeEnabled, setLikeEnabled] = useState(true);
  const [retweetEnabled, setRetweetEnabled] = useState(true);

  useEffect(() => {
    if (props.tweet)
      setLocalTweet(props.tweet)
  }, [props.tweet]);

  const handleRetweet = (tweet) => {
    if (retweetEnabled) {
      fetch(configuration.retweet_tweet + '?tweet_id=' + tweet.tweet_id + '&session_id=2&access_token=' + props.givenArguments.access_token + '&access_token_secret=' + props.givenArguments.access_token_secret, { method: 'POST' });
      try {
        const newTweetLocal = Object.assign({}, localTweet);
        let amount = parseInt(newTweetLocal.retweet_count) + 1;
        newTweetLocal.retweet_count = String(amount);
        setLocalTweet(newTweetLocal);
        setRetweetEnabled(false);
      } catch {
        setRetweetEnabled(false);
      }
    }
  };

  const handleLike = (tweet) => {
    if (likeEnabled) {
      fetch(configuration.like_tweet + '?tweet_id=' + tweet.tweet_id + '&session_id=2&access_token=' + props.givenArguments.access_token + '&access_token_secret=' + props.givenArguments.access_token_secret, { method: 'POST' });
      try {
        const newTweetLocal = Object.assign({}, localTweet);
        let amount = parseInt(newTweetLocal.likes) + 1;
        newTweetLocal.likes = String(amount);
        setLocalTweet(newTweetLocal);
        setLikeEnabled(false);
      } catch {
        setLikeEnabled(false);
      }
    }
  };

  const handleLinkClicked = () => {
    console.log('Link was clicked.');
  };

  return (
    <div className="completeTweet">
      {
        localTweet.retweet_by !== ''
          ? <div className="TweetStateBanner"> Retweeted by: {localTweet.retweet_by} </div>
          : null
      }
      {
        localTweet.quoted_by !== ''
          ?
          <div>
            <div style={{ display: 'flex' }} className="TweetStateBannerQuote">
              <img style={{ paddingRight: '2%', paddingLeft: '1%' }} src={localTweet.quoted_by_actor_picture} alt={"User " + localTweet.quoted_by_actor_picture + '\'s profile picture.'} />
              {localTweet.quoted_by + ' @' + localTweet.quoted_by_actor_username + ' Quoted:'} </div>
            <div className="QuoteBody">{localTweet.quoted_by_text}</div>
          </div>
          : null
      }
      <div className={localTweet.quoted_by === '' ? 'TweetContent' : 'QuotedTweetContent'}>
        <img src={localTweet.actor_picture} alt={"User " + localTweet.actor_name + '\'s profile picture.'} />
        <div style={{ marginLeft: 'auto' }}>
          {localTweet.actor_name}
          {' @' + localTweet.actor_username}
        </div>
      </div>
      <div className={localTweet.quoted_by === '' ? 'TweetContent' : 'QuotedTweetContent'}>
        <div style={{ marginBottom: '1%' }}>{localTweet.body}</div>
        {localTweet.picture !== ''
          ? <div className="TweetArticleContainer">
            <div style={{ marginTop: '1%', marginBottom: '1%' }}>{localTweet.picture_heading}</div>
            <a href={localTweet.urls} rel="noopener noreferrer" target="_blank" onClick={handleLinkClicked}>
              <img className="TweetImage" src={localTweet.picture} alt='Article' />
            </a>
            <div>{localTweet.picture_description}</div>
          </div>
          :
          localTweet.embedded_image !== ''
            ?
            <img className="TweetImage" src={localTweet.embedded_image} alt='User posted' />
            : null}
      </div>
      <div className="TweetFooter">
        <div style={{ float: 'left', marginLeft: '2%' }}>{<button onClick={() => handleRetweet(localTweet)}>{'Retweets: ' + localTweet.retweet_count}</button>}</div>
        <div style={{ marginLeft: 'auto', marginRight: '2%' }}><button onClick={() => handleLike(localTweet)}>{'Likes: ' + localTweet.likes}</button></div>

      </div>
    </div>
  )
}

export default Tweet;
