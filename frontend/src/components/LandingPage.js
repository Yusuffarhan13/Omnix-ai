import React, { useState, useEffect } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import { 
  Menu, 
  X, 
  ArrowRight, 
  Brain, 
  Globe, 
  Zap, 
  MessageCircle,
  BookOpen,
  Code,
  Search,
  Image,
  Mic,
  Monitor,
  Star,
  ChevronDown
} from 'lucide-react';

const LandingPage = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const { scrollYProgress } = useScroll();
  const y = useTransform(scrollYProgress, [0, 1], ['0%', '50%']);

  useEffect(() => {
    const handleScroll = () => {
      const elements = document.querySelectorAll('.animate-on-scroll');
      elements.forEach(element => {
        const elementTop = element.getBoundingClientRect().top;
        const elementVisible = 150;
        
        if (elementTop < window.innerHeight - elementVisible) {
          element.classList.add('animate-slide-up');
        }
      });
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleGetStarted = () => {
    // Redirect to Omnix AI app
    window.location.href = '/';
  };

  const handleApolaAI = () => {
    window.open('https://apolaai.com', '_blank');
  };

  return (
    <div className="min-h-screen bg-black text-white overflow-x-hidden">
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 bg-black/80 backdrop-blur-md border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center space-x-2"
            >
              <div className="w-8 h-8 bg-gradient-to-r from-primary-500 to-primary-600 rounded-lg flex items-center justify-center">
                <Brain className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold gradient-text">Anéxodos AI</span>
            </motion.div>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-8">
              <a href="#products" className="text-gray-300 hover:text-primary-500 transition-colors">Products</a>
              <a href="#about" className="text-gray-300 hover:text-primary-500 transition-colors">About</a>
              <a href="#contact" className="text-gray-300 hover:text-primary-500 transition-colors">Contact</a>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleGetStarted}
                className="btn-primary"
              >
                Get Started
              </motion.button>
            </div>

            {/* Mobile menu button */}
            <div className="md:hidden">
              <button
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                className="text-gray-300 hover:text-white"
              >
                {isMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
              </button>
            </div>
          </div>

          {/* Mobile Navigation */}
          {isMenuOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="md:hidden bg-black border-t border-white/10"
            >
              <div className="px-2 pt-2 pb-3 space-y-1">
                <a href="#products" className="block px-3 py-2 text-gray-300 hover:text-primary-500">Products</a>
                <a href="#about" className="block px-3 py-2 text-gray-300 hover:text-primary-500">About</a>
                <a href="#contact" className="block px-3 py-2 text-gray-300 hover:text-primary-500">Contact</a>
                <button
                  onClick={handleGetStarted}
                  className="w-full text-left px-3 py-2 btn-primary mt-2"
                >
                  Get Started
                </button>
              </div>
            </motion.div>
          )}
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
        {/* Animated Background */}
        <div className="absolute inset-0">
          <div className="absolute inset-0 bg-gradient-to-r from-black via-gray-900 to-black"></div>
          <motion.div 
            style={{ y }}
            className="absolute inset-0 opacity-20"
          >
            <div className="absolute top-20 left-10 w-72 h-72 bg-primary-500/20 rounded-full blur-3xl animate-pulse-slow"></div>
            <div className="absolute bottom-20 right-10 w-96 h-96 bg-primary-600/10 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '2s' }}></div>
          </motion.div>
        </div>

        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
              Revolutionizing
              <span className="gradient-text"> AI </span>
              in Sri Lanka
            </h1>
            <p className="text-xl md:text-2xl text-gray-300 mb-8 max-w-3xl mx-auto">
              Our goal is to give quality AI to everyone. Building innovative solutions that transform how people learn, work, and interact with artificial intelligence.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleGetStarted}
                className="btn-primary text-lg px-8 py-4 flex items-center gap-2"
              >
                Try Omnix AI <ArrowRight className="w-5 h-5" />
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleApolaAI}
                className="btn-secondary text-lg px-8 py-4"
              >
                Explore Apola AI
              </motion.button>
            </div>
          </motion.div>
        </div>

        {/* Scroll indicator */}
        <motion.div
          animate={{ y: [0, 10, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="absolute bottom-8 left-1/2 transform -translate-x-1/2"
        >
          <ChevronDown className="w-6 h-6 text-primary-500" />
        </motion.div>
      </section>

      {/* Products Section */}
      <section id="products" className="py-20 bg-gradient-to-b from-black to-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold mb-6">
              Our <span className="gradient-text">AI Solutions</span>
            </h2>
            <p className="text-xl text-gray-300 max-w-3xl mx-auto">
              Discover our cutting-edge AI products designed to enhance education and productivity
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-8">
            {/* Apola AI Card */}
            <motion.div
              initial={{ opacity: 0, x: -50 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8 }}
              className="glass-effect p-8 hover:bg-white/10 transition-all duration-300 group"
            >
              <div className="flex items-center mb-6">
                <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center mr-4">
                  <BookOpen className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-3xl font-bold">Apola AI</h3>
              </div>
              
              <p className="text-gray-300 mb-6 text-lg">
                A personalized multimodal AI tutor designed specifically for Sri Lankan students, 
                aligned with the local school curriculum.
              </p>

              <div className="grid grid-cols-2 gap-4 mb-8">
                <div className="flex items-center gap-2">
                  <Mic className="w-4 h-4 text-primary-500" />
                  <span className="text-sm">Speech Support</span>
                </div>
                <div className="flex items-center gap-2">
                  <Image className="w-4 h-4 text-primary-500" />
                  <span className="text-sm">Visual Learning</span>
                </div>
                <div className="flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-primary-500" />
                  <span className="text-sm">Homework Help</span>
                </div>
                <div className="flex items-center gap-2">
                  <Brain className="w-4 h-4 text-primary-500" />
                  <span className="text-sm">Adaptive Learning</span>
                </div>
              </div>

              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleApolaAI}
                className="w-full btn-primary group-hover:glow-effect transition-all duration-300"
              >
                Visit Apola AI <ArrowRight className="w-4 h-4 ml-2" />
              </motion.button>
            </motion.div>

            {/* Omnix AI Card */}
            <motion.div
              initial={{ opacity: 0, x: 50 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8 }}
              className="glass-effect p-8 hover:bg-white/10 transition-all duration-300 group"
            >
              <div className="flex items-center mb-6">
                <div className="w-12 h-12 bg-gradient-to-r from-primary-500 to-primary-600 rounded-lg flex items-center justify-center mr-4">
                  <Zap className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-3xl font-bold">Omnix AI</h3>
              </div>
              
              <p className="text-gray-300 mb-6 text-lg">
                An all-in-one general AI agent with advanced capabilities including browser control, 
                speech-to-speech conversations, and powerful reasoning models.
              </p>

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="flex items-center gap-2">
                  <Monitor className="w-4 h-4 text-primary-500" />
                  <span className="text-sm">Browser Control</span>
                </div>
                <div className="flex items-center gap-2">
                  <MessageCircle className="w-4 h-4 text-primary-500" />
                  <span className="text-sm">Voice Chat</span>
                </div>
                <div className="flex items-center gap-2">
                  <Search className="w-4 h-4 text-primary-500" />
                  <span className="text-sm">Research Tools</span>
                </div>
                <div className="flex items-center gap-2">
                  <Code className="w-4 h-4 text-primary-500" />
                  <span className="text-sm">Code Generation</span>
                </div>
              </div>

              <div className="mb-8">
                <h4 className="text-lg font-semibold mb-4">Two Powerful Models:</h4>
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <Zap className="w-5 h-5 text-yellow-400" />
                    <div>
                      <span className="font-medium text-yellow-400">Omnix Flash</span>
                      <p className="text-sm text-gray-400">Fast everyday tasks and quick responses</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Star className="w-5 h-5 text-purple-400" />
                    <div>
                      <span className="font-medium text-purple-400">Omnix Maxima</span>
                      <p className="text-sm text-gray-400">Advanced deep thinking and multi-perspective reasoning</p>
                    </div>
                  </div>
                </div>
              </div>

              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleGetStarted}
                className="w-full btn-primary group-hover:glow-effect transition-all duration-300"
              >
                Launch Omnix AI <ArrowRight className="w-4 h-4 ml-2" />
              </motion.button>
            </motion.div>
          </div>
        </div>
      </section>

      {/* About Section */}
      <section id="about" className="py-20 bg-black">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center"
          >
            <h2 className="text-4xl md:text-5xl font-bold mb-8">
              About <span className="gradient-text">Anéxodos AI</span>
            </h2>
            <div className="max-w-4xl mx-auto">
              <p className="text-xl text-gray-300 mb-8 leading-relaxed">
                Based in Sri Lanka, Anéxodos AI is on a mission to democratize artificial intelligence. 
                We believe that advanced AI should be accessible to everyone, regardless of their location or background.
              </p>
              <p className="text-lg text-gray-400 mb-12">
                We're revolutionizing AI in Sri Lanka while building global solutions that inspire trust, 
                innovation, and progress. Our products are designed to enhance education, productivity, 
                and human potential through cutting-edge artificial intelligence.
              </p>
              
              <div className="grid md:grid-cols-3 gap-8">
                <div className="glass-effect p-6 text-center">
                  <Globe className="w-12 h-12 text-primary-500 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold mb-2">Global Impact</h3>
                  <p className="text-gray-400">Building AI solutions for a worldwide audience</p>
                </div>
                <div className="glass-effect p-6 text-center">
                  <Brain className="w-12 h-12 text-primary-500 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold mb-2">Innovation First</h3>
                  <p className="text-gray-400">Pushing the boundaries of AI technology</p>
                </div>
                <div className="glass-effect p-6 text-center">
                  <Star className="w-12 h-12 text-primary-500 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold mb-2">Quality Focus</h3>
                  <p className="text-gray-400">Delivering excellence in every product</p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer id="contact" className="bg-gray-900 border-t border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center">
            <div className="flex items-center justify-center space-x-2 mb-6">
              <div className="w-8 h-8 bg-gradient-to-r from-primary-500 to-primary-600 rounded-lg flex items-center justify-center">
                <Brain className="w-5 h-5 text-white" />
              </div>
              <span className="text-2xl font-bold gradient-text">Anéxodos AI</span>
            </div>
            
            <p className="text-gray-400 mb-6">
              Revolutionizing AI in Sri Lanka, building global solutions
            </p>
            
            <div className="mb-8">
              <p className="text-lg text-gray-300 mb-2">Get in touch with us</p>
              <a 
                href="mailto:support@anexodsai.com" 
                className="text-primary-500 hover:text-primary-400 transition-colors text-lg font-medium"
              >
                support@anexodsai.com
              </a>
            </div>
            
            <div className="border-t border-white/10 pt-8">
              <p className="text-gray-500">
                © 2024 Anéxodos AI. All rights reserved.
              </p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;