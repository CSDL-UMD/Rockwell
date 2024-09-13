import React, { useEffect, useState } from 'react';
import Tweet from '../Tweet/Tweet';
import CarouselModal from '../Carousel/Components/CarouselModal';
import configuration from '../../Configuration/config';
import handleTotalResize from './handleTotalResize';
import rightArrow from './Icons/arrow-right.png';
import rightArrowEnabled from './Icons/Enabled_arrow.png';
import config from '../../Configuration/config';
import Modal from 'react-bootstrap/Modal';
import './MainFeed.css';

function MainFeed(props) {
  const [givenArguments, setGivenArguments] = useState({});
  const [showEndModal, setShowEndModal] = useState(false);
  const [feedInformation, setFeedInformation] = useState({});
  const [workeridIdentifier, setWorkeridIdentifier] = useState('0');
  const [sessionIdentifier, setSessionIdentifier] = useState('0');
  const [maxPageIdentifier, setMaxPageIdentifier] = useState('0');
  const [currentPageIdentifier, setCurrentPageIdentifier] = useState(0);
  const [minimumFeedTimeCondition, setMinimumFeedTimeCondition] = useState(false);
  const [endOfFeedCondition, setEndOfFeedCondition] = useState(false);
  const [starTimeInformation, setStarTimeInformation] = useState(0);
  const [starTimeGlobalInformation, setStarTimeGlobalInformation] = useState(0);
  const [tweetViewTimeStamps, setTweetViewTimeStamps] = useState([]);
  const [tweetRetweets, setTweetRetweets] = useState([]);
  const [tweetLikes, setTweetLikes] = useState([]);
  const [tweetLinkClicks, setTweetLinkClicks] = useState([]);

  async function beginTimer() {
    await new Promise(r => setTimeout(r, 9));
    setMinimumFeedTimeCondition(true)
  }

  useEffect(() => {
    let startTime = Date.now();
    let startTimeGlobal = Date.now();
    setStarTimeGlobalInformation(startTimeGlobal);
    let feedSize = [];
    let currentTweet = [1, 0];
    let hasReachedEndOfFeed = false;
    let tweetViewTimeStamps_local = [];
    let tweetViewTimeStamps_global = [];
    let feedslocal = [];
    let page_set = 0;
    let page_current = 0;
    let totalFeedLength = 0;
    let feedtype_set = '';
    let max_page = 0;
    let canFetchNewFeed = true;

    const handleFirstRender = () => {
      let result = handleTotalResize();
      feedSize = (calculateFeedSize(result, window.innerHeight));
      totalFeedLength = result.length;
      tweetViewTimeStamps_local.push([1,0]);
      //window.scrollTo(0, 0);
      startTime = Date.now();
      setStarTimeInformation(startTime);
      if (page_set !== 0) {
        beginTimer();
      }
    };

    const fetchTweets = () => {
      let worker_id_cookie = document.cookie.replace(/(?:(?:^|.*;\s*)_rockwellidentifierv2_\s*\=\s*([^;]*).*$)|^.*$/, "$1");
      setWorkeridIdentifier(worker_id_cookie);
      //fetch(configuration.get_feed + '?access_token=' + argumentObject.access_token + '&access_token_secret=' + argumentObject.access_token_secret + '&user_id=' + argumentObject.user_id +  '&screen_name=' + argumentObject.screen_name + '&worker_id=' + argumentObject.worker_id + '&attn=' + argumentObject.attn + '&page=' + argumentObject.page + '&feedtype=' + argumentObject.feedtype).then(resp => {
      fetch(configuration.get_feed + '?worker_id=' + worker_id_cookie + '&attn=1&page=' + page_set + '&feedtype=' + feedtype_set).then(resp => {
        return resp.json();
      }).then(value => {
        if (value[value.length - 1]['anything_present'] == 'NO') {
          //window.location.href = config.error + '?error=' + config.error_codes.no_tweets_main_feed;
          setEndOfFeedCondition(true);
        }
        setMaxPageIdentifier(value[value.length - 1]['max_pages']);
        setSessionIdentifier(value[value.length - 1]['session_id']);
        value.pop();
        //let cookieValue = document.cookie.replace(/(?:(?:^|.*;\s*)worker_id\s*\=\s*([^;]*).*$)|^.*$/, "$1");
        //console.log(cookieValue);
        for (let i = 0; i < value.length; i++) {
          feedslocal.push(value[i]);
        }
        console.log(feedslocal);
        setFeedInformation(feedslocal);
        const sleep = (time) => {
          return new Promise((resolve) => setTimeout(resolve, time));
        }
        sleep(500).then(() => {
          handleFirstRender(); // Add ifs for return size == 0 just in case 500 ms is not enough for firstRender.
        });
        sleep(500).then(() => {
          handleFirstRender(); // Add ifs for return size == 0 just in case 500 ms is not enough for firstRender.
        });
        sleep(500).then(() => {
          handleFirstRender(); // Add ifs for return size == 0 just in case 500 ms is not enough for firstRender.
        });
      }).catch(err => {
        //window.location.href = config.error + '?error=' + config.error_codes.tweet_fetch_error_main_feed;
      })
    }

    const fetchTweetsagain = () => {
      let worker_id_cookie = document.cookie.replace(/(?:(?:^|.*;\s*)_rockwellidentifierv2_\s*\=\s*([^;]*).*$)|^.*$/, "$1");
      //fetch(configuration.get_feed + '?access_token=' + argumentObject.access_token + '&access_token_secret=' + argumentObject.access_token_secret + '&user_id=' + argumentObject.user_id +  '&screen_name=' + argumentObject.screen_name + '&worker_id=' + argumentObject.worker_id + '&attn=' + argumentObject.attn + '&page=' + argumentObject.page + '&feedtype=' + argumentObject.feedtype).then(resp => {
      fetch(configuration.get_feed + '?worker_id=' + worker_id_cookie + '&attn=1&page=1&feedtype=S').then(resp => {
        return resp.json();
      }).then(value => {
        value.pop();
        for (let i = 0; i < value.length; i++) {
          feedslocal.push(value[i]);
        }
        console.log(feedslocal)
        setFeedInformation(feedslocal);
        //setTweetViewTimeStamps(tempObject);
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

    document.addEventListener("visibilitychange", event => {
      const time = Date.now()
      if (document.visibilityState === "visible") {
        //handleTweetViewTracking(-2,feedSize,currentTweet,startTime);
        tweetViewTimeStamps_global.push([-2, time - startTime]);
        setTweetViewTimeStamps(tweetViewTimeStamps_global);
        //let tempObject = Object.assign([], tweetViewTimeStamps);
        //tempObject.push([-2, time - startTime]);
        //setTweetViewTimeStamps(tempObject);
      } else {
        //handleTweetViewTracking(-1,feedSize,currentTweet,startTime);
        tweetViewTimeStamps_global.push([-1, time - startTime]);
        setTweetViewTimeStamps(tweetViewTimeStamps_global);
        //let tempObject = Object.assign([], tweetViewTimeStamps);
        //tempObject.push([-1, time - startTime]);
        //setTweetViewTimeStamps(tempObject);
      }
    })

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

    const handleTweetViewTracking = (clientHeight) => {
      const time = Date.now();

      if (clientHeight < 0) {
        tweetViewTimeStamps_local.push([clientHeight, time - startTime]);
        tweetViewTimeStamps_global.push([clientHeight, time - startTimeGlobal]);
        setTweetViewTimeStamps(tweetViewTimeStamps_global);
        //let tempObject = Object.assign([], tweetViewTimeStamps);
        //tempObject.push([clientHeight, time - startTime]);
        //setTweetViewTimeStamps(tempObject);
        return null;
      }

      if (!feedSize.length) {
        return null;
      }

      const position = window.pageYOffset + clientHeight * 0.75; // Need to account for the bottom bar height
      let feedPosition = feedSize[0];
      let feedIndex = 1;
      //console.log(position);
      //console.log(feedPosition);
      while (position > feedPosition) {
        feedPosition += feedSize[feedIndex];
        feedIndex++;
      }
      feedIndex--;
      if (feedIndex === currentTweet[0]) {
        return null;
      }

      //let tempObject = Object.assign([], tweetViewTimeStamps);
      //tempObject.push([feedIndex, time - startTime]);
      //setTweetViewTimeStamps(tempObject);
      //console.log(tweetViewTimeStamps);
      tweetViewTimeStamps_local.push([feedIndex, time - startTime]);
      tweetViewTimeStamps_global.push([feedIndex, time - startTimeGlobal]);
      setTweetViewTimeStamps(tweetViewTimeStamps_global);
      //console.log(tweetViewTimeStamps);
      //console.log(feedIndex);
      //console.log(time - startTimeGlobal);
      return [feedIndex, time - startTime];
    };

    const debouncedHandleResize = debounce(function handleResize() {
      let res = handleTotalResize();
      feedSize = (calculateFeedSize(res, window.innerHeight));
    }, 500);

    const debouncedHandleScroll = debounce(function handleScroll() {
      const res = handleTweetViewTracking(window.innerHeight);
      //console.log(res);
      if (res !== null) {
        currentTweet = res;
  console.log(res);
        //console.log('Current Tweet: ' + res[0], ' Time: ' + res[1]);
        if (res[0] > (page_set*10 + 2)) {
          page_set = page_set + 1;
    console.log(page_set);
    console.log("FETCHING TWEETS!!!!");
          fetchTweets();
          //hasReachedEndOfFeed = true;
          //setEndOfFeedCondition(true);
          //console.log(tweetViewTimeStamps_local);
        }
        if ((res[0] % 10) == 0){
          page_current = page_current + 1;
          setCurrentPageIdentifier(page_current);
        } 
        //if ((totalFeedLength - res[0]) < 8 && canFetchNewFeed){
        //  canFetchNewFeed = false;
        //  page_set = page_set + 1;
        //  const getnewfeedtimer = setTimeout(() => {
        //    canFetchNewFeed = true;
        //  }, 5000);
        //  fetchTweets();
        //}
      }
      
    }, 1);

    const urlArgs = getUrlArgs();
    setGivenArguments(urlArgs);
    page_set = parseInt(urlArgs.page);
    setCurrentPageIdentifier(page_set);
    feedtype_set = urlArgs.feedtype;
    //startTime = Date.now();
    fetchTweets();
    window.addEventListener('resize', debouncedHandleResize);
    window.addEventListener('scroll', debouncedHandleScroll);
    return _ => {
      window.removeEventListener('resize', debouncedHandleResize);
      window.removeEventListener('scroll', debouncedHandleScroll);
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.location.search]);

  const calculateFeedSize = (tweetSizeArray, clientHeight) => {
    let feedSizeArray = Object.assign([], tweetSizeArray);
    let res = document.getElementsByClassName('TopInstructions');
    if (res.length) {
      feedSizeArray.unshift(res[0].clientHeight + (clientHeight * 0.07));
      for (let i = 0; i < feedSizeArray.length; i++) {
        feedSizeArray[i] += (clientHeight * 0.01);
      }
    }
    return feedSizeArray;
  };

  const handleRetweet = (feedIndex,tweet_id) => {
    const time = Date.now();
    let tempObject = Object.assign([], tweetRetweets);
    tempObject.push([tweet_id,(time - starTimeGlobalInformation)]);
    setTweetRetweets(tempObject);
  };

  const handleLike = (feedIndex,tweet_id) => {
    const time = Date.now();
    let tempObject = Object.assign([], tweetLikes);
    tempObject.push([tweet_id,(time - starTimeGlobalInformation)]);
    setTweetLikes(tempObject);
  };

  const handleLinkClicked = (url,tweet_id,is_card) => {
    let startTimeLinkClicked = starTimeGlobalInformation;
    const timeLinkClicked = Date.now();
    let tempObject = Object.assign([], tweetLinkClicks);
    tempObject.push([url, tweet_id, is_card, timeLinkClicked - startTimeLinkClicked]);
    setTweetLinkClicks(tempObject);
  };  

  const nextButtonClicked = () => {
    setShowEndModal(true);
    //fetch(configuration.database_attn_url + '?worker_id='+ workeridIdentifier + '&page=' + givenArguments.page + '&tweetRetweets=' + tweetRetweets + '&tweetLikes=' + tweetLikes + '&tweetLinkClicks=' + tweetLinkClicks + '&tweetViewTimeStamps=' + tweetViewTimeStamps).then(resp => {
    //fetch(configuration.database_url + '?random_indentifier='+ givenArguments.randomtokenszzzz + '&page=' + givenArguments.page + '&tweetRetweets=' + tweetRetweets + '&tweetLikes=' + tweetLikes + '&tweetLinkClicks=' + tweetLinkClicks + '&tweetViewTimeStamps=' + tweetViewTimeStamps).then(resp => {
    //fetch(configuration.database_url + '?worker_id='+ workeridIdentifier + '&page=' + givenArguments.page + '&tweetRetweets=' + tweetRetweets + '&tweetLikes=' + tweetLikes + '&tweetLinkClicks=' + tweetLinkClicks + '&tweetViewTimeStamps=' + tweetViewTimeStamps).then(resp => {
    fetch(configuration.database_attn_url,{method: 'post', headers: {'Content-Type':'application/json'}, body: JSON.stringify({"worker_id":workeridIdentifier,"page":givenArguments.page,"tweetRetweets":tweetRetweets,"tweetLikes":tweetLikes,"tweetLinkClicks":tweetLinkClicks,"tweetViewTimeStamps":tweetViewTimeStamps})}).then(resp => {
        //return resp.json();
        window.location.href = '/complete';
    })
    //window.location.href = '/attention?access_token=' + givenArguments.access_token + '&access_token_secret=' + givenArguments.access_token_secret + '&worker_id=' + givenArguments.worker_id + '&attn=1&page=' + givenArguments.page
    //window.location.href = '/attention?randomtokenszzzz=' + nextRandomIdentifier + '&attn=1&page=' + givenArguments.page
    //window.location.href = '/complete';
    //document.getElementById('root').style.filter = 'blur(5px)'
    //alert("Thank you for participating! Please close this window and return to the survey.")
  };

  return (
    <div>
      <div className="Title">
        <h1 style={{ margin: '0' }}>Rockwell</h1>
      </div>
      {JSON.stringify(feedInformation) === '{}'
        ?
        <div style={{ alignContent: 'center', textAlign: 'center' }}> Please wait while your feed is loading. It might take a few seconds to load. Please do not reload the page.</div>
        :
        <React.Fragment>
          <div className="Feed">
            <div className="TopInstructions">
	      <p style={{ margin: '3em 1em 1em 1em' }}><i>We would like to again ask you to look at some social media content.</i></p>
              <p style={{ margin: '3em 1em 1em 1em' }}><i>Please scroll through the content below and interact with it as if you were on Twitter --- for example, by reading as well as clicking on links, liking, and/or retweeting content of interest. <strong>Be sure to spend several minutes reading and interacting with content as you normally would.</strong> We will ask you questions about your actions later.</i></p>   
            </div>
            {
              feedInformation.map(tweet => (
                <Tweet key={JSON.stringify(tweet)} tweet={tweet} givenArguments={givenArguments} workerid={workeridIdentifier} handleRetweet={handleRetweet} handleLike={handleLike} handleLinkClicked={handleLinkClicked}/>
              ))
            }
            <div class={!endOfFeedCondition ? 'loader' : 'loaderHidden'}></div>
            <div className={!endOfFeedCondition ? 'TopInstructionsHidden' : 'TopInstructions'}>
              <h4 style={{ margin: '0' }}>End of feed reached. Once you are done click on the button below.</h4>
            </div>
          </div>

          <div className="BottomNavBar">
            <input type="image" alt="right arrow, next page button" src={rightArrowEnabled} className="rightImg" onClick={nextButtonClicked}/>
          </div>

        </React.Fragment>
      }
      <Modal show={showEndModal} size='m'>
        <Modal.Body>
                <p> Please wait while your progress is being saved. This could take as long as 30 seconds or more. Please be patient and do not reload the page. </p>
        </Modal.Body>
      </Modal>
    </div>
  );
}

export default MainFeed;

