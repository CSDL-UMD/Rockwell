import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Tweet from '../Tweet/Tweet';
import CarouselModal from '../Carousel/CarouselModal';
import configuration from '../../Configuration/config';
import handleTotalResize from './handleTotalResize';
import rightArrow from './Icons/arrow-right.png';
import './MainFeed.css';

function MainFeed(props) {
  const [showInstructionCarousel, setShowInstructionCarousel] = useState(false);
  const [givenArguments, setGivenArguments] = useState({});
  const [feedInformation, setFeedInformation] = useState({});
  const [minimumFeedTimeCondition, setMinimumFeedTimeCondition] = useState(false);
  const [hasReachedEndOfFeed, setHasReachedEndOfFeed] = useState(true);

  async function beginTimer() { // This must be called in my handleFirstRender function, change to promise syntax
    await new Promise(r => setTimeout(r, 30000)); // Also need to consider time that the modal is shown
    setMinimumFeedTimeCondition(true)
  }

  useEffect(() => {
    let startTime = Date.now();
    let feedSize = [];
    let furthestSeen = [1, 0];
    const tweetViewTimeStamps = [];

    const handleFirstRender = (argumentObject) => {
      let result = handleTotalResize();
      feedSize = (calculateFeedSize(result, window.innerHeight));
      window.scrollTo(0, 0);
      startTime = Date.now();
      if (argumentObject.page !== 0) {
        beginTimer();
      }
      tweetViewTimeStamps.push([0,0]);
    };

    const fetchTweets = (argumentObject) => {
      fetch(configuration.get_feed + '?access_token=' + argumentObject.access_token + '&access_token_secret=' + argumentObject.access_token_secret + '&worker_id=' + argumentObject.worker_id + '&attn=' + argumentObject.attn + '&page=' + argumentObject.page).then(resp => {
        return resp.json();
      }).then(value => {
        setFeedInformation(value);
        const sleep = (time) => {
          return new Promise((resolve) => setTimeout(resolve, time));
        }
        sleep(500).then(() => {
          handleFirstRender(argumentObject); // Add ifs for return size == 0 just in case 500 ms is not enough for firstRender.
        });
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

    const handleTweetViewTracking = (clientHeight) => { // Return None when its the same and then handle not none outside with a timestamp and tracking state change.
      const time = Date.now();
      // Need to account for first tweet being on the screen at the start (set in array manually perhaps and set this to only report > 1)
      if (!feedSize.length) {
        return null;
      }
      if (furthestSeen[0] === 10) {
        return null;
      }

      const position = window.pageYOffset + clientHeight * 0.5;

      if (position < feedSize[0] && furthestSeen[0] === 0) {
        return null;
      } else if (position < feedSize[0]) {
        return null;
      }

      let currentThreshold = 0;
      let i = 0;
      for (; i <= furthestSeen[0]; ++i) {
        currentThreshold += feedSize[i];
      }

      if (position < currentThreshold) {
        return null;
      }

      let didBreak = false;
      for (; i < feedSize.length; ++i) {
        currentThreshold += feedSize[i];
        if (currentThreshold > position) {
          didBreak = true;
          break;
        }
      }
      if (didBreak) {
        setHasReachedEndOfFeed(true);
        tweetViewTimeStamps.push([i,time-startTime]);
        return [i, time - startTime];
      } else {
        tweetViewTimeStamps.push([i - 1,time-startTime]);
        return [i - 1, time - startTime];
      }
    };

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
      let res = handleTotalResize();
      feedSize = (calculateFeedSize(res, window.innerHeight));
    }, 500);

    const debouncedHandleScroll = debounce(function handleScroll() {
      const res = handleTweetViewTracking(window.innerHeight);
      if (res !== null) {
        // Make a copy of view array and reset state with the new one here.
        furthestSeen = res;
        console.log('Furthest Tweet Seen: ' + res[0], ' Time: ' + res[1]);
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
  }, [props.location.search]);

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

  const handleCloseInstructionCarousel = () => {
    setShowInstructionCarousel(false);
    beginTimer();
    document.getElementById('root').style.filter = 'blur(0px)'
  };

  const handleShowInstructionCarousel = () => {
    setShowInstructionCarousel(true);
    document.getElementById('root').style.filter = 'blur(5px)'
  };

  return (
    <div>
      <div className="Title">
        <h1 style={{ margin: '0' }}>Infodiversity</h1>
      </div>
      {JSON.stringify(feedInformation) === '{}'
        ?
        <div style={{ alignContent: 'center', textAlign: 'center' }}> Please wait while your feed is loading.</div>
        :
        <React.Fragment>
          <div className="Feed">
            <div className="TopInstructions">
              <h5 style={{ margin: '0' }}>Feed {parseInt(givenArguments.page) + 1} out of 5, please read and interact with it like your regular feed.</h5>
            </div>
            {
              feedInformation.map(tweet => (
                <Tweet key={JSON.stringify(tweet)} tweet={tweet} givenArguments={givenArguments} />
              ))
            }
            <div className="TopInstructions">
              <h4 style={{ margin: '0' }}>Once you are done, click on the button below</h4>
            </div>
          </div>

          <div className="BottomNavBar">
            <Link to={'/attention?access_token=' + givenArguments.access_token + '&access_token_secret=' + givenArguments.access_token_secret + '&worker_id=' + givenArguments.worker_id + '&attn=1&page=' + givenArguments.page}>
              <input type="image" alt="right arrow, next page button" disabled={(!minimumFeedTimeCondition || !hasReachedEndOfFeed) ? 'disabled' : ''} src={rightArrow} className="rightImg" />
            </Link>
          </div>

        </React.Fragment>
      }
      <CarouselModal showCarousel={showInstructionCarousel} hideCarousel={handleCloseInstructionCarousel} />
    </div>
  );
}

export default MainFeed;
