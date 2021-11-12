import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Tweet from '../Tweet/Tweet';
import configuration from '../../Configuration/config';

function MainAttentionPage(props) {
  const [givenArguments, setGivenArguments] = useState({});
  const [feedInformation, setFeedInformation] = useState({});

  useEffect(() => {

    const fetchTweets = (argumentObject) => {
      fetch(configuration.get_feed + '?access_token=' + argumentObject.access_token + '&access_token_secret=' + argumentObject.access_token_secret + '&worker_id=' + argumentObject.worker_id + '&attn=' + argumentObject.attn + '&page=' + argumentObject.page).then(resp => {
        return resp.json();
      }).then(value => {
        console.log(value);
        setFeedInformation(value);
        const sleep = (time) => {
          return new Promise((resolve) => setTimeout(resolve, time));
        }
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

  const calculateFeedSize = (tweetSizeArray, clientHeight) => {
    let feedSizeArray = Object.assign([], tweetSizeArray);
    let res = document.getElementsByClassName('TopInstructions');
    if (res.length) {
      feedSizeArray.unshift(res[0].clientHeight + (clientHeight * 0.07)); // Might need to be between 7-9% here, 1% more than what is listed here because of next loop
      for (let i = 0; i < feedSizeArray.length; i++) {
        feedSizeArray[i] += (clientHeight * 0.01);
      }
    }
    return feedSizeArray;
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
        <div className="Feed">
          <div className="TopInstructions">
            <h5 style={{ margin: '0' }}>Please indicate whether the tweets below appeared on the previous screen of the survey:</h5>
          </div>
          {
            feedInformation.map(tweet => (
              <Tweet key={JSON.stringify(tweet)} tweet={tweet} givenArguments={givenArguments} />
            ))
          }
          <form>
            <div className="radio">
              <label>
                <input
                  type="radio"
                  name="isPublished"
                  value="true"/>
                Yes
              </label>
            </div>
            <div className="radio">
              <label>
                <input
                  type="radio"
                  name="isPublished"
                  value="false"/>
                No
              </label>
            </div>
          </form>
          <div className="TopInstructions">
            <h4 style={{ margin: '0' }}>Once you are done, click on the button below</h4>
          </div>
          <div>
            <Link to={'/feed?access_token=' + givenArguments.access_token + '&access_token_secret=' + givenArguments.access_token_secret + '&worker_id=' + givenArguments.worker_id + '&attn=0&page=' + (parseInt(givenArguments.page) + 1)}>Next</Link>
          </div>
        </div>
      }
    </div>
  )
}

export default MainAttentionPage;