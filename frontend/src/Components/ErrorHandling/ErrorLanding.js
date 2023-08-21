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
      switch (Number(errorCode)) {
        case config.error_codes.no_tweets_main_feed:
          setErrorMessage("Dang! There was an error loading the simulated feed, please go back to the Qualtrics tab and try again. If this error persists, please complete the suvery manually and let us know in the feedback on Connect.Thank you and sorry for the inconvenience.");
          break;
        case (config.error_codes.tweet_fetch_error_main_feed):
          setErrorMessage("Dang! There was an error loading the simulated feed, please go back to the Qualtrics tab and try again. If this error persists, please complete the suvery manually and let us know in the feedback on Connect.Thank you and sorry for the inconvenience.");
          break;
        case config.error_codes.no_tweets_attn_check:
          setErrorMessage("Sorry no attention tweets existed for your account.");
          break;
        case config.error_codes.tweet_fetch_error_attn_check:
          setErrorMessage("We were unable to retrieve your attention check at this time.");
          break
        default:
          setErrorMessage("Dang! There was an error loading the simulated feed, please go back to the Qualtrics tab and try again. If this error persists, please complete the suvery manually and let us know in the feedback on Connect.Thank you and sorry for the inconvenience.");
      }
    };
    errorMessageSelector(getUrlArgs().error);
  }, [props.location.search])
  return (
    <div>
      {errorMessage ? errorMessage : ''}
    </div>
  )
}

export default ErrorLanding;
