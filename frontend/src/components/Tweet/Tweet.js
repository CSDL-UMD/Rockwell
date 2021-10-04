import React from 'react';
import './Tweet.css';
function Tweet(props) {
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
            <img className="TweetImage" src={props.tweet.picture} alt='Article' />
            <div>{props.tweet.picture_description}</div>
          </div>
          :
          props.tweet.embeded_image !== ''
            ?
            <div>
              <img className="TweetImage" src={props.tweet.embedded_image} alt='User posted' />
            </div>
            : null}
      </div>
      <div className="TweetFooter">
        <div style={{ float: 'left', marginLeft: '2%' }}>{'Retweets: ' + props.tweet.retweet_count}</div>
        <div style={{ marginLeft: 'auto', marginRight: '2%' }}>{'Likes: ' + props.tweet.likes}</div>

      </div>
    </div>
  )
}

export default Tweet;
