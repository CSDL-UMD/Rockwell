import './App.css';
import Tweet from './components/Tweet/Tweet';
import CarouselComponent from './components/Carousel/Carousel';
import {useEffect, useState} from 'react';
function App() {
  let names = ["Tommy", "Tony", "Robert"];
  const [tommyTesting, setTommyTesting] = useState(false);
  useEffect(() => {
    setTommyTesting(false);
  },[])

  return (
    <div>
      <div className="Title">
        <h1 style={{ margin: '0' }}>Infodiversity</h1>
      </div>
      <div className="Feed">
        <div className="TopInstructions">
          <h3 style={{ margin: '0'}}>Feed {1} out of 5, please read it like your regular feed.</h3>
        </div>
        { tommyTesting ?
        <CarouselComponent />
        :
          names.map(name => (
            <Tweet name={name} content1="This is some text" content2 = "Alternative text" />
          ))
        }
      </div>
    </div>
  );
}

export default App;
