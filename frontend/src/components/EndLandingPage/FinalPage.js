import { Link } from 'react-router-dom';

function FinalPage(props) {
    return (
        <div>
            Thank you for participating in the ...
            <br />
            <Link to={'/'}><button>Return to Yougov</button></Link>
            <div>Note: The button currently doesnt work until we have a link back to YouGov</div>
        </div>
    )
}

export default FinalPage;
