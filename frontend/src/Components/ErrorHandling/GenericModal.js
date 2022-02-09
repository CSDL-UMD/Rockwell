import React from 'react';
import Modal from 'react-bootstrap/Modal';

function GenericModal(props) {
    return (
        <Modal show={props.showModal} size='s'>
            <Modal.Body>
                <div>
                    {props.message}
                    <br />
                    <button onClick={props.actionHandler}>{props.buttonText}</button>
                </div>
            </Modal.Body>
        </Modal>
    )
}

export default GenericModal;