import Tweet from '../Tweet/Tweet';
import CarouselModal from '../Carousel/CarouselModal';
import { useEffect, useState } from 'react';
import configuration from '../../Configuration/config';
import handleTotalResize from './handleTotalResize';
import './MainFeed.css';

function MainFeed(props) {
  const [showInstructionCarousel, setShowInstructionCarousel] = useState(false);
  const [givenArguments, setGivenArguments] = useState({});
  const [feedInformation, setFeedInformation] = useState({});
  const [tweetSizes, setTweetSizes] = useState([]);

  useEffect(() => {
    const handleFirstRender = () => {
      let result = handleTotalResize();
      console.log(result);
      setTweetSizes(result);
      window.scrollTo(0, 0);
    };

    const fetchTweets = (argumentObject) => {
      fetch(configuration.get_feed + '?access_token=' + argumentObject.access_token + '&access_token_secret=' + argumentObject.access_token_secret + '&attn=' + argumentObject.attn + '&page=' + argumentObject.page).then(resp => {
        return resp.json();
      }).then(value => {
        setFeedInformation(value);
        const sleep = (time) => {
          return new Promise((resolve) => setTimeout(resolve, time));
        }
        sleep(500).then(() => {
          handleFirstRender();
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

    const urlArgs = getUrlArgs();
    setGivenArguments(urlArgs);
    fetchTweets(urlArgs);
    urlArgs.page === '0' ? handleShowInstructionCarousel() : setShowInstructionCarousel(false);
    
    const debounce = (fn, ms) => {
      let timer
      return _ => {
        clearTimeout(timer)
        timer = setTimeout(_ => {
          timer = null
          fn.apply(this, arguments)
        }, ms)
      };
    }
    const debouncedHandleResize = debounce(function handleResize() {
      let res = handleTotalResize();
      console.log(res);
      setTweetSizes(res);
    }, 500);
    
    window.addEventListener('resize', debouncedHandleResize);
    return _ => {
      window.removeEventListener('resize', debouncedHandleResize)
  }
  }, [props.location.search]);

  const handleCloseInstructionCarousel = () => {
    setShowInstructionCarousel(false);
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
        <div className="Feed">
          <div className="TopInstructions">
            <h4 style={{ margin: '0' }}>Feed {parseInt(givenArguments.page) + 1} out of 5, please read it like your regular feed.</h4>
          </div>
          {
            feedInformation.map(tweet => (
              <Tweet key={JSON.stringify(tweet)} tweet={tweet} givenArguments={givenArguments} />
            ))
          }
          {/*<button onClick={handleShowInstructionCarousel}>Show Carousel</button>*/}
        </div>
      }
      <CarouselModal showCarousel={showInstructionCarousel} hideCarousel={handleCloseInstructionCarousel} />
    </div>
  );
}

export default MainFeed;
