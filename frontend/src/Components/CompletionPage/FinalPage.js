import configuration from '../../Configuration/config';
import config from '../../Configuration/config';
import './FinalPage.css';

function FinalPage() {
    let worker_id_cookie = document.cookie.replace(/(?:(?:^|.*;\s*)_rockwellidentifierv2_\s*\=\s*([^;]*).*$)|^.*$/, "$1");
    fetch(configuration.completed_change + '?worker_id='+ worker_id_cookie, { method: 'POST' });
    return (
        <div className="TextBody">
            Thank you for participating! Please close this tab and return to the survey.
        </div>
    )
}

export default FinalPage;
