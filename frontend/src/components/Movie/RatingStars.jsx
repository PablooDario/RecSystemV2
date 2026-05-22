import React, { useState } from 'react';
import { Star } from 'lucide-react';

const RatingStars = ({ rating, onRate, isReadOnly = false }) => {
  const [hover, setHover] = useState(0);

  const handleClick = (value) => {
    if (!isReadOnly && onRate) {
      onRate(value);
    }
  };

  const handleMouseEnter = (value) => {
    if (!isReadOnly) {
      setHover(value);
    }
  };

  const handleMouseLeave = () => {
    if (!isReadOnly) {
      setHover(0);
    }
  };

  const displayRating = hover || rating || 0;

  return (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <div 
          key={star} 
          className="relative"
          onMouseLeave={handleMouseLeave}
        >
          {/* Full Star */}
          <div
            className={`cursor-pointer transition-all ${
              isReadOnly ? 'cursor-default' : 'hover:scale-110'
            }`}
            onClick={() => handleClick(star)}
            onMouseEnter={() => handleMouseEnter(star)}
          >
            <Star
              className={`w-8 h-8 transition-colors ${
                displayRating >= star
                  ? 'fill-yellow-400 text-yellow-400'
                  : 'fill-gray-700 text-gray-700'
              }`}
            />
          </div>

          {/* Half Star Overlay */}
          {!isReadOnly && (
            <div
              className="absolute top-0 left-0 w-1/2 h-full overflow-hidden cursor-pointer"
              onClick={() => handleClick(star - 0.5)}
              onMouseEnter={() => handleMouseEnter(star - 0.5)}
            >
              <Star
                className={`w-8 h-8 transition-colors ${
                  displayRating >= star - 0.5
                    ? 'fill-yellow-400 text-yellow-400'
                    : 'fill-gray-700 text-gray-700'
                }`}
              />
            </div>
          )}
        </div>
      ))}
      <span className="ml-2 text-white font-semibold text-lg">
        {displayRating > 0 ? displayRating.toFixed(1) : '0.0'}
      </span>
    </div>
  );
};

export default RatingStars;