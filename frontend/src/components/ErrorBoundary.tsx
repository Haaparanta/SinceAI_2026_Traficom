import { Component, type ErrorInfo, type ReactNode } from "react";

/** Keeps one broken view from blanking the whole screen: shows what failed and a way back. */
export class ErrorBoundary extends Component<{ children: ReactNode; label?: string }, { error: Error | null }> {
  state: { error: Error | null } = { error: null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error(`Filing Radar: ${this.props.label ?? "view"} failed`, error, info.componentStack);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div role="alert" className="p-4 text-sm space-y-2">
        <p className="font-semibold">This {this.props.label ?? "view"} could not be shown.</p>
        <p className="text-muted-foreground break-words">{this.state.error.message}</p>
        <button type="button" onClick={() => this.setState({ error: null })}
          className="min-h-11 rounded-full border border-border px-4 font-semibold hover:bg-muted">
          Try again
        </button>
      </div>
    );
  }
}
