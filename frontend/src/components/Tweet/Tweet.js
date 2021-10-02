import React from 'react';
import './Tweet.css';
function Tweet(props) {
    return (
        <div class="completeTweet">
            <div style={{ display: 'flex', flex: '100%' }} className="TweetTitle">
                <img style={{alignItems: 'flex-start'}} src={props.tweet.actor_picture} />
                <div style={{flex:'flex-end'}}>{props.tweet.actor_name + '@' + props.tweet.actor_username}</div>
            </div>
            <div className="TweetContent">
                {props.tweet.body}
            </div>
            <div className="footer">
                <div style={{display: 'inline-block', float:'left', marginLeft: '2%'}}>{'Retweets: ' + props.tweet.retweet_count}</div>
                <div style={{display: 'inline-block'}}></div>
                <div style={{display: 'inline-block', float: 'right', marginRight: '2%'}}>{'Likes: ' + props.tweet.likes}</div>

            </div>
        </div>
    )
}

export default Tweet;
