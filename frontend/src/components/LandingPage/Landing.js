import React from 'react';
import config from '../../Configuration/config';
import { useEffect } from 'react';

function Landing(props) {
    useEffect(() => {
        window.location.href = config.authorizer;
    }, [])
    return (
        <div>Welcome to my landing page.</div>
    )

}

export default Landing;