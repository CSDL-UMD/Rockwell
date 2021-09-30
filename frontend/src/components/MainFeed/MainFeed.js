import Tweet from '../Tweet/Tweet';
import CarouselModal from '../Carousel/CarouselModal';
import { useEffect, useState } from 'react';
import './MainFeed.css';
function MainFeed(props) {
  let names = ["Tommy", "Tony", "Robert"];
  const [showInstructionCarousel, setShowInstructionCarousel] = useState(false);
  useEffect(() => {
    setShowInstructionCarousel(false);
  }, []);

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
      <div className="Feed">
        <div className="TopInstructions">
          <h3 style={{ margin: '0' }}>Feed {1} out of 5, please read it like your regular feed.</h3>
          {JSON.stringify(props.location.search)}
        </div>
        {
          names.map(name => (
            <Tweet key={name} name={name} content="This is some text"/>
          ))
        }
        <button onClick={handleShowInstructionCarousel}>Show Carousel</button>
      </div>
      <CarouselModal showCarousel={showInstructionCarousel} hideCarousel={handleCloseInstructionCarousel} />
    </div>
  );
}

export default MainFeed;
