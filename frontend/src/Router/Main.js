import React from 'react';
import { Switch, Route } from 'react-router-dom';
import MainAttentionPage from '../components/AttentionCheck/MainAttentionPage';
import MainFeed from '../components/MainFeed/MainFeed';
import Landing from '../components/LandingPage/Landing';
import ErrorLanding from '../components/FeedError/ErrorLanding';

function Main(){
    return (
      <Switch>
        { /*<Route exact path='/' component={Home}></Route> */ }
        <Route exact path='/' render={(props) => <Landing {...props} />}></Route>
        <Route exact path='/feed' render={(props) => <MainFeed {...props} />}></Route>
        <Route exact path='/attention' render={(props) => <MainAttentionPage {...props} />}></Route>
        <Route exact path='/error' render={(props) => <ErrorLanding {...props} />}></Route>
      </Switch>
    );
  }
  
  export default Main;
