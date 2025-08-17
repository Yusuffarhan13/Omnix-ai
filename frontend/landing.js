// Landing Page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    initializeNavigation();
    initializeScrollEffects();
    initializeAnimations();
    initializeIntersectionObserver();
});

// Navigation functionality
function initializeNavigation() {
    const navToggle = document.getElementById('nav-toggle');
    const navMenu = document.getElementById('nav-menu');
    const navbar = document.getElementById('navbar');

    // Mobile menu toggle
    navToggle.addEventListener('click', function() {
        navMenu.classList.toggle('active');
        navToggle.classList.toggle('active');
    });

    // Close mobile menu when clicking on a link
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            navMenu.classList.remove('active');
            navToggle.classList.remove('active');
        });
    });

    // Close mobile menu when clicking outside
    document.addEventListener('click', function(event) {
        const isClickInsideNav = navMenu.contains(event.target) || navToggle.contains(event.target);
        if (!isClickInsideNav && navMenu.classList.contains('active')) {
            navMenu.classList.remove('active');
            navToggle.classList.remove('active');
        }
    });

    // Navbar scroll effect
    window.addEventListener('scroll', function() {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });
}

// Scroll effects and animations
function initializeScrollEffects() {
    // Smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                const offsetTop = targetElement.offsetTop - 70; // Account for fixed navbar
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Parallax effect for hero background elements
    window.addEventListener('scroll', function() {
        const scrolled = window.pageYOffset;
        const parallaxElements = document.querySelectorAll('.floating-orb');
        
        parallaxElements.forEach((element, index) => {
            const speed = 0.5 + (index * 0.1);
            const yPos = -(scrolled * speed);
            element.style.transform = `translate3d(0, ${yPos}px, 0)`;
        });
    });
}

// Initialize animations
function initializeAnimations() {
    // Add entrance animations to elements
    const animatedElements = document.querySelectorAll('[data-aos]');
    animatedElements.forEach(element => {
        element.style.visibility = 'hidden';
    });

    // Typing effect for hero title (optional enhancement)
    const heroTitle = document.querySelector('.hero-title');
    if (heroTitle) {
        // Add subtle glow effect on hover for interactive elements
        const interactiveElements = document.querySelectorAll('.btn, .product-card, .pillar');
        interactiveElements.forEach(element => {
            element.addEventListener('mouseenter', function() {
                this.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
            });
        });
    }
}

// Intersection Observer for scroll animations
function initializeIntersectionObserver() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.visibility = 'visible';
                entry.target.classList.add('aos-animate');
                
                // Add staggered animation delays for multiple elements
                const siblings = entry.target.parentElement.children;
                if (siblings.length > 1) {
                    Array.from(siblings).forEach((sibling, index) => {
                        if (sibling.hasAttribute('data-aos')) {
                            setTimeout(() => {
                                sibling.style.visibility = 'visible';
                                sibling.classList.add('aos-animate');
                            }, index * 100);
                        }
                    });
                }
            }
        });
    }, observerOptions);

    // Observe all elements with data-aos attributes
    const animatedElements = document.querySelectorAll('[data-aos]');
    animatedElements.forEach(element => {
        observer.observe(element);
    });
}

// Button click handlers
function handleGetStarted() {
    // Redirect to Omnix AI app
    window.location.href = '/';
}

function handleApolaAI() {
    // Open Apola AI in new tab
    window.open('https://apolaai.com', '_blank');
}

// Enhanced user interactions
function initializeEnhancedInteractions() {
    // Add particle effect on button hover (optional)
    const primaryButtons = document.querySelectorAll('.btn-primary');
    primaryButtons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            createParticleEffect(this);
        });
    });

    // Add magnetic effect to cards
    const cards = document.querySelectorAll('.product-card, .pillar');
    cards.forEach(card => {
        card.addEventListener('mousemove', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const deltaX = (x - centerX) / centerX;
            const deltaY = (y - centerY) / centerY;
            
            const rotateX = deltaY * 5;
            const rotateY = deltaX * 5;
            
            this.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(10px)`;
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateZ(0px)';
        });
    });
}

// Particle effect function (optional enhancement)
function createParticleEffect(element) {
    // Simple particle effect implementation
    const rect = element.getBoundingClientRect();
    const particle = document.createElement('div');
    
    particle.style.position = 'fixed';
    particle.style.width = '4px';
    particle.style.height = '4px';
    particle.style.background = '#d1462a';
    particle.style.borderRadius = '50%';
    particle.style.pointerEvents = 'none';
    particle.style.left = rect.left + Math.random() * rect.width + 'px';
    particle.style.top = rect.top + Math.random() * rect.height + 'px';
    particle.style.opacity = '1';
    particle.style.transition = 'all 1s ease-out';
    particle.style.zIndex = '9999';
    
    document.body.appendChild(particle);
    
    // Animate particle
    setTimeout(() => {
        particle.style.transform = 'translateY(-50px)';
        particle.style.opacity = '0';
    }, 10);
    
    // Remove particle
    setTimeout(() => {
        if (particle.parentNode) {
            particle.parentNode.removeChild(particle);
        }
    }, 1000);
}

// Performance optimization: Debounce scroll events
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Initialize enhanced interactions after DOM load
document.addEventListener('DOMContentLoaded', function() {
    initializeEnhancedInteractions();
});

// Add loading animation
window.addEventListener('load', function() {
    document.body.classList.add('loaded');
    
    // Optional: Add a loading screen fade out effect
    const loadingScreen = document.querySelector('.loading-screen');
    if (loadingScreen) {
        setTimeout(() => {
            loadingScreen.style.opacity = '0';
            setTimeout(() => {
                loadingScreen.style.display = 'none';
            }, 500);
        }, 100);
    }
});

// Handle resize events
window.addEventListener('resize', debounce(function() {
    // Recalculate any position-dependent animations
    const navMenu = document.getElementById('nav-menu');
    if (window.innerWidth > 768 && navMenu.classList.contains('active')) {
        navMenu.classList.remove('active');
        document.getElementById('nav-toggle').classList.remove('active');
    }
}, 100));

// Easter egg: Konami code
let konamiCode = [];
const konamiSequence = [38, 38, 40, 40, 37, 39, 37, 39, 66, 65]; // Up Up Down Down Left Right Left Right B A

document.addEventListener('keydown', function(e) {
    konamiCode.push(e.keyCode);
    if (konamiCode.length > konamiSequence.length) {
        konamiCode.shift();
    }
    
    if (konamiCode.join(',') === konamiSequence.join(',')) {
        // Easter egg activated
        document.body.style.filter = 'hue-rotate(180deg)';
        setTimeout(() => {
            document.body.style.filter = 'none';
        }, 3000);
        konamiCode = [];
    }
});

// Initialize all components when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Anéxodos AI Landing Page Loaded Successfully');
    
    // Add any additional initialization here
    const logo = document.querySelector('.brand-icon');
    if (logo) {
        logo.addEventListener('click', function() {
            // Add a subtle animation when logo is clicked
            this.style.transform = 'scale(1.1) rotate(360deg)';
            setTimeout(() => {
                this.style.transform = 'scale(1) rotate(0deg)';
            }, 300);
        });
    }
});