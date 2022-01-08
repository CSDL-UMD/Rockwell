import React from 'react';
import Modal from 'react-bootstrap/Modal';
import CarouselComponent from './CarouselComponent';
import './CarouselModal.css';

function CarouselModal(props) {
  return (
    <Modal show={props.showCarousel} size='m'>
      <Modal.Body>
        <CarouselComponent hideCarousel={props.hideCarousel} />
      </Modal.Body>
    </Modal>
  )
}

export default CarouselModal;
