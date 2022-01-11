import { Link } from 'react-router-dom';

function ErrorLanding(props) {
    return (
        <div>
            Please try to login again or use a different twitter account, there were no valid tweets to display.
            <br />
            <Link to={'/'}><button>Login Again</button></Link>
        </div>
    )
}

export default ErrorLanding;
