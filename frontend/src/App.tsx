import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import Dashboard from "./pages/Dashboard";

function App() {
  const [theme, setTheme] = useState(localStorage.getItem("theme") || "light");

  useEffect(() => {
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(theme === "light" ? "dark" : "light");
  };

  return (
    <div className={theme}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage toggleTheme={toggleTheme} currentTheme={theme} />} />
          <Route path="/app" element={<Dashboard toggleTheme={toggleTheme} currentTheme={theme} />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;