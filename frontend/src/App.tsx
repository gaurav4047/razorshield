import { useState, useEffect } from "react";
import Dashboard from "./pages/Dashboard";
import LandingPage from "./pages/LandingPage";

export default function App() {
  const [view, setView] = useState<"landing" | "console">(() => {
    const hash = window.location.hash;
    const path = window.location.pathname;
    if (hash === "#/console" || path === "/console" || path === "/dashboard") {
      return "console";
    }
    return "landing";
  });

  useEffect(() => {
    const handlePopState = () => {
      const hash = window.location.hash;
      const path = window.location.pathname;
      if (hash === "#/console" || path === "/console" || path === "/dashboard") {
        setView("console");
      } else {
        setView("landing");
      }
    };
    window.addEventListener("popstate", handlePopState);
    window.addEventListener("hashchange", handlePopState);
    return () => {
      window.removeEventListener("popstate", handlePopState);
      window.removeEventListener("hashchange", handlePopState);
    };
  }, []);

  const navigateToConsole = () => {
    window.location.hash = "#/console";
    setView("console");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const navigateToLanding = () => {
    window.location.hash = "#/";
    setView("landing");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  if (view === "console") {
    return <Dashboard onBackToLanding={navigateToLanding} />;
  }

  return <LandingPage onLaunchConsole={navigateToConsole} />;
}

