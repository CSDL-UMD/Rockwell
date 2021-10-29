import React from 'react';
import { Switch, Route } from 'react-router-dom';
import MainAttentionPage from '../components/AttentionCheck/MainAttentionPage';
import MainFeed from '../components/MainFeed/MainFeed';
function Main(){
    return (
      <Switch>
        { /*<Route exact path='/' component={Home}></Route> */ }
        <Route exact path='/feed' render={(props) => <MainFeed {...props} />}/*component={MainFeed}*/></Route>
        <Route exact path='/attention' render={(props) => <MainAttentionPage {...props} />}></Route>
      </Switch>
    );
  }
  
  export default Main;