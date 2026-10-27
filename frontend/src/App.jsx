import React, { useState, useRef, useEffect } from 'react';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import LandingPage from './components/LandingPage';
import UploadPage from './components/UploadPage';
import ResultsPage from './components/ResultsPage';
import SystemTransparency from './components/SystemTransparency';
import RegistryPage from './components/RegistryPage';

export default function App() {
  const [currentView, setCurrentView] = useState('landing'); // 'landing' | 'upload' | 'results' | 'transparency' | 'registry'
  const [scanData, setScanData] = useState(null);
  const [scanFile, setScanFile] = useState(null); // raw File object for "Register as original"

  // Page-transition state
  const [displayView, setDisplayView]   = useState('landing');
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [enterKey, setEnterKey]         = useState(0);
  const transitionTimer = useRef(null);

  const navigateTo = (view) => {
    if (view === displayView && !isTransitioning) return;
    if (transitionTimer.current) clearTimeout(transitionTimer.current);
    setIsTransitioning(true);
    transitionTimer.current = setTimeout(() => {
      setDisplayView(view);
      setCurrentView(view);
      setEnterKey(k => k + 1);
      setIsTransitioning(false);
    }, 190);
  };

  useEffect(() => () => clearTimeout(transitionTimer.current), []);

  const handleStartScan = () => navigateTo('upload');

  const handleScanComplete = (data, file) => {
    setScanData(data);
    setScanFile(file || null);
    navigateTo('results');
  };

  const handleReset = () => {
    setScanData(null);
    setScanFile(null);
    navigateTo('upload');
  };

  const handleHomeReset = () => {
    setScanData(null);
    setScanFile(null);
    navigateTo('landing');
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#14171C] text-[#E7E9EC] font-sans selection:bg-[#4FD6C4]/30 selection:text-[#4FD6C4]">
      <Navbar
        activeTab={currentView}
        setActiveTab={(tab) => navigateTo(tab)}
        onResetToHome={handleHomeReset}
      />

      <main className="flex-grow">
        <div
          key={isTransitioning ? 'exiting' : 'stable'}
          className={isTransitioning ? 'page-exit' : ''}
        >
          <div key={enterKey} className="page-enter">
            {displayView === 'landing' && (
              <LandingPage
                onStartScan={handleStartScan}
                onNavigateToTransparency={() => navigateTo('transparency')}
              />
            )}

            {displayView === 'upload' && (
              <UploadPage onScanComplete={handleScanComplete} />
            )}

            {displayView === 'results' && (
              <ResultsPage
                scanData={scanData}
                onReset={handleReset}
                scanFile={scanFile}
              />
            )}

            {displayView === 'transparency' && (
              <SystemTransparency onStartScan={handleStartScan} />
            )}

            {displayView === 'registry' && (
              <RegistryPage />
            )}
          </div>
        </div>
      </main>

      <Footer onNavigateToTransparency={() => navigateTo('transparency')} />
    </div>
  );
}
