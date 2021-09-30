import React from 'react';
import './Tweet.css';
function Tweet(props) {
    return (
        <div class="completeTweet">
            <div className="TweetTitle">
                {props.name}
            </div>
            {props.content}
        </div>
    )
}

export default Tweet;
