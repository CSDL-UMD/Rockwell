import React from 'react';
import './Tweet.css';
import configuration from '../../Configuration/config';
function Tweet(props) {
  const handleRetweet = (tweet) => {
    fetch(configuration.retweet_tweet + '?tweet_id=' + tweet.tweet_id + '&session_id=2&access_token=' + props.givenArguments.access_token + '&access_token_secret=' + props.givenArguments.access_token_secret, {method: 'POST'});
    try {
      let amount = parseInt(tweet.retweet_count) + 1;
      tweet.retweet_count = String(amount);
    } catch {
      console.log("Not an integer.");
    }
  };

  const handleLike = (tweet) => {
    fetch(configuration.like_tweet + '?tweet_id=' + tweet.tweet_id + '&session_id=2&access_token=' + props.givenArguments.access_token + '&access_token_secret=' + props.givenArguments.access_token_secret, {method: 'POST'});
    try { // Wont work as we need to update main object and update state to get the rerender of numbers.
          // useEffect, store prop in local state and only rerender on prop change (dep array)
      let amount = parseInt(tweet.likes) + 1;
      tweet.likes = String(amount);
    } catch {
      console.log("Not an integer.");
    }
  };

  const handleTotalResize = () => {
    let res = document.getElementsByClassName('TweetImage'); 
    Object.keys(res).forEach(image => {
      console.log(getImageHeightRatio(res[image].width));
      res[image].height = res[image].width * getImageHeightRatio(res[image].width);
    });
  };

  const imageResizerOnLoad = (image) => {
    image.target.height = image.target.width * getImageHeightRatio(image.target.width);
  };

  const getImageHeightRatio = (width) => {
    if (width > 800)
      return 0.65;
    if (width > 500)
      return 0.60;
    else 
      return 0.60;
  }

  window.addEventListener('resize', handleTotalResize);

  return (
    <div class="completeTweet">
      {
        props.tweet.user_retweet !== 'False'
          ? <div className="TweetStateBanner"> Retweeted by: {props.tweet.retweet_by} </div>
          : null
      }
      {
        props.tweet.quoted_by !== ''
          ? 
          <div>
          <div className="TweetStateBanner"> Quoted by: {props.tweet.quoted_by} </div>
          <div className="QuoteBody">{props.tweet.quoted_by_text}</div>
          </div>
          : null
      }
      <div className="TweetTitle">
        <img style={{ justifySelf: 'flex-start' }} src={props.tweet.actor_picture} alt={"User " + props.tweet.actor_name + '\'s profile picture.'} />
        <div style={{ marginLeft: 'auto' }}>
          {props.tweet.actor_name}
          {' @' + props.tweet.actor_username}
        </div>
      </div>
      <div className="TweetContent">
        <div style={{ marginBottom: '1%' }}>{props.tweet.body + ' ' + props.tweet.expanded_urls}</div>
        {props.tweet.picture !== ''
          ? <div className="TweetArticleContainer">
            <div style={{ marginTop: '1%', marginBottom: '1%' }}>{props.tweet.picture_heading}</div>
            <img className = "TweetImage" onLoad={imageResizerOnLoad} src={props.tweet.picture} alt='Article' />
            <div>{props.tweet.picture_description}</div>
          </div>
          :
          props.tweet.embeded_image !== ''
            ?
            <div>
              <img className = "TweetImage" onLoad={imageResizerOnLoadd} src={props.tweet.embedded_image} alt='User posted' />
            </div>
            : null}
      </div>
      <div className="TweetFooter">
        <div style={{ float: 'left', marginLeft: '2%' }}>{<button onClick={() => handleRetweet(props.tweet)}>{'Retweets: ' + props.tweet.retweet_count}</button>}</div>
        <div style={{ marginLeft: 'auto', marginRight: '2%' }}><button onClick={() => handleLike(props.tweet)}>{'Likes: ' + props.tweet.likes}</button></div>

      </div>
    </div>
  )
}

export default Tweet;
