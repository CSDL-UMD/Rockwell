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
    let feedSize = [];
    let furthestSeen = 0;

    const handleFirstRender = () => {
      let result = handleTotalResize();
      feedSize = (calculateFeedSize(result, window.innerHeight));
      window.scrollTo(0, 0);
    };

    const fetchTweets = (argumentObject) => {
      fetch(configuration.get_feed + '?access_token=' + argumentObject.access_token + '&access_token_secret=' + argumentObject.access_token_secret + '&worker_id=' + argumentObject.worker_id + '&attn=' + argumentObject.attn + '&page=' + argumentObject.page).then(resp => {
        return resp.json();
      }).then(value => {
        console.log(value);
        setFeedInformation(value);
        const sleep = (time) => {
          return new Promise((resolve) => setTimeout(resolve, time));
        }
        sleep(500).then(() => {
          handleFirstRender(); // Add ifs for return size == 0 just in case 500 ms is not enough for firstRender.
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
      console.log(JSON.stringify(returnObject))
      return returnObject;
    }

    const handleTweetViewTracking = (clientHeight) => {
      const time = new Date();
      console.log("HOURS:" + String(time.getHours()) + ' MINUTES: ' + String(time.getMinutes()) + ' SECONDS: ' + + String(time.getSeconds()) + ' DATE: ' + String(time.getFullYear()) + String(time.getMonth()) + String(time.getDate()));
      if (!feedSize.length) {
        return 0;
      }
      if (furthestSeen === 10) {
        return furthestSeen;
      }

      const position = window.pageYOffset + clientHeight * 0.5;

      if (position < feedSize[0] && furthestSeen === 0) {
        return 0;
      } else if (position < feedSize[0]) {
        return furthestSeen;
      }

      let currentThreshold = 0;
      let i = 0;
      for (; i < furthestSeen; ++i) {
        currentThreshold += feedSize[i];
      }

      if (position < currentThreshold) {
        return furthestSeen;
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
        return i;
      } else {
        return i - 1;
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
      furthestSeen = res;
      console.log('Furthest Tweet Seen: ' + res);
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
              <button className='nextBtn' disabled={!minimumFeedTimeCondition || !hasReachedEndOfFeed}><img className='rightImg' src = {rightArrow} alt=''/></button>
            </Link>
          </div>

        </React.Fragment>
      }
      <CarouselModal showCarousel={showInstructionCarousel} hideCarousel={handleCloseInstructionCarousel} />
    </div>
  );
}

export default MainFeed;
