import React, { useEffect, useState } from 'react';
import Tweet from '../Tweet/Tweet';
import CarouselModal from '../Carousel/Components/CarouselModal';
import configuration from '../../Configuration/config';
import handleTotalResize from './handleTotalResize';
import rightArrow from './Icons/arrow-right.png';
import rightArrowEnabled from './Icons/Enabled_arrow.png';
import config from '../../Configuration/config';
import './MainFeed.css';

function MainFeed(props) {
  const [showInstructionCarousel, setShowInstructionCarousel] = useState(false);
  const [givenArguments, setGivenArguments] = useState({});
  const [feedInformation, setFeedInformation] = useState({});
  const [sessionIdentifier, setSessionIdentifier] = useState('0');
  const [maxPageIdentifier, setMaxPageIdentifier] = useState('0');
  const [minimumFeedTimeCondition, setMinimumFeedTimeCondition] = useState(false);
  const [endOfFeedCondition, setEndOfFeedCondition] = useState(false);
  const [starTimeInformation, setStarTimeInformation] = useState(0);
  const [tweetViewTimeStamps, setTweetViewTimeStamps] = useState([]);
  const [tweetRetweets, setTweetRetweets] = useState([]);
  const [tweetLikes, setTweetLikes] = useState([]);
  const [tweetLinkClicks, setTweetLinkClicks] = useState([]);

  async function beginTimer() {
    await new Promise(r => setTimeout(r, 10000));
    setMinimumFeedTimeCondition(true)
  }

  useEffect(() => {
    let startTime = Date.now();
    let feedSize = [];
    let currentTweet = [1, 0];
    let hasReachedEndOfFeed = false;
    let tweetViewTimeStamps_local = []

    const handleFirstRender = (argumentObject) => {
      let result = handleTotalResize();
      feedSize = (calculateFeedSize(result, window.innerHeight));
      tweetViewTimeStamps_local.push([1,0]);
      window.scrollTo(0, 0);
      startTime = Date.now();
      setStarTimeInformation(startTime);
      if (parseInt(argumentObject.page) !== 0) {
        beginTimer();
      }
    };

    const fetchTweets = (argumentObject) => {
      let worker_id_cookie = document.cookie.replace(/(?:(?:^|.*;\s*)_rockwellidentifierv2_\s*\=\s*([^;]*).*$)|^.*$/, "$1");
      //fetch(configuration.get_feed + '?access_token=' + argumentObject.access_token + '&access_token_secret=' + argumentObject.access_token_secret + '&user_id=' + argumentObject.user_id +  '&screen_name=' + argumentObject.screen_name + '&worker_id=' + argumentObject.worker_id + '&attn=' + argumentObject.attn + '&page=' + argumentObject.page + '&feedtype=' + argumentObject.feedtype).then(resp => {
      fetch(configuration.get_feed + '?worker_id=' + worker_id_cookie + '&attn=' + argumentObject.attn + '&page=' + argumentObject.page + '&feedtype=' + argumentObject.feedtype).then(resp => {
        return resp.json();
      }).then(value => {
        if (JSON.stringify(value) === '{}') {
          window.location.href = config.error + '?error=' + config.error_codes.no_tweets_main_feed;
        }
        setMaxPageIdentifier(value[value.length - 1]['max_pages']);
        setSessionIdentifier(value[value.length - 1]['session_id']);
        value.pop();
        //let cookieValue = document.cookie.replace(/(?:(?:^|.*;\s*)worker_id\s*\=\s*([^;]*).*$)|^.*$/, "$1");
        //console.log(cookieValue);
        setFeedInformation(value);
        const sleep = (time) => {
          return new Promise((resolve) => setTimeout(resolve, time));
        }
        sleep(500).then(() => {
          handleFirstRender(argumentObject); // Add ifs for return size == 0 just in case 500 ms is not enough for firstRender.
        });
      }).catch(err => {
        window.location.href = config.error + '?error=' + config.error_codes.tweet_fetch_error_main_feed;
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
        tweetViewTimeStamps_local.push([-2, time - startTime]);
        setTweetViewTimeStamps(tweetViewTimeStamps_local);
        //let tempObject = Object.assign([], tweetViewTimeStamps);
        //tempObject.push([-2, time - startTime]);
        //setTweetViewTimeStamps(tempObject);
      } else {
        //handleTweetViewTracking(-1,feedSize,currentTweet,startTime);
        tweetViewTimeStamps_local.push([-1, time - startTime]);
        setTweetViewTimeStamps(tweetViewTimeStamps_local);
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
        setTweetViewTimeStamps(tweetViewTimeStamps_local);
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

      while (position > feedPosition && feedIndex < 11) {
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
      setTweetViewTimeStamps(tweetViewTimeStamps_local);
      console.log(tweetViewTimeStamps);
      return [feedIndex, time - startTime];
    };

    const debouncedHandleResize = debounce(function handleResize() {
      let res = handleTotalResize();
      feedSize = (calculateFeedSize(res, window.innerHeight));
    }, 500);

    const debouncedHandleScroll = debounce(function handleScroll() {
      const res = handleTweetViewTracking(window.innerHeight);
      if (res !== null) {
        currentTweet = res;
        console.log('Current Tweet: ' + res[0], ' Time: ' + res[1]);
      if (res[0] === 10 && !hasReachedEndOfFeed) {
        hasReachedEndOfFeed = true;
        setEndOfFeedCondition(true);
        console.log(tweetViewTimeStamps_local);
      }
      }
      
    }, 1);

    const urlArgs = getUrlArgs();
    setGivenArguments(urlArgs);
    fetchTweets(urlArgs);
    urlArgs.page === '0' ? handleShowInstructionCarousel() : setShowInstructionCarousel(false);
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

  const handleCloseInstructionCarousel = () => {
    setShowInstructionCarousel(false);
    beginTimer();
    document.getElementById('root').style.filter = 'blur(0px)'
  };

  const handleShowInstructionCarousel = () => {
    setShowInstructionCarousel(true);
    document.getElementById('root').style.filter = 'blur(5px)'
  };

  const handleRetweet = (feedIndex) => {
    let tempObject = Object.assign([], tweetRetweets);
    tempObject.push(feedIndex);
    setTweetRetweets(tempObject);
  };

  const handleLike = (feedIndex) => {
    let tempObject = Object.assign([], tweetLikes);
    tempObject.push(feedIndex);
    setTweetLikes(tempObject);
  };

  const handleLinkClicked = (url,tweet_id,is_card) => {
    let startTimeLinkClicked = starTimeInformation;
    const timeLinkClicked = Date.now();
    let tempObject = Object.assign([], tweetLinkClicks);
    tempObject.push([url, tweet_id, is_card, timeLinkClicked - startTimeLinkClicked]);
    setTweetLinkClicks(tempObject);
  };  

  const nextButtonClicked = () => {
    //fetch(configuration.database_url + '?worker_id='+ givenArguments.worker_id + '&page=' + givenArguments.page + '&tweetRetweets=' + tweetRetweets + '&tweetLikes=' + tweetLikes + '&tweetLinkClicks=' + tweetLinkClicks + '&tweetViewTimeStamps=' + tweetViewTimeStamps).then(resp => {
    //fetch(configuration.database_url + '?random_indentifier='+ givenArguments.randomtokenszzzz + '&page=' + givenArguments.page + '&tweetRetweets=' + tweetRetweets + '&tweetLikes=' + tweetLikes + '&tweetLinkClicks=' + tweetLinkClicks + '&tweetViewTimeStamps=' + tweetViewTimeStamps).then(resp => {
    fetch(configuration.database_url + '?session_id='+ sessionIdentifier + '&page=' + givenArguments.page + '&tweetRetweets=' + tweetRetweets + '&tweetLikes=' + tweetLikes + '&tweetLinkClicks=' + tweetLinkClicks + '&tweetViewTimeStamps=' + tweetViewTimeStamps).then(resp => {
        return resp.json();
      })
    //window.location.href = '/attention?access_token=' + givenArguments.access_token + '&access_token_secret=' + givenArguments.access_token_secret + '&worker_id=' + givenArguments.worker_id + '&attn=1&page=' + givenArguments.page
    //window.location.href = '/attention?randomtokenszzzz=' + nextRandomIdentifier + '&attn=1&page=' + givenArguments.page
    window.location.href = '/attention?attn=1&page=' + givenArguments.page + '&feedtype=' + givenArguments.feedtype
  };

  return (
    <div>
      <div className="Title">
        <h1 style={{ margin: '0' }}>Rockwell</h1>
      </div>
      {JSON.stringify(feedInformation) === '{}'
        ?
        <div style={{ alignContent: 'center', textAlign: 'center' }}> Please wait while your feed is loading.</div>
        :
        <React.Fragment>
          <div className="Feed">
            <div className="TopInstructions">
              <h5 style={{ margin: '0.3em' }}>Feed {parseInt(givenArguments.page) + 1} of 5</h5> 
              <p style={{ margin: '0.1em' }}><i>Please interact with the content below as if you were on Twitter. To complete this page, make sure to scroll through the entire feed.</i></p>
            </div>
            {
              feedInformation.map(tweet => (
                <Tweet key={JSON.stringify(tweet)} tweet={tweet} givenArguments={givenArguments} handleRetweet={handleRetweet} handleLike={handleLike} handleLinkClicked={handleLinkClicked}/>
              ))
            }
            <div className="TopInstructions">
              <h4 style={{ margin: '0' }}>Once you are done, click on the button below</h4>
            </div>
          </div>

          <div className="BottomNavBar">
            <input type="image" alt="right arrow, next page button" disabled={(!minimumFeedTimeCondition || !endOfFeedCondition) ? 'disabled' : ''} src={(!minimumFeedTimeCondition || !endOfFeedCondition) ? rightArrow : rightArrowEnabled} className="rightImg" onClick={nextButtonClicked}/>
          </div>

        </React.Fragment>
      }
      <CarouselModal showCarousel={showInstructionCarousel} hideCarousel={handleCloseInstructionCarousel} />
    </div>
  );
}

export default MainFeed;
