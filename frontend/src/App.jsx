import React, { useState } from 'react';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import LandingPage from './components/LandingPage';
import UploadPage from './components/UploadPage';
import ResultsPage from './components/ResultsPage';

export default function App() {
  const [currentView, setCurrentView] = useState('landing'); // 'landing' | 'upload' | 'results'
  const [preselectedModule, setPreselectedModule] = useState('auto');
  const [scanData, setScanData] = useState(null);

  const handleStartScan = (moduleType = 'auto') => {
    setPreselectedModule(moduleType);
    setCurrentView('upload');
  };

  const handleScanComplete = (data) => {
    setScanData(data);
    setCurrentView('results');
  };

  const handleReset = () => {
    setScanData(null);
    setCurrentView('upload');
  };

  const handleHomeReset = () => {
    setScanData(null);
    setCurrentView('landing');
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#14171C] text-[#E7E9EC] font-sans selection:bg-[#4FD6C4]/30 selection:text-[#4FD6C4]">
      <Navbar 
        activeTab={currentView} 
        setActiveTab={(tab) => setCurrentView(tab)} 
        onResetToHome={handleHomeReset} 
      />

      <main className="flex-grow">
        {currentView === 'landing' && (
          <LandingPage 
            onStartScan={handleStartScan} 
            onSelectModule={handleStartScan} 
          />
        )}

        {currentView === 'upload' && (
          <UploadPage 
            selectedModule={preselectedModule} 
            onScanComplete={handleScanComplete} 
          />
        )}

        {currentView === 'results' && (
          <ResultsPage 
            scanData={scanData} 
            onReset={handleReset} 
          />
        )}
      </main>

      <Footer />
    </div>
  );
}
