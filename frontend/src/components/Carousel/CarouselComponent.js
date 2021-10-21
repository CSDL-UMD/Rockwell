import React, { useState } from 'react';
import { SliderData } from './SliderData';
import BtnSlider from './BtnSlider';
import './Carousel.css';

function CarouselComponent(props) {

  const [slideIndex, setSlideIndex] = useState(1);

  const nextSlide = () => {
    if (slideIndex !== SliderData.length) {
      setSlideIndex(slideIndex + 1);
    }
    else if (slideIndex === SliderData.length) {
      setSlideIndex(1);
    }
  };

  const prevSlide = () => {
    if (slideIndex !== 1) {
      setSlideIndex(slideIndex - 1);
    }
    else if (slideIndex === 1) {
      setSlideIndex(SliderData.length);
    }
  };

  return (
    <div>
      <div className="slider-container">
            <div className="slide active-anim">
              <img
                src={`/Instruction_Images/Screenshot${slideIndex}.png`}
                alt="" />
            </div>

        {SliderData.length !== slideIndex ? <BtnSlider moveSlide={nextSlide} direction={"next"} /> : null}
        {slideIndex !== 1 ? <BtnSlider moveSlide={prevSlide} direction={"prev"} /> : null}

        <div className="container-dots">
          {Array.from({ length: SliderData.length }).map((item, index) => (
            <div className={slideIndex === index + 1 ? "dot active" : "dot"}></div>
          ))}
        </div>
      </div>
        <div className="CloseButton">
          {SliderData.length === slideIndex ? <button onClick={props.hideCarousel}>Close</button> : null}
        </div>
    </div>
  )
}

export default CarouselComponent;
