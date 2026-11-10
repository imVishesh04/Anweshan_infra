import { Component, Suspense, lazy, useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import Home from "@/pages/Home";

// The admin panel is only for the owner; customers never download its code.
const Admin = lazy(() => import("@/pages/Admin"));

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { err: false };
  }
  static getDerivedStateFromError() {
    return { err: true };
  }
  render() {
    if (this.state.err) {
      return (
        <div className="min-h-screen grid place-items-center bg-cream text-espresso">
          <div className="text-center px-6">
            <p className="font-serif text-3xl">Something went wrong</p>
            <p className="mt-3 text-espresso-muted">Please refresh the page.</p>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <ScrollToTop />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route
            path="/admin"
            element={
              <Suspense fallback={<div className="min-h-screen bg-espresso" />}>
                <Admin />
              </Suspense>
            }
          />
          <Route path="*" element={<Home />} />
        </Routes>
        <Toaster position="top-center" richColors closeButton />
      </BrowserRouter>
    </ErrorBoundary>
  );
}
