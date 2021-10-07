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
    console.log(value);
    setFeedInformation(value);
  })
}

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
          <h3 style={{ margin: '0' }}>Feed {parseInt(givenArguments.page) + 1} out of 5, please read it like your regular feed.</h3>
        </div>
        {
          feedInformation.map(tweet => (
            <Tweet key={JSON.stringify(tweet)} tweet={tweet} givenArguments={givenArguments} />
          ))
        }
        <button onClick={handleShowInstructionCarousel}>Show Carousel</button>
      </div>
      }
      <CarouselModal showCarousel={showInstructionCarousel} hideCarousel={handleCloseInstructionCarousel} />
    </div>
  );
}

export default MainFeed;
