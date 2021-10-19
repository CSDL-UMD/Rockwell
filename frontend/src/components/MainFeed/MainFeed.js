import Tweet from '../Tweet/Tweet';
import CarouselModal from '../Carousel/CarouselModal';
import { useEffect, useState } from 'react';
import configuration from '../../Configuration/config';
import './MainFeed.css';
function MainFeed(props) {
  const [showInstructionCarousel, setShowInstructionCarousel] = useState(false);
  const [givenArguments, setGivenArguments] = useState({});
  const [feedInformation, setFeedInformation] = useState({});

  useEffect(() => {
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
    setShowInstructionCarousel(false);
  }, [props.location.search]);

  const handleCloseInstructionCarousel = () => {
    setShowInstructionCarousel(false);
    document.getElementById('root').style.filter = 'blur(0px)'
  };
  const handleShowInstructionCarousel = () => {
    setShowInstructionCarousel(true);
    document.getElementById('root').style.filter = 'blur(5px)'
  };

const fetchTweets = (argumentObject) => {
  fetch(configuration.get_feed + '?access_token=' + argumentObject.access_token + '&access_token_secret=' + argumentObject.access_token_secret + '&attn=' + argumentObject.attn + '&page=' + argumentObject.page).then(resp => {
    return resp.json();
  }).then(value => {
    setFeedInformation(value);
  })
}

const handleTotalResize = (arg) => {
  let res = document.getElementsByClassName('TweetImage');
  Object.keys(res).forEach(image => {
    res[image].height = res[image].width * getImageHeightRatio(res[image].width);
  });
};

const getImageHeightRatio = (width) => {
  if (width > 800)
    return 0.65;
  if (width > 500)
    return 0.60;
  else
    return 0.60;
}

window.addEventListener('resize', handleTotalResize);

  return (
    <div>
      <div className="Title">
        <h1 style={{ margin: '0' }}>Infodiversity</h1>
      </div>
      { JSON.stringify(feedInformation) === '{}'
      ?
    <div style={{alignContent: 'center', textAlign: 'center'}}> Please wait while your feed is loading.</div>
      :
      <div className="Feed">
        <div className="TopInstructions">
          <h4 style={{ margin: '0' }}>Feed {parseInt(givenArguments.page) + 1} out of 5, please read it like your regular feed.</h4>
        </div>
        {
          feedInformation.map(tweet => (
            <Tweet key={JSON.stringify(tweet)} tweet={tweet} givenArguments={givenArguments} getImageHeightRatio={getImageHeightRatio} />
          ))
        }
        {window.scrollTo(0, 0) /* Fix user starting somewhere random in feed due to resize */}
        <button onClick={handleShowInstructionCarousel}>Show Carousel</button>
      </div>
      }
      <CarouselModal showCarousel={showInstructionCarousel} hideCarousel={handleCloseInstructionCarousel} />
    </div>
  );
}

export default MainFeed;
