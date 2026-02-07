import { useEffect, useRef, useState } from 'react';

export default function ScrambledText({
  children,
  className = '',
  textClassName = '',
  radius = 80,
  duration = 1.2,
  speed = 0.5,
  scrambleChars = '!<>-_\\/[]{}—=+*^?#________'
}) {
  const textRef = useRef(null);
  const [isVisible, setIsVisible] = useState(false);
  const [displayText, setDisplayText] = useState('');
  const originalText = children?.toString() || '';

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !isVisible) {
          setIsVisible(true);
        }
      },
      { threshold: 0.1 }
    );

    if (textRef.current) {
      observer.observe(textRef.current);
    }

    return () => {
      if (textRef.current) {
        observer.unobserve(textRef.current);
      }
    };
  }, [isVisible]);

  useEffect(() => {
    if (!isVisible) return;

    const chars = originalText.split('');
    const scrambleCharsArray = scrambleChars.split('');
    let frame = 0;
    const totalFrames = duration * 60; // 60fps
    
    const animate = () => {
      frame++;
      const progress = frame / totalFrames;

      const newText = chars.map((char, index) => {
        if (char === ' ') return ' ';
        
        const charProgress = Math.max(0, Math.min(1, 
          (progress - (index / chars.length) * (1 - speed)) / speed
        ));

        if (charProgress >= 1) {
          return char;
        }

        const randomChar = scrambleCharsArray[
          Math.floor(Math.random() * scrambleCharsArray.length)
        ];
        
        return Math.random() < charProgress ? char : randomChar;
      }).join('');

      setDisplayText(newText);

      if (frame < totalFrames) {
        requestAnimationFrame(animate);
      } else {
        setDisplayText(originalText);
      }
    };

    animate();
  }, [isVisible, originalText, duration, speed, scrambleChars]);

  return (
    <div ref={textRef} className={className}>
      <span className={textClassName}>
        {isVisible ? displayText : originalText}
      </span>
    </div>
  );
}
