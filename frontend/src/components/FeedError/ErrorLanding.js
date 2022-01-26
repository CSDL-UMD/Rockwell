import { Link } from 'react-router-dom';
import { useEffect, useState } from 'react';
import config from '../../Configuration/config';

function ErrorLanding(props) {
  const [errorMessage, setErrorMessage] = useState(null);
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
    const errorMessageSelector = (errorCode) => {
      switch (errorCode) { // Error codes can be made into names using an error config for clarity (Translates back to a simple number)
        case config.error_codes.no_tweets_main_feed:
          setErrorMessage("Sorry we were unable to find tweets for this account."); // Likely need a zero tweet and an error case, this would be error in actuality
          break;
        case config.error_codes.tweet_fetch_error_main_feed:
          setErrorMessage("Unfortunately there was an error trying to fetch tweets at this time.");
          break;
        case 2:
          setErrorMessage("Sorry no attention tweets existed for your account.");
          break;
        case 3:
          setErrorMessage("We were unable to retrieve your attention check at this time.");
          break
        default:
          setErrorMessage("Something went wrong...");
      }

    };

    setErrorMessage(errorMessageSelector(getUrlArgs().error));
  }, [props.location.search])
  return (
    <div>
      {errorMessage ? errorMessage : null

      }
      <br />
      <Link to={'/'}><button>Login Again</button></Link>
    </div>
  )
}

export default ErrorLanding;
