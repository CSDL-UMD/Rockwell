import React, { useState } from 'react';
import { CarouselItem } from 'react-bootstrap';
import Carousel from 'react-bootstrap/Carousel';
import {SliderData} from './SliderData';
import BtnSlider from './BtnSlider';
import './Carousel.css';

//const {current, setCurrent} = useState{0}
//const length = slides.length
function CarouselComponent() {
  
  const [slideIndex, setSlideIndex] = useState(1)
  const nextSlide = () => {
    if(slideIndex !== SliderData.length){
      setSlideIndex(slideIndex + 1)
    }
    else if(slideIndex === SliderData.length){
      setSlideIndex(1)
    }
  }
  const prevSlide = () => {
    if(slideIndex !== 1){
      setSlideIndex(slideIndex - 1)
    }
    else if(slideIndex === 1){
      setSlideIndex(SliderData.length)
    }
  }

  const moveDot = index => {
    setSlideIndex(index)
  }

  return (
    <div className="slider-container">
      {SliderData.map((slide, i) => {
        return (
          <div className = {slideIndex === i + 1 ? "slide active-anim" : "slide"}>
            <img
              src={`/Instruction_Images/Screenshot${i + 1}.png`}
              alt="" />
          </div>
        )
      })}
      <BtnSlider moveSlide={nextSlide} direction = {"next"}/>
      <BtnSlider moveSlide={prevSlide} direction = {"prev"}/>
      {/*I work right*/}

      <div className = "container-dots">
        {Array.from({length: SliderData.length}).map((item, index) => (
          <div onClick = {() => moveDot(index + 1)}
          className={slideIndex === index + 1 ? "dot active" : "dot"}></div>
        ))}
      </div>
    </div>
  )
}

export default CarouselComponent;
/*SliderData[index + 1].image*/

/* src={slide.image} key={i}
alt="" /> */