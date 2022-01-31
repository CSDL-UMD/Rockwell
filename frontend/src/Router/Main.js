import React from 'react';
import { Switch, Route } from 'react-router-dom';
import MainAttentionPage from '../Components/AttentionCheck/MainAttentionPage';
import MainFeed from '../Components/MainFeed/MainFeed';
import Landing from '../Components/FeedError/Landing';
import ErrorLanding from '../Components/FeedError/ErrorLanding';
import FinalPage from '../Components/EndLandingPage/FinalPage';

function Main(){
    return (
      <Switch>
        { /*<Route exact path='/' component={Home}></Route> */ }
        <Route exact path='/' render={(props) => <Landing {...props} />}></Route>
        <Route exact path='/feed' render={(props) => <MainFeed {...props} />}></Route>
        <Route exact path='/attention' render={(props) => <MainAttentionPage {...props} />}></Route>
        <Route exact path='/error' render={(props) => <ErrorLanding {...props} />}></Route>
        <Route exact path='/complete' render={(props) => <FinalPage {...props} />}></Route>
      </Switch>
    );
  }
  
  export default Main;
