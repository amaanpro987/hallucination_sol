import { useEffect, useRef, useState } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { useNavigate } from 'react-router-dom';
import { Github } from 'lucide-react';
import ScrollStack, { ScrollStackItem } from '../components/animations/scroll';
import Plasma from '../components/animations/plasma';
import ScrambledText from '../components/animations/scrolltext';

gsap.registerPlugin(ScrollTrigger);

export default function Landing() {
  const navigate = useNavigate();
  const heroRef = useRef(null);
  const headerRef = useRef(null);
  const subtitleRef = useRef(null);
  const blackBarRef = useRef(null);
  const ctaRef = useRef(null);
  const cursorDotRef = useRef(null);
  const cursorCircleRef = useRef(null);
  const statsRef = useRef(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [statsAnimated, setStatsAnimated] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  // Detect mobile for performance optimization
  useEffect(() => {
    setIsMobile(window.innerWidth < 768);
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Custom cursor effect
  useEffect(() => {
    const moveCursor = (e) => {
      setMousePos({ x: e.clientX, y: e.clientY });
    };

    window.addEventListener('mousemove', moveCursor);
    
    return () => {
      window.removeEventListener('mousemove', moveCursor);
    };
  }, []);

  // Animate cursor with GSAP
  useEffect(() => {
    if (!cursorDotRef.current || !cursorCircleRef.current) return;

    // Dot follows immediately
    gsap.to(cursorDotRef.current, {
      x: mousePos.x,
      y: mousePos.y,
      duration: 0,
      ease: 'none'
    });

    // Circle follows with delay (slower)
    gsap.to(cursorCircleRef.current, {
      x: mousePos.x,
      y: mousePos.y,
      duration: 0.3,
      ease: 'power2.out'
    });
  }, [mousePos]);

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Initial state - everything hidden
      gsap.set(headerRef.current, { 
        opacity: 0, 
        y: -30 
      });
      gsap.set([subtitleRef.current, ctaRef.current], { 
        opacity: 0, 
        y: 50 
      });
      gsap.set(blackBarRef.current, { 
        scaleX: 0,
        transformOrigin: 'left center'
      });

      // Create timeline
      const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });

      // Header appears first
      tl.to(headerRef.current, {
        opacity: 1,
        y: 0,
        duration: 0.8
      })
      // Animate black bar sliding in
      .to(blackBarRef.current, {
        scaleX: 1,
        duration: 1.2,
        ease: 'power4.inOut'
      }, '-=0.4')
      // Subtitle appears
      .to(subtitleRef.current, {
        opacity: 1,
        y: 0,
        duration: 0.8
      }, '-=0.6')
      // CTA button appears
      .to(ctaRef.current, {
        opacity: 1,
        y: 0,
        duration: 0.6
      }, '-=0.4');

      // Removed scroll-driven hero scrub per request

    }, heroRef);

    return () => ctx.revert();
  }, []);

  // Animated counter for stats
  useEffect(() => {
    if (!statsRef.current || statsAnimated) return;

    const statCards = statsRef.current.querySelectorAll('[data-stat-card]');
    
    ScrollTrigger.create({
      trigger: statsRef.current,
      start: 'top 80%',
      once: true,
      onEnter: () => {
        setStatsAnimated(true);
        
        statCards.forEach((card) => {
          const numberElement = card.querySelector('[data-stat-number]');
          const target = parseFloat(numberElement.getAttribute('data-target'));
          const suffix = numberElement.getAttribute('data-suffix') || '';
          
          // Create a counter object to animate
          const counter = { value: 0 };
          
          gsap.to(counter, {
            value: target,
            duration: 2.5,
            ease: 'power2.out',
            onUpdate: function() {
              const currentValue = Math.round(counter.value);
              numberElement.textContent = currentValue + suffix;
            }
          });
        });

        // Fade in cards with stagger
        gsap.fromTo(statCards, 
          {
            opacity: 0,
            y: 50
          },
          {
            opacity: 1,
            y: 0,
            duration: 0.8,
            stagger: 0.2,
            ease: 'power3.out'
          }
        );
      }
    });

    return () => {
      ScrollTrigger.getAll().forEach(trigger => trigger.kill());
    };
  }, [statsAnimated]);

  return (
    <div ref={heroRef} className="min-h-screen w-full overflow-hidden bg-black relative m-0 p-0 cursor-none">
      {/* Plasma Background Animation - Behind everything */}
      <div 
        className="fixed inset-0 w-screen h-screen z-0"
      >
        {!isMobile ? (
          <Plasma 
            color="#BA7967"
            speed={1.5}
            direction="forward"
            scale={1.0}
            opacity={1}
            mouseInteractive={false}
          />
        ) : (
          <div className="w-full h-full bg-gradient-radial from-[#BA7967]/20 via-[#6B5B59]/10 to-transparent" />
        )}
      </div>

      {/* Custom Cursor */}
      <div 
        ref={cursorDotRef}
        className="fixed w-2 h-2 bg-white rounded-full pointer-events-none z-[9999]"
        style={{ 
          left: 0, 
          top: 0,
          transform: 'translate(-50%, -50%)'
        }}
      />
      <div 
        ref={cursorCircleRef}
        className="fixed w-8 h-8 border-2 border-white/40 rounded-full pointer-events-none z-[9998]"
        style={{ 
          left: 0, 
          top: 0,
          transform: 'translate(-50%, -50%)'
        }}
      />

      {/* Header - Separate Elements */}
      <header 
        ref={headerRef}
        className="fixed top-3 left-0 right-0 z-50 m-0 px-6 py-4"
      >
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          {/* Logo/Brand - No Background */}
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-[#BA7967] to-[#6B5B59] rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">AL</span>
            </div>
            <span className="text-white font-bold text-xl">ALVance</span>
          </div>

          {/* Navigation Links - Glass Rounded Rectangle */}
          <div className="hidden md:flex items-center gap-3 bg-white/10 backdrop-blur-xl border border-white/20 rounded-full px-6 py-2 shadow-lg">
            <button 
              onClick={() => navigate('/')}
              className="text-white hover:text-black hover:bg-[#BA7967] transition-all px-4 py-2 rounded-full font-medium cursor-none"
            >
              • Home
            </button>
            <button 
              onClick={() => navigate('/dashboard')}
              className="text-white hover:text-black hover:bg-[#BA7967] transition-all px-4 py-2 rounded-full font-medium cursor-none"
            >
              Dashboard
            </button>
            <button 
              onClick={() => navigate('/projects')}
              className="text-white hover:text-black hover:bg-[#BA7967] transition-all px-4 py-2 rounded-full font-medium cursor-none"
            >
              Projects
            </button>
            <button 
              onClick={() => navigate('/docs')}
              className="text-white hover:text-black hover:bg-[#BA7967] transition-all px-4 py-2 rounded-full font-medium cursor-none"
            >
              Docs
            </button>
          </div>

          {/* GitHub Button - Solid Rounded Box */}
          <a
            href="https://github.com/ayanfarooque/SIH69"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 bg-[#BA7967] hover:bg-[#6B5B59] text-white px-4 py-2 rounded-full transition-all duration-300 transform hover:scale-105 shadow-lg cursor-none"
          >
            <Github size={18} />
            <span className="font-semibold">Visit Our GitHub</span>
            <div className="flex items-center gap-1 bg-white/20 px-2 py-0.5 rounded-md">
              <span className="text-yellow-300">★</span>
              <span className="text-xs">Star</span>
            </div>
          </a>
        </div>
      </header>

      {/* Accent bar */}
      <div 
        ref={blackBarRef}
        className="absolute top-0 left-0 w-full h-2 bg-[#BA7967] z-40"
      />

      {/* Hero Section - Pushed Down */}
      <div className="relative min-h-screen flex flex-col items-center justify-center px-2 md:px-16 lg:px-12 pt-6 mt-7 z-10">
        {/* Animated circle decorations with mud colors */}
        <div className="absolute top-1/4 right-10 w-32 h-32 bg-[#BA7967] rounded-full opacity-20 blur-2xl z-0" />
        <div className="absolute bottom-1/4 left-10 w-48 h-48 bg-[#6B5B59] rounded-full opacity-15 blur-3xl z-0" />

        {/* Content */}
        <div className="relative z-20 max-w-6xl text-center">
          {/* Line 1: Brand heading */}
          <div className="mb-0">
            <h1 className="m-0 mx-0 text-center drop-shadow-2xl font-bold tracking-tight text-white text-[clamp(3rem,10vw,5rem)] md:text-[clamp(2.5rem,7vw,4.5rem)] lg:text-[clamp(8rem,7vw,5rem)]">
              ALvance
            </h1>
          </div>

          {/* Lines 2 & 3 inside subtitleRef for the entrance animation */}
          <div ref={subtitleRef} className="mb-0 max-w-5xl mx-auto">
            {/* Line 2: Gradient tagline matching theme */}
            <ScrambledText
              className="m-0 mx-auto text-center"
              textClassName="font-semibold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-[#BA7967] via-[#D4956F] to-[#6B5B59] text-[clamp(1.0rem,4.5vw,2rem)] md:text-[clamp(1.3rem,4.5vw,2.4rem)] lg:text-[clamp(1.5rem,3.5vw,1.9rem)]"
              radius={110}
              duration={1.2}
              speed={0.55}
              scrambleChars=".:"
            >
              India's First AI-powered LCA platform for metals
            </ScrambledText>

            {/* Line 3: Supporting description */}
            <ScrambledText
              className="m-0 mt-3 mx-auto text-center"
              textClassName="text-white/90 leading-relaxed text-[clamp(0.95rem,2.1vw,1.15rem)] md:text-[clamp(1rem,2.1vw,1.25rem)]"
              radius={100}
              duration={1.05}
              speed={0.5}
              scrambleChars=".:"
            >
              Analyze environmental impact across the global aluminum supply chain with AI-powered insights,
              real-time data from major production hubs, and comprehensive sustainability reporting.
            </ScrambledText>
          </div>

          <button
            ref={ctaRef}
            onClick={() => navigate('/dashboard')}
            className="bg-[#BA7967] hover:bg-[#6B5B59] text-white px-12 py-4 rounded-lg text-lg font-semibold transition-all duration-300 transform hover:scale-105 shadow-xl hover:shadow-2xl cursor-none"
          >
            Get Started
          </button>
        </div>
      </div>

      {/* Stats Section */}
      <div className="relative w-full py-24 px-8 md:px-16 lg:px-24 z-10">
        <div 
          ref={statsRef}
          className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-6"
        >
          {/* Left Column - Two stacked cards */}
          <div className="flex flex-col gap-6">
            {/* Stat Card 1 */}
            <div 
              data-stat-card
              className="bg-black/40 backdrop-blur-xl p-8 rounded-2xl border-2 border-white/20 hover:border-[#BA7967] transition-all duration-300 hover:bg-black/50 flex-1 shadow-2xl"
            >
              <div 
                data-stat-number
                data-target="100"
                data-suffix="%"
                className="text-6xl font-bold text-transparent bg-clip-text bg-gradient-to-br from-[#BA7967] to-[#6B5B59] mb-3"
              >
                0%
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">
                Free & Open Source
              </h3>
              <p className="text-[#BA7967] text-sm">
                Loved by sustainability teams worldwide
              </p>
            </div>

            {/* Stat Card 2 */}
            <div 
              data-stat-card
              className="bg-black/40 backdrop-blur-xl p-8 rounded-2xl border-2 border-white/20 hover:border-[#BA7967] transition-all duration-300 hover:bg-black/50 flex-1 shadow-2xl"
            >
              <div 
                data-stat-number
                data-target="7"
                className="text-6xl font-bold text-transparent bg-clip-text bg-gradient-to-br from-[#BA7967] to-[#6B5B59] mb-3"
              >
                0
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">
                Lifecycle Stages
              </h3>
              <p className="text-[#BA7967] text-sm">
                Complete metal value chain coverage
              </p>
            </div>
          </div>

          {/* Right Column - One tall card */}
          <div 
            data-stat-card
            className="bg-black/40 backdrop-blur-xl p-12 rounded-2xl border-2 border-white/20 hover:border-[#BA7967] transition-all duration-300 hover:bg-black/50 flex flex-col justify-center items-center text-center shadow-2xl"
          >
            <div 
              data-stat-number
              data-target="500"
              data-suffix="+"
              className="text-8xl font-bold text-transparent bg-clip-text bg-gradient-to-br from-[#BA7967] to-[#6B5B59] mb-4"
            >
              0+
            </div>
            <h3 className="text-2xl font-semibold text-white mb-3">
              Data Points Analyzed
            </h3>
            <p className="text-[#BA7967] text-base max-w-sm">
              Comprehensive analytics & insights across the entire metal lifecycle with real-time tracking
            </p>
          </div>
        </div>
      </div>

      {/* Scroll stack section: 5 solid cards, alternating colors */}
      <ScrollStack useWindowScroll={true} className="w-full mt-16">
        <ScrollStackItem>
          <h2 className="text-3xl font-bold mb-2">Dashboard</h2>
          <p className="text-base leading-relaxed max-w-2xl">
            Get a unified overview of your organization's lifecycle KPIs, system status, and
            recent activity. Jump straight into projects and reports with smart shortcuts.
          </p>
        </ScrollStackItem>
        <ScrollStackItem>
          <h2 className="text-3xl font-bold mb-2">Advanced Analytics</h2>
          <p className="text-base leading-relaxed max-w-2xl">
            Drill into emissions, energy, and material flows across stages. Compare scenarios,
            benchmark against standards, and visualize insights with interactive charts.
          </p>
        </ScrollStackItem>
        <ScrollStackItem>
          <h2 className="text-3xl font-bold mb-2">Canvas</h2>
          <p className="text-base leading-relaxed max-w-2xl">
            Model processes with a drag-and-drop canvas. Connect nodes, set parameters, and let
            the engine compute balances and impacts with instant feedback.
          </p>
        </ScrollStackItem>
        <ScrollStackItem>
          <h2 className="text-3xl font-bold mb-2">Wizard</h2>
          <p className="text-base leading-relaxed max-w-2xl">
            Create robust projects quickly using guided steps and templates. Validate inputs,
            reuse components, and save progress as you go.
          </p>
        </ScrollStackItem>
        <ScrollStackItem>
          <h2 className="text-3xl font-bold mb-2">Reports</h2>
          <p className="text-base leading-relaxed max-w-2xl">
            Export professional reports and data tables in one click. Share PDFs/CSVs, compare
            runs, and keep stakeholders aligned with traceable results.
          </p>
        </ScrollStackItem>
      </ScrollStack>

      {/* Glassy Footer */}
      <footer className="relative w-full py-16 px-8 md:px-16 lg:px-24 z-10">
        <div className="max-w-7xl mx-auto bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-12 shadow-2xl">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-8">
            {/* Brand Section */}
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <div className="w-10 h-10 bg-gradient-to-br from-[#BA7967] to-[#6B5B59] rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold">AL</span>
                </div>
                <span className="text-white font-bold text-2xl">ALVance</span>
              </div>
              <p className="text-white/70 text-sm leading-relaxed">
                India's first AI-powered LCA platform for comprehensive metal lifecycle analytics.
              </p>
            </div>

            {/* Product Links */}
            <div className="space-y-4">
              <h3 className="text-white font-semibold text-lg">Product</h3>
              <ul className="space-y-2">
                <li>
                  <button onClick={() => navigate('/dashboard')} className="text-white/70 hover:text-[#BA7967] transition-colors text-sm cursor-none">
                    Dashboard
                  </button>
                </li>
                <li>
                  <button onClick={() => navigate('/analytics')} className="text-white/70 hover:text-[#BA7967] transition-colors text-sm cursor-none">
                    Analytics
                  </button>
                </li>
                <li>
                  <button onClick={() => navigate('/projects')} className="text-white/70 hover:text-[#BA7967] transition-colors text-sm cursor-none">
                    Projects
                  </button>
                </li>
                <li>
                  <button onClick={() => navigate('/reports')} className="text-white/70 hover:text-[#BA7967] transition-colors text-sm cursor-none">
                    Reports
                  </button>
                </li>
                <li>
                  <button onClick={() => navigate('/docs')} className="text-white/70 hover:text-[#BA7967] transition-colors text-sm cursor-none">
                    Docs
                  </button>
                </li>
              </ul>
            </div>

            {/* Resources */}
            <div className="space-y-4">
              <h3 className="text-white font-semibold text-lg">Resources</h3>
              <ul className="space-y-2">
                <li>
                  <a href="#" className="text-white/70 hover:text-[#BA7967] transition-colors text-sm cursor-none">
                    Documentation
                  </a>
                </li>
                <li>
                  <a href="#" className="text-white/70 hover:text-[#BA7967] transition-colors text-sm cursor-none">
                    API Reference
                  </a>
                </li>
                <li>
                  <a href="#" className="text-white/70 hover:text-[#BA7967] transition-colors text-sm cursor-none">
                    Guides
                  </a>
                </li>
                <li>
                  <a href="#" className="text-white/70 hover:text-[#BA7967] transition-colors text-sm cursor-none">
                    Support
                  </a>
                </li>
              </ul>
            </div>

            {/* Connect */}
            <div className="space-y-4">
              <h3 className="text-white font-semibold text-lg">Connect</h3>
              <ul className="space-y-2">
                <li>
                  <a href="https://github.com/ayanfarooque/SIH69" target="_blank" rel="noopener noreferrer" className="text-white/70 hover:text-[#BA7967] transition-colors text-sm cursor-none">
                    GitHub
                  </a>
                </li>
                <li>
                  <a href="#" className="text-white/70 hover:text-[#BA7967] transition-colors text-sm cursor-none">
                    Twitter
                  </a>
                </li>
                <li>
                  <a href="#" className="text-white/70 hover:text-[#BA7967] transition-colors text-sm cursor-none">
                    LinkedIn
                  </a>
                </li>
                <li>
                  <a href="#" className="text-white/70 hover:text-[#BA7967] transition-colors text-sm cursor-none">
                    Contact
                  </a>
                </li>
              </ul>
            </div>
          </div>

          {/* Bottom Bar */}
          <div className="border-t border-white/10 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-white/50 text-sm">
              © 2025 ALVance. All rights reserved.
            </p>
            <div className="flex items-center gap-6">
              <a href="#" className="text-white/50 hover:text-[#BA7967] transition-colors text-sm cursor-none">
                Privacy Policy
              </a>
              <a href="#" className="text-white/50 hover:text-[#BA7967] transition-colors text-sm cursor-none">
                Terms of Service
              </a>
              <a href="#" className="text-white/50 hover:text-[#BA7967] transition-colors text-sm cursor-none">
                Cookies
              </a>
            </div>
          </div>
        </div>

        {/* Accent bar */}
        <div className="w-full h-1 bg-gradient-to-r from-[#BA7967] via-[#D4956F] to-[#6B5B59] mt-8 rounded-full" />
      </footer>
    </div>
  );
}
