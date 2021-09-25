import './App.css';
import Tweet from './components/Tweet';
function App() {
  return (
    <div>
      <div className="Title">
        <h1 style={{margin: '0'}}>Infodiversity</h1>
      </div>
      <div className="TopInstructions">
      <h3 style={{margin: '0'}}>Feed {1} out of 5, please read it like your regular feed.</h3>
      </div>
      <div className="Feed">
        <Tweet />
      </div>
    </div>
  );
}

export default App;
