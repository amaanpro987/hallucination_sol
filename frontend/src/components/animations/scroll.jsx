import { useEffect, useRef } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);

export function ScrollStackItem({ children, index = 0 }) {
  return (
    <div 
      className="scroll-stack-item min-h-screen flex items-center justify-start p-8 md:p-16 lg:p-24 sticky top-0"
      data-index={index}
      style={{
        backgroundColor: index % 2 === 0 ? '#BA7967' : '#6B5B59'
      }}
    >
      <div className="max-w-4xl w-full text-white">
        {children}
      </div>
    </div>
  );
}

export default function ScrollStack({ children, useWindowScroll = false, className = '' }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const items = containerRef.current.querySelectorAll('.scroll-stack-item');
    
    items.forEach((item, index) => {
      // Skip the last item
      if (index === items.length - 1) return;

      ScrollTrigger.create({
        trigger: item,
        start: 'top top',
        end: 'bottom top',
        pin: true,
        pinSpacing: false,
        scrub: true,
      });

      // Fade out effect as next card comes in
      gsap.to(item, {
        scrollTrigger: {
          trigger: items[index + 1],
          start: 'top bottom',
          end: 'top top',
          scrub: true,
        },
        opacity: 0.7,
        scale: 0.95,
        ease: 'none'
      });
    });

    return () => {
      ScrollTrigger.getAll().forEach(trigger => trigger.kill());
    };
  }, []);

  return (
    <div ref={containerRef} className={`scroll-stack ${className}`}>
      {Array.isArray(children) ? 
        children.map((child, index) => (
          <ScrollStackItem key={index} index={index}>
            {child.props.children}
          </ScrollStackItem>
        ))
        :
        <ScrollStackItem index={0}>
          {children}
        </ScrollStackItem>
      }
    </div>
  );
}
