import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Tweet from '../Tweet/Tweet';

function MainAttentionPage(props) {
  const [givenArguments, setGivenArguments] = useState({});

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
    setGivenArguments(getUrlArgs());
  }, [props]);

  

  return (
    <div>{JSON.stringify(givenArguments)}
      <Link to={'/feed?access_token=' + givenArguments.access_token + '&access_token_secret=' + givenArguments.access_token_secret + '&worker_id=' + givenArguments.worker_id + '&attn=0&page=' + (parseInt(givenArguments.page) + 1)}>Next</Link>
    </div>
  )
}

export default MainAttentionPage;