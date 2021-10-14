import React from 'react';
import Modal from 'react-bootstrap/Modal';
import CarouselComponent from './CarouselComponent';
import './CarouselModal.css';

function CarouselModal(props) {
    return (
        <Modal show={props.showCarousel} size='xl'>
            <Modal.Body>
            <CarouselComponent />
            </Modal.Body>
            <button onClick={props.hideCarousel}>Close</button>
        </Modal>
    )
}

export default CarouselModal;
