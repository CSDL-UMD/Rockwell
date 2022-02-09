import React from 'react';
import './Tweet.css';
import { useEffect, useState } from 'react';

function Tweet(props) {
  const [localTweet, setLocalTweet] = useState({});

  useEffect(() => {
    if (props.tweet)
      setLocalTweet(props.tweet)
  }, [props.tweet]);

  const yesbtnclicked = (event) => {
    document.getElementById("yes_button_"+localTweet.rank).style.backgroundColor = "yellow"
    document.getElementById("no_button_"+localTweet.rank).style.backgroundColor = "white"
    props.handleUserSelection(localTweet.rank,'Y');
  };

  const nobtnclicked = (event) => {
    document.getElementById("no_button_"+localTweet.rank).style.backgroundColor = "yellow"
    document.getElementById("yes_button_"+localTweet.rank).style.backgroundColor = "white"
    props.handleUserSelection(localTweet.rank,'N');
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
        <img style={{alignItems: 'left'}} src={localTweet.actor_picture} alt={"User " + localTweet.actor_name + '\'s profile picture.'} />
        <div style={{ marginLeft: '5%'}}>
          <b>{localTweet.actor_name /* Line this up with actor photo */}</b>
          {' @' + localTweet.actor_username}
        </div>
      </div>
      <div className={localTweet.quoted_by === '' ? 'TweetContent' : 'QuotedTweetContent'}>
        <div style={{ marginBottom: '1%' }}>{localTweet.body}</div>
        {localTweet.urls !== ''
          ? <div className="TweetArticleContainer">
            {localTweet.picture_heading !== '' ?
              <div style={{ marginTop: '1%', marginBottom: '1%' }}>{localTweet.picture_heading}</div>
              : null}
            {localTweet.picture !== '' ?
              <img className="TweetImage" src={localTweet.picture} alt='Article' />
              : localTweet.urls}
            <div>{localTweet.picture_description}</div>
          </div>
          :
          localTweet.embedded_image !== ''
            ?
            <img className="TweetImage" src={localTweet.embedded_image} alt='User posted' />
            : null}
      </div>
      <div className="TweetFooterAttn">
        <p className="attnpara"><strong>Did this tweet appear on the previous screen?</strong></p>
        <div className="attnbuttondiv">
        <button className="attnbutton" id={"yes_button_"+localTweet.rank} onClick={() => yesbtnclicked()}>Yes</button>
        <button className="attnbutton" id={"no_button_"+localTweet.rank} onClick={() => nobtnclicked()}>No</button>
        </div>
      </div>
    </div>
  )
}

export default Tweet;
