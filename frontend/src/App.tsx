import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import Dashboard from "./pages/Dashboard";

function App() {
  const [theme, setTheme] = useState(localStorage.getItem("theme") || "light");

  useEffect(() => {
    
    const root = window.document.documentElement;
    root.classList.remove("light", "dark");
    root.classList.add(theme);
    

    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(theme === "light" ? "dark" : "light");
  };

  return (
    // No need for className={theme} wrapper anymore since it's on <html>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage toggleTheme={toggleTheme} currentTheme={theme} />} />
        <Route path="/app" element={<Dashboard toggleTheme={toggleTheme} currentTheme={theme} />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;