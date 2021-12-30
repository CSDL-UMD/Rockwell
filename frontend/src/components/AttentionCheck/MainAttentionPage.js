import React, { useEffect, useState } from 'react';
import { Form } from "react-bootstrap";
import { Link } from 'react-router-dom';
import Tweet from '../Tweet/Tweet_attn.js';
import configuration from '../../Configuration/config';
import rightArrow from './Icons/arrow-right.png';
import rightArrowEnabled from './Icons/Enabled_arrow.png';

function MainAttentionPage(props) {
  let tweet_pos = 1;
  let attn_marked = [0,0,0,0,0];
  const [givenArguments, setGivenArguments] = useState({});
  const [feedInformation, setFeedInformation] = useState({});
  const [endOfFeedCondition, setEndOfFeedCondition] = useState(false);

  useEffect(() => {

    const fetchTweets = (argumentObject) => {
      fetch(configuration.get_feed + '?access_token=' + argumentObject.access_token + '&access_token_secret=' + argumentObject.access_token_secret + '&worker_id=' + argumentObject.worker_id + '&attn=' + argumentObject.attn + '&page=' + argumentObject.page).then(resp => {
        return resp.json();
      }).then(value => {
        console.log(value);
        setFeedInformation(value);
      })
    }

    const getUrlArgs = () => {
      let originalArgs = props.location.search.substring(1).split('&');
      let returnObject = {};
      originalArgs.forEach(pair => {
        let temp = pair.split('=');
        returnObject[temp[0]] = temp[1];
      })
      return returnObject;
    }

    const urlArgs = getUrlArgs();
    setGivenArguments(urlArgs);
    fetchTweets(urlArgs);
  }, [props]);

  const onValueChange = (event) => {
    let answer = event.target.name.split('_')[0];
    let idx = event.target.name.split('_')[1];
    if(answer === 'Y')
      attn_marked[idx-1] = 1;
    else
      attn_marked[idx-1] = 2;
    let all_marked = 1;
    for (let i = 0; i < attn_marked.length; i++){
      if (attn_marked[i] === 0){
        all_marked = 0;
        break;
      }
    }
    if (all_marked == 1)
      setEndOfFeedCondition(true);
  };

  const incrementcount = () => {
    tweet_pos = tweet_pos + 1;
  };  

  //
  const handleattncheck = (rank,answer) => {
    if(answer === 'Y')
      attn_marked[rank-1] = 1;
    else
      attn_marked[rank-1] = 2;
    let all_marked = 1;
    for (let i = 0; i < attn_marked.length; i++){
      if (attn_marked[i] === 0){
        all_marked = 0;
        break;
      }
    }
    if (all_marked == 1)
      setEndOfFeedCondition(true);
  };  

  return (
    <div>
      <div className="Title">
        <h1 style={{ margin: '0' }}>Infodiversity</h1>
      </div>
      {JSON.stringify(feedInformation) === '{}'
        ?
        <div style={{ alignContent: 'center', textAlign: 'center' }}> Please wait while your attention check is loading.</div>
        :
        <React.Fragment>
          <div className="Feed">
            <div className="TopInstructions">
              <h5 style={{ margin: '0' }}>Please indicate whether the tweets below appeared on the previous screen of the survey:</h5>
            </div>
            {
              feedInformation.map(tweet => (
                <div key={JSON.stringify(tweet)}>
                <Tweet tweet={tweet} givenArguments={givenArguments} handleUserSelection={handleattncheck}/>
                </div>
              ))
            }
            <div className="TopInstructions">
              <h4 style={{ margin: '0' }}>Once you are done, click on the button below</h4>
            </div>
          </div>

          <div className="BottomNavBar">
            <Link to={'/feed?access_token=' + givenArguments.access_token + '&access_token_secret=' + givenArguments.access_token_secret + '&worker_id=' + givenArguments.worker_id + '&attn=0&page=' + (parseInt(givenArguments.page) + 1)}>
              <input type="image" alt="right arrow, next page button" disabled={!endOfFeedCondition ? 'disabled' : ''} src={!endOfFeedCondition ? rightArrow : rightArrowEnabled} className="rightImg" />
            </Link>
          </div>
        </React.Fragment>
      }
    </div>
  )
}

export default MainAttentionPage;