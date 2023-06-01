import configuration from '../../Configuration/config';
import config from '../../Configuration/config';
import './FinalPage.css';

function FinalPage() {
    let worker_id_cookie = document.cookie.replace(/(?:(?:^|.*;\s*)_rockwellidentifierv2_\s*\=\s*([^;]*).*$)|^.*$/, "$1");
    fetch(configuration.completed_change + '?worker_id='+ worker_id_cookie, { method: 'POST' });
    return (
        <div className="TextBody">
            Thank you for answering these questions. This research is not intended to support or oppose any political candidate or
            office. The research has no affiliation with any political candidate or campaign and has received no financial support from any political candidate or campaign. Should you have any questions about this study, please contact Brendan Nyhan at
            nyhan@dartmouth.edu.

            We will not access your Twitter account again in the future. You can revoke access to your profile at any time by following
            the instructions <a rel="noopener noreferrer" target="_blank" href="https://help.twitter.com/en/managing-your-account/connect-or-revoke-access-to-third-party-apps">here.</a> Please click the next button below to finish the survey and receive credit for completion from YouGov.
            Thank you again for participating!
            <br />
            <button onClick={() => window.location.href = config.youGovCompleteRedirect}>Next</button>
        </div>
    )
}

export default FinalPage;
