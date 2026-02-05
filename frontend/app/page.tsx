"use client";

import { useRef, useState, useEffect, useCallback } from "react";
import {
  Power,
  Bot,
  MousePointer2,
  Monitor,
  MessageSquare,
  Github,
  Play,
  Square,
  Loader2,
} from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { ChatList } from "@/components/chat/message-list";
import { ChatInput } from "@/components/chat/input";
import { ExamplePrompts } from "@/components/chat/example-prompts";
import { useChat } from "@/lib/chat-context";
import { Button } from "@/components/ui/button";
import { Loader } from "@/components/loader";
import Link from "next/link";
import { SANDBOX_TIMEOUT_MS } from "@/lib/config";

// ============================================================================
// COMPONENTS
// ============================================================================

/** Header Component */
function Header() {
  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-slate-200/60 bg-white/80 backdrop-blur-xl">
      <Link href="/" className="flex items-center gap-3 group">
        <div className="size-10 rounded-xl bg-slate-900 flex items-center justify-center text-white font-bold text-sm shadow-lg shadow-slate-900/20 group-hover:shadow-slate-900/40 transition-shadow">
          OX
        </div>
        <div className="flex flex-col">
          <h1 className="text-xl font-semibold text-slate-900">OpenCompX</h1>
          <span className="text-[10px] uppercase tracking-widest text-slate-500 font-medium">
            Autonomous Desktop Agent
          </span>
        </div>
      </Link>

      <a
        href="https://github.com/e2b-dev/opencompx"
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-900 text-white text-sm font-medium hover:bg-slate-800 transition-colors shadow-lg"
      >
        <Github className="w-4 h-4" />
        <span className="hidden sm:inline">Star on GitHub</span>
      </a>
    </header>
  );
}

/** Desktop Viewer Component */
function DesktopViewer({
  vncUrl,
  isLoading,
  sandboxId,
  isControlOverride,
  setIsControlOverride,
  iframeRef,
  iFrameWrapperRef,
}: {
  vncUrl: string | null;
  isLoading: boolean;
  sandboxId: string | null;
  isControlOverride: boolean;
  setIsControlOverride: (value: boolean) => void;
  iframeRef: React.RefObject<HTMLIFrameElement | null>;
  iFrameWrapperRef: React.RefObject<HTMLDivElement | null>;
}) {
  const showLoading = isLoading;
  const showDesktop = sandboxId && vncUrl;
  const showStandby = !showLoading && !showDesktop;

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-white rounded-xl p-3 border border-slate-200 shadow-sm transition-all duration-300 hover:shadow-md overflow-hidden">
      {/* Desktop Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 bg-slate-50/50">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <div className={cn(
              "w-2.5 h-2.5 rounded-full transition-colors",
              showDesktop ? "bg-emerald-500 animate-pulse" : "bg-slate-300"
            )} />
            <span className="text-xs font-medium text-slate-600">
              {showDesktop ? "Live" : "Offline"}
            </span>
          </div>
          <div className="h-4 w-px bg-slate-200" />
          <div className="flex items-center gap-1.5 text-slate-500">
            <Monitor className="w-3.5 h-3.5" />
            <span className="text-xs font-medium">Desktop View</span>
          </div>
        </div>
      </div>

      {/* Desktop Content */}
      <div ref={iFrameWrapperRef} className="flex-1 relative bg-slate-100">
        {showLoading && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-white/80 dark:bg-[#0a0a0a]/90 backdrop-blur-sm z-50">
            <div className="flex flex-col items-center gap-4">
              <Loader2 className="w-8 h-8 text-slate-900 dark:text-white animate-spin" />
              <p className="text-sm font-medium text-slate-500 dark:text-slate-400 animate-pulse">
                Starting Desktop...
              </p>
            </div>
          </div>
        )}

        {showDesktop && (
          <>
            <iframe
              ref={iframeRef}
              src={vncUrl}
              className={cn(
                "w-full h-full border-0",
                !isControlOverride && "pointer-events-none"
              )}
              allow="clipboard-read; clipboard-write"
            />

            {/* Agent Working Indicator - Bottom Glow */}
            {!isControlOverride && (
              <div className="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-slate-900/10 via-slate-900/5 to-transparent pointer-events-none animate-pulse" />
            )}

            {/* Agent Control Badge */}
            <div className="absolute bottom-4 right-4 z-10">
              {!isControlOverride ? (
                <Button
                  onClick={() => setIsControlOverride(true)}
                  className="bg-white/95 backdrop-blur-sm text-slate-700 border border-slate-200 shadow-lg hover:bg-white hover:shadow-xl transition-all"
                  size="sm"
                >
                  <Bot className="w-4 h-4 mr-2 text-slate-900 animate-pulse" />
                  Agent Active
                  <MousePointer2 className="w-3 h-3 ml-2 text-slate-400" />
                </Button>
              ) : (
                <Button
                  onClick={() => setIsControlOverride(false)}
                  className="bg-slate-900 text-white shadow-lg hover:bg-slate-800 transition-all"
                  size="sm"
                >
                  <Play className="w-4 h-4 mr-2" />
                  Resume Agent
                </Button>
              )}
            </div>
          </>
        )}

        {showStandby && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100">
            <div className="flex flex-col items-center gap-6 max-w-md text-center px-6">
              <div className="relative">
                <div className="w-20 h-20 rounded-[28px] bg-slate-100 flex items-center justify-center">
                  <Power className="w-10 h-10 text-slate-400" />
                </div>
              </div>
              <div>
                <h2 className="text-xl font-semibold text-slate-900 mb-2">
                  Ready to Start
                </h2>
                <p className="text-sm text-slate-500 leading-relaxed">
                  Send a message to wake the agent and start automating your desktop tasks.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/** Chat Panel Component */
function ChatPanel({
  messages,
  input,
  setInput,
  image,
  setImage,
  selectedTool,
  setSelectedTool,
  onSubmit,
  isLoading,
  onStop,
  onExampleClick,
  sandboxId,
  onStopSandbox,
}: {
  messages: any[];
  input: string;
  setInput: (value: string) => void;
  image: string | null;
  setImage: (value: string | null) => void;
  selectedTool: string | null;
  setSelectedTool: (value: string | null) => void;
  onSubmit: (e: React.FormEvent) => void;
  isLoading: boolean;
  onStop: () => void;
  onExampleClick: (prompt: string) => void;
  sandboxId: string | null;
  onStopSandbox: () => void;
}) {
  return (
    <div className="w-full lg:w-[450px] flex flex-col min-h-0 bg-white dark:bg-[#1a1a1a] rounded-xl p-3 border border-slate-200 dark:border-slate-800 shadow-sm transition-all duration-300 hover:shadow-md overflow-hidden">
      {/* Chat Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 bg-slate-50/50">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-slate-600" />
          <span className="text-sm font-semibold text-slate-900">Chat</span>
        </div>
        {sandboxId && (
          <Button
            onClick={onStopSandbox}
            variant="destructive"
            size="sm"
            className="h-7 text-xs font-medium px-3 shadow-sm hover:bg-red-600 transition-colors"
          >
            <Square className="w-3 h-3 mr-1.5 fill-current" />
            Stop Desktop
          </Button>
        )}
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto relative">
        {messages.length > 0 ? (
          <ChatList messages={messages} className="p-4" />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center p-4">
            <ExamplePrompts
              onPromptClick={onExampleClick}
              className="w-full"
            />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-slate-100 bg-slate-50/30">
        <ChatInput
          input={input}
          setInput={setInput}
          image={image}
          setImage={setImage}
          selectedTool={selectedTool}
          setSelectedTool={setSelectedTool}
          onSubmit={onSubmit}
          isLoading={isLoading}
          onStop={onStop}
          placeholder="Ask the agent to do something..."
          className="w-full"
        />
      </div>
    </div>
  );
}

// ============================================================================
// MAIN PAGE
// ============================================================================

export default function Home() {
  // State
  const [sandboxId, setSandboxId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [vncUrl, setVncUrl] = useState<string | null>(null);
  const [timeRemaining, setTimeRemaining] = useState<number>(SANDBOX_TIMEOUT_MS / 1000);
  const [isTabVisible, setIsTabVisible] = useState<boolean>(true);
  const [isControlOverride, setIsControlOverride] = useState(false);

  // Refs
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const iFrameWrapperRef = useRef<HTMLDivElement>(null);

  // Chat Hook
  const {
    messages,
    isLoading: chatLoading,
    input,
    setInput,
    image,
    setImage,
    selectedTool,
    setSelectedTool,
    sendMessage,
    stopGeneration,
    clearMessages,
    handleSubmit,
    onSandboxCreated,
  } = useChat();

  // Visibility tracking
  useEffect(() => {
    const handleVisibilityChange = () => {
      setIsTabVisible(document.visibilityState === "visible");
    };
    setIsTabVisible(document.visibilityState === "visible");
    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => document.removeEventListener("visibilitychange", handleVisibilityChange);
  }, []);

  // Sandbox handlers
  const stopSandbox = useCallback(async () => {
    if (!sandboxId) return;
    try {
      stopGeneration();
      // Local Docker logic - just clear state
      setSandboxId(null);
      setVncUrl(null);
      clearMessages();
      setTimeRemaining(SANDBOX_TIMEOUT_MS / 1000);
      toast.success("Session ended");
    } catch (error) {
      console.error("Failed to stop sandbox:", error);
      toast.error("Failed to stop session");
    }
  }, [sandboxId, stopGeneration, clearMessages]);

  const handleIncreaseTimeout = useCallback(async () => {
    if (!sandboxId) return;
    // Local Docker mode - just reset timer
    setTimeRemaining(SANDBOX_TIMEOUT_MS / 1000);
  }, [sandboxId]);

  // Message handlers
  const getResolution = useCallback((): [number, number] => {
    const width = iFrameWrapperRef.current?.clientWidth || (window.innerWidth < 768 ? window.innerWidth - 32 : 1024);
    const height = iFrameWrapperRef.current?.clientHeight || (window.innerWidth < 768 ? Math.min(window.innerHeight * 0.4, 400) : 768);
    return [width, height];
  }, []);

  const onSubmit = useCallback((e: React.FormEvent) => {
    const content = handleSubmit(e);
    if (content) {
      sendMessage({
        content,
        sandboxId: sandboxId || undefined,
        environment: "linux",
        resolution: getResolution(),
      });
    }
  }, [handleSubmit, sendMessage, sandboxId, getResolution]);

  const handleExampleClick = useCallback((prompt: string) => {
    sendMessage({
      content: prompt,
      sandboxId: sandboxId || undefined,
      environment: "linux",
      resolution: getResolution(),
    });
  }, [sendMessage, sandboxId, getResolution]);

  // Timer effects
  useEffect(() => {
    if (!sandboxId) return;
    const interval = setInterval(() => {
      if (isTabVisible) {
        setTimeRemaining((prev) => (prev > 0 ? prev - 1 : 0));
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [sandboxId, isTabVisible]);

  useEffect(() => {
    if (!sandboxId) return;
    if (timeRemaining === 10 && isTabVisible) {
      handleIncreaseTimeout();
    }
    if (timeRemaining === 0) {
      setSandboxId(null);
      setVncUrl(null);
      clearMessages();
      stopGeneration();
      toast.error("Session expired");
      setTimeRemaining(SANDBOX_TIMEOUT_MS / 1000);
    }
  }, [timeRemaining, sandboxId, stopGeneration, clearMessages, isTabVisible, handleIncreaseTimeout]);

  // Sandbox creation callback
  useEffect(() => {
    onSandboxCreated((newSandboxId: string, newVncUrl: string) => {
      setSandboxId(newSandboxId);
      setVncUrl(newVncUrl);
      setTimeRemaining(SANDBOX_TIMEOUT_MS / 1000);
      toast.success("Desktop ready");
    });
  }, [onSandboxCreated]);

  return (
    <div className="h-screen flex flex-col bg-slate-50">
      <Header />

      <main className="flex-1 flex flex-col lg:flex-row gap-4 p-4 lg:p-6 min-h-0">
        {/* Desktop Viewer */}
        <DesktopViewer
          vncUrl={vncUrl}
          isLoading={isLoading || (chatLoading && !sandboxId)}
          sandboxId={sandboxId}
          isControlOverride={isControlOverride}
          setIsControlOverride={setIsControlOverride}
          iframeRef={iframeRef}
          iFrameWrapperRef={iFrameWrapperRef}
        />

        {/* Chat Panel */}
        <ChatPanel
          messages={messages}
          input={input}
          setInput={setInput}
          image={image}
          setImage={setImage}
          selectedTool={selectedTool}
          setSelectedTool={setSelectedTool}
          onSubmit={onSubmit}
          isLoading={chatLoading}
          onStop={stopGeneration}
          onExampleClick={handleExampleClick}
          sandboxId={sandboxId}
          onStopSandbox={stopSandbox}
        />
      </main>
    </div>
  );
}
