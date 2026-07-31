import React, { useState } from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import LandingPage from "./LandingPage.jsx";

function Root() {
  const [launched, setLaunched] = useState(false);
  return launched ? <App /> : <LandingPage onLaunch={() => setLaunched(true)} />;
}

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>
);