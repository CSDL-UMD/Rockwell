import React, { useEffect, useState } from 'react';
import Tweet from '../Tweet/Tweet_attn.js';
import configuration from '../../Configuration/config';
import rightArrow from './Icons/arrow-right.png';
import rightArrowEnabled from './Icons/Enabled_arrow.png';
import handleTotalResize from '../MainFeed/handleTotalResize';
import config from '../../Configuration/config';
import 'bootstrap/dist/css/bootstrap.css';
import OverlayTrigger from 'react-bootstrap/OverlayTrigger';
import Popover from 'react-bootstrap/Popover'

function MainAttentionPage(props) {
  const [attnMap, setAttnMap] = useState([0,0,0,0,0]);
  const [givenArguments, setGivenArguments] = useState({});
  const [sessionIdentifier, setSessionIdentifier] = useState('0');
  const [maxPageIdentifier, setMaxPageIdentifier] = useState('0');
  const [feedInformation, setFeedInformation] = useState({});
  const [endOfFeedCondition, setEndOfFeedCondition] = useState(false);

  useEffect(() => {
    const sleep = (time) => {
      return new Promise((resolve) => setTimeout(resolve, time));
    }
    const fetchTweets = (argumentObject) => {
      let worker_id_cookie = document.cookie.replace(/(?:(?:^|.*;\s*)_rockwellidentifierv2_\s*\=\s*([^;]*).*$)|^.*$/, "$1");
      //fetch(configuration.get_feed + '?access_token=' + argumentObject.access_token + '&access_token_secret=' + argumentObject.access_token_secret + '&worker_id=' + argumentObject.worker_id + '&attn=' + argumentObject.attn + '&page=' + argumentObject.page).then(resp => {
      //fetch(configuration.get_feed + '?random_indentifier=' + argumentObject.randomtokenszzzz + '&attn=' + argumentObject.attn + '&page=' + argumentObject.page + '&feedtype=' + argumentObject.feedtype).then(resp => {
      fetch(configuration.get_feed + '?worker_id=' + worker_id_cookie + '&attn=' + argumentObject.attn + '&page=' + argumentObject.page + '&feedtype=' + argumentObject.feedtype).then(resp => {
        return resp.json();
      }).then(value => {
        if (JSON.stringify(value) === '{}') {
          window.location.href = config.error + '?error=' + config.error_codes.no_tweets_attn_check;
        }
        setMaxPageIdentifier(value[value.length - 1]['max_pages']);
        setSessionIdentifier(value[value.length - 1]['session_id']);
        value.pop();
        setFeedInformation(value);
        sleep(500).then(() => {
          handleTotalResize();
        });
      }).catch(err => {
        window.location.href = config.error + '?error=' + config.error_codes.tweet_fetch_error_attn_check;
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

    const debounce = (fn, ms) => {
      let timer
      return _ => {
        clearTimeout(timer)
        timer = setTimeout(_ => {
          timer = null
          fn.apply(this, arguments);
        }, ms)
      };
    };

    const debouncedHandleResize = debounce(function handleResize() {
      handleTotalResize();
    }, 500);

    const urlArgs = getUrlArgs();
    setGivenArguments(urlArgs);
    fetchTweets(urlArgs);
    window.addEventListener('resize', debouncedHandleResize);
    return _ => {
      window.removeEventListener('resize', debouncedHandleResize);
    }
  }, [props]);

  const handleattncheck = (rank, answer) => {
    let attn_marked = Object.assign([], attnMap);
    if (answer === 'Y')
      attn_marked[rank - 1] = 1;
    else
      attn_marked[rank - 1] = 2;
    let all_marked = 1;
    for (let i = 0; i < attn_marked.length; i++) {
      if (attn_marked[i] == 0) {
        all_marked = 0;
        break;
      }
    }
    if (all_marked == 1)
      setEndOfFeedCondition(true);
    setAttnMap(attn_marked);
  };

  const popup = () =>(
    <Popover id = 'popover-positioned-top' style = {{color: 'red'}}>
      <Popover.Title as='h5'>
        Mark either yes or no for all given tweets to proceed to the next page
      </Popover.Title>
    </Popover>
  );

  const nextButtonClickedAttn = () => {
    console.log(maxPageIdentifier);
    //alert("Next Button Clicked");
    //fetch(configuration.database_attn_url + '?worker_id='+ givenArguments.worker_id + '&page=' + givenArguments.page + '&attnanswers=' + attnMap).then(resp => {
    //fetch(configuration.database_attn_url + '?random_indentifier='+ givenArguments.randomtokenszzzz + '&page=' + givenArguments.page + '&attnanswers=' + attnMap).then(resp => {
    fetch(configuration.database_attn_url + '?session_id='+ sessionIdentifier + '&page=' + givenArguments.page + '&attnanswers=' + attnMap).then(resp => {
        return resp.json();
      })
    //window.location.href = givenArguments.page === '4' ? '/complete' : '/feed?access_token=' + givenArguments.access_token + '&access_token_secret=' + givenArguments.access_token_secret + '&worker_id=' + givenArguments.worker_id + '&attn=0&page=' + (parseInt(givenArguments.page) + 1)
    //window.location.href = givenArguments.page === '4' ? '/complete' : '/feed?randomtokenszzzz=' + nextRandomIdentifier + '&attn=0&page=' + (parseInt(givenArguments.page) + 1)
    window.location.href = parseInt(givenArguments.page) === maxPageIdentifier ? '/complete' : '/feed?attn=0&page=' + (parseInt(givenArguments.page) + 1) + '&feedtype=' + givenArguments.feedtype
  };

  return (
    <div>
      <div className="Title">
        <h1 style={{ margin: '0' }}>Rockwell</h1>
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
                  <Tweet tweet={tweet} givenArguments={givenArguments} handleUserSelection={handleattncheck} />
                </div>
              ))
            }
            <div className="TopInstructions">
              <h4 style={{ margin: '0' }}>Once you are done, click on the button below</h4>
            </div>
          </div>

          <div className="BottomNavBar">
            { /* <Link to={isActive ? '/link-to-route' : '#'} /> */}
            <input type="image" alt="right arrow, next page button" disabled={!endOfFeedCondition ? 'disabled' : ''} src={!endOfFeedCondition ? rightArrow : rightArrowEnabled} className="rightImg" onClick={nextButtonClickedAttn}/>

            <div style = {endOfFeedCondition ? {pointerEvents: 'none'} : {}}>
              <OverlayTrigger placement={!endOfFeedCondition ? 'top' : ''} trigger = 'click' rootClose = {true} overlay={popup()}>
                <div className = "Trigger"/>
              </OverlayTrigger>
            </div>
          </div>
        </React.Fragment>
      }
    </div>
  )
}

export default MainAttentionPage;
