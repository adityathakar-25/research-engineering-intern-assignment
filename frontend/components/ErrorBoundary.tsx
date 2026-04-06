"use client";

import React, { Component, ReactNode } from "react";
import { AlertTriangle, RefreshCcw } from "lucide-react";

interface Props {
  children?: ReactNode;
  fallbackMessage?: string;
}

interface State {
  hasError: boolean;
}

export default class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(_: Error): State {
    return { hasError: true };
  }

  public componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Uncaught error boundary trap:", error, errorInfo);
  }

  public reset = () => {
    this.setState({ hasError: false });
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="bg-red-50 border border-red-100 rounded-xl p-6 flex flex-col items-center justify-center text-center space-y-4 shadow-sm min-h-[300px]">
          <div className="w-12 h-12 bg-red-100 text-red-600 flex items-center justify-center rounded-full mb-2">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-red-900">Render Failure</h3>
            <p className="text-sm text-red-700 mt-1 max-w-sm">
              {this.props.fallbackMessage || "Something went wrong loading this section."}
            </p>
          </div>
          <button
            onClick={this.reset}
            className="flex items-center gap-2 bg-white text-sm font-medium text-gray-700 border border-gray-300 px-4 py-2 rounded-full hover:bg-gray-50 transition-colors shadow-sm"
          >
            <RefreshCcw className="w-4 h-4" />
            Retry Component
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
