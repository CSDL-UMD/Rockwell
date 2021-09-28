import React from 'react';
import './Tweet.css';
function Tweet(props) {
    let renderFirst = false;
    return (
        <div class="completeTweet">
            <div className="TweetTitle">
                {props.name}
            </div>
            {renderFirst ? 
            props.content1 :
            props.content2}
        </div>
    )
}

export default Tweet;
