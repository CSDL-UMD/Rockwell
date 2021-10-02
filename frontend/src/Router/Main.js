import React from 'react';
import { Switch, Route } from 'react-router-dom';
import MainFeed from '../components/MainFeed/MainFeed';
function Main(){
    return (
      <Switch>
        { /*<Route exact path='/' component={Home}></Route> */ }
        <Route exact path='/feed' render={(props) => <MainFeed {...props} />}/*component={MainFeed}*/></Route>
      </Switch>
    );
  }
  
  export default Main;