import { Component } from 'react';

export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-8 max-w-6xl mx-auto">
          <div className="bg-red-950/30 border border-red-900 rounded-lg p-6">
            <h2 className="text-xl font-bold text-red-500 mb-2">Frontend Crash Detected</h2>
            <p className="text-red-300 text-sm mb-4">
              An unhandled exception occurred during rendering. This is likely due to malformed data from the backend.
            </p>
            <pre className="text-xs text-red-400 bg-red-950/50 p-4 rounded-md overflow-x-auto">
              {this.state.error?.toString()}
              {'\n\n'}
              {this.state.error?.stack}
            </pre>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
