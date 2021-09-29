import Tweet from './components/Tweet/Tweet';
import CarouselModal from './components/Carousel/CarouselModal';
import { useEffect, useState } from 'react';
import './App.css';
function App() {
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
        </div>
        {
          names.map(name => (
            <Tweet key={name} name={name} content1="This is some text" content2="Alternative text" />
          ))
        }
        <button onClick={handleShowInstructionCarousel}>Show Carousel</button>
      </div>
      <CarouselModal showCarousel={showInstructionCarousel} hideCarousel={handleCloseInstructionCarousel} />
    </div>
  );
}

export default App;
