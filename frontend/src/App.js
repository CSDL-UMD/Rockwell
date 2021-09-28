import './App.css';
import Tweet from './components/Tweet/Tweet';
function App() {
  let names = ["Tommy", "Tony", "Robert"];
  return (
    <div>
      <div className="Title">
        <h1 style={{ margin: '0' }}>Infodiversity</h1>
      </div>
      <div className="Feed">
        <div className="TopInstructions">
          <h3 style={{ margin: '0'}}>Feed {1} out of 5, please read it like your regular feed.</h3>
        </div>
        {
          names.map(name => (
            <Tweet name={name} content1="This is some text" content2 = "Alternative text" />
          ))
        }
      </div>
    </div>
  );
}

export default App;
