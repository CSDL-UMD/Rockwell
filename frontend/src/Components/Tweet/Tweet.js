import React from 'react';
import './Tweet.css';
import fallback from './3925572_1_10.png';
import { useEffect, useState } from 'react';
import configuration from '../../Configuration/config';
import retUnclicked from '../MainFeed/Icons/retweet-unclicked.png';
import retClicked from '../MainFeed/Icons/retweet-clicked.png';
import likeUnclicked from '../MainFeed/Icons/like-unclicked.png';
import likeClicked from '../MainFeed/Icons/like-clicked.png';

function Tweet(props) {
  const [localTweet, setLocalTweet] = useState({});
  const [likeEnabled, setLikeEnabled] = useState(true);
  const [retweetEnabled, setRetweetEnabled] = useState(true);

  useEffect(() => {
    if (props.tweet)
      setLocalTweet(props.tweet)
    props.tweet.user_fav === 'True' ? setLikeEnabled(false) : setLikeEnabled(true);
    props.tweet.user_retweet === 'True' ? setRetweetEnabled(false) : setRetweetEnabled(true); 
  }, [props.tweet]);

  const handleRetweet = (tweet) => {
    if (retweetEnabled) {
      //fetch(configuration.retweet_tweet + '?tweet_id=' + tweet.tweet_id + '&session_id=2&access_token=' + props.givenArguments.access_token + '&access_token_secret=' + props.givenArguments.access_token_secret, { method: 'POST' });
      fetch(configuration.retweet_tweet + '?worker_id='+ props.workerid + '&tweet_id=' + tweet.tweet_id, { method: 'POST' });
      if (localTweet.retweet_count.includes('k')) {
        setRetweetEnabled(false);
      } else {
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
      props.handleRetweet(localTweet.rank,tweet.tweet_id);
    }
  };

  const handleLike = (tweet) => {
    if (likeEnabled) {
      //fetch(configuration.like_tweet + '?tweet_id=' + tweet.tweet_id + '&session_id=2&access_token=' + props.givenArguments.access_token + '&access_token_secret=' + props.givenArguments.access_token_secret, { method: 'POST' });
      fetch(configuration.like_tweet + '?worker_id='+ props.workerid + '&tweet_id=' + tweet.tweet_id, { method: 'POST' });
      if (localTweet.likes.includes('k')) {
        setLikeEnabled(false);
      } else {
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
      props.handleLike(localTweet.rank,tweet.tweet_id);
    }
  };

  const handleLinkClicked = (url,tweet_id,is_card) => {
    props.handleLinkClicked(url,tweet_id,is_card);
  };

  return (
    <div className="completeTweet">
      {
        localTweet.retweet_by !== ''
          ? <div className="TweetStateBanner"> Retweeted by: <b>{localTweet.retweet_by}</b> </div>
          : null
      }
      {
        localTweet.quoted_by !== ''
          ?
          <div>
            <div style={{ display: 'flex' }} className="TweetStateBannerQuote">
              <img style={{ paddingRight: '2%', paddingLeft: '1%' }} src={localTweet.quoted_by_actor_picture} alt={"User " + localTweet.quoted_by_actor_picture + '\'s profile picture.'} />
              <b style={{alignItems: 'right'}}>{localTweet.quoted_by}</b>&nbsp;{"@" + localTweet.quoted_by_actor_username + ' Quoted:'}</div>
            <div className="QuoteBody">{localTweet.quoted_by_text}</div>
          </div>
          : null
      }
      <div style={{display: 'flex'}} className={localTweet.quoted_by === '' ? 'TweetContent' : 'QuotedTweetContent'}>
        <img style={{alignItems: 'left'}} src={localTweet.actor_picture} alt={"User " + localTweet.actor_name + '\'s profile picture.'}
	  onError= {({ currentTarget }) => {
		  currentTarget.onerror = null; // prevents looping
		  //currentTarget.src=`/3925572_1_10.png`;
		  currentTarget.src=fallback;
	}}
	/>
        <div style={{ marginLeft: '5%'}}>
          <b>{localTweet.actor_name /* Line this up with actor photo */}</b>
          {' @' + localTweet.actor_username}
        </div>
      </div>
      <div className={localTweet.quoted_by === '' ? 'TweetContent' : 'QuotedTweetContent'}>
        <div style={{ marginBottom: '1%' }}>{localTweet.body}</div>
        {localTweet.urls !== ''
          ? <div className="TweetArticleContainer">

            <a href={localTweet.urls} rel="noopener noreferrer" target="_blank" onClick={() => handleLinkClicked(localTweet.urls,localTweet.tweet_id,'True')}>
            {
                localTweet.picture !== '' ? (
                    <img className="TweetImage" src={localTweet.picture} alt='Article' />
                ) : (
			localTweet.embedded_image !== '' ? (
				<img className="TweetImage" src={localTweet.embedded_image} alt='User posted' />
			) 
			:
                    	<img className="TweetImage" src={`/no-image.png`} alt='Article' />
                )
            }
            </a>
	    {localTweet.domain_present !== '' ? <div style={{ marginBottom: '1%', color:'#808080', fontWeight:'bold'}}>{localTweet.domain_present}</div> : null}
            {localTweet.picture_heading !== '' ?
              <div style={{ marginTop: '1%', marginBottom: '1%',fontWeight:'bold' }}>{localTweet.picture_heading}</div>
              : null}
            <div>{localTweet.picture_description}</div>
          </div>
          :
          localTweet.embedded_image !== ''
            ?
            <img className="TweetImage" src={localTweet.embedded_image} alt='User posted' />
            : null}
      </div>
      <div className="TweetFooter">
        <div className='retBtn' onClick={() => handleRetweet(localTweet)}><img className='retImg' src={retweetEnabled ? retUnclicked : retClicked} alt='' />{localTweet.retweet_count}</div>
        <div className='likeBtn' onClick={() => handleLike(localTweet)}><img className='likeImg' src={likeEnabled ? likeUnclicked : likeClicked} alt='' />{localTweet.likes}</div>
      </div>
    </div>
  )
}

export default Tweet;
