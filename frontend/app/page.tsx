"use client";

import { useRef, useState, useEffect } from "react";
import {
  MoonIcon,
  SunIcon,
  Timer,
  Power,
  Menu,
  X,
  ArrowUpRight,
} from "lucide-react";
import { useTheme } from "next-themes";
import { toast } from "sonner";
import { increaseTimeout, stopSandboxAction } from "@/app/actions";
import { motion, AnimatePresence } from "framer-motion";
import { ChatList } from "@/components/chat/message-list";
import { ChatInput } from "@/components/chat/input";
import { ExamplePrompts } from "@/components/chat/example-prompts";
import { useChat } from "@/lib/chat-context";
import Frame from "@/components/frame";
import { Button } from "@/components/ui/button";
import { Loader, AssemblyLoader } from "@/components/loader";
import Link from "next/link";
import Logo from "@/components/logo";
import { RepoBanner } from "@/components/repo-banner";
import { SANDBOX_TIMEOUT_MS } from "@/lib/config";
import { Surfing } from "@/components/surfing";

export default function Home() {
  const [sandboxId, setSandboxId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [vncUrl, setVncUrl] = useState<string | null>(null);
  const { theme, setTheme } = useTheme();
  const [timeRemaining, setTimeRemaining] = useState<number>(
    SANDBOX_TIMEOUT_MS / 1000
  );
  const [isTabVisible, setIsTabVisible] = useState<boolean>(true);
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const iFrameWrapperRef = useRef<HTMLDivElement>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const {
    messages,
    isLoading: chatLoading,
    input,
    setInput,
    sendMessage,
    stopGeneration,
    clearMessages,
    handleSubmit,
    onSandboxCreated,
  } = useChat();

  useEffect(() => {
    const handleVisibilityChange = () => {
      setIsTabVisible(document.visibilityState === "visible");
    };

    setIsTabVisible(document.visibilityState === "visible");

    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, []);

  const stopSandbox = async () => {
    if (sandboxId) {
      try {
        stopGeneration();
        const success = await stopSandboxAction(sandboxId);
        if (success) {
          setSandboxId(null);
          setVncUrl(null);
          clearMessages();
          setTimeRemaining(SANDBOX_TIMEOUT_MS / 1000);
          toast("Sandbox instance stopped");
        } else {
          toast.error("Failed to stop sandbox instance");
        }
      } catch (error) {
        console.error("Failed to stop sandbox:", error);
        toast.error("Failed to stop sandbox");
      }
    }
  };

  const handleIncreaseTimeout = async () => {
    if (!sandboxId) return;

    try {
      await increaseTimeout(sandboxId);
      setTimeRemaining(SANDBOX_TIMEOUT_MS / 1000);
      toast.success("Instance time increased");
    } catch (error) {
      console.error("Failed to increase time:", error);
      toast.error("Failed to increase time");
    }
  };

  const onSubmit = (e: React.FormEvent) => {
    const content = handleSubmit(e);
    if (content) {
      const width =
        iFrameWrapperRef.current?.clientWidth ||
        (window.innerWidth < 768 ? window.innerWidth - 32 : 1024);
      const height =
        iFrameWrapperRef.current?.clientHeight ||
        (window.innerWidth < 768
          ? Math.min(window.innerHeight * 0.4, 400)
          : 768);

      sendMessage({
        content,
        sandboxId: sandboxId || undefined,
        environment: "linux",
        resolution: [width, height],
      });
    }
  };

  const handleExampleClick = (prompt: string) => {
    const width =
      iFrameWrapperRef.current?.clientWidth ||
      (window.innerWidth < 768 ? window.innerWidth - 32 : 1024);
    const height =
      iFrameWrapperRef.current?.clientHeight ||
      (window.innerWidth < 768 ? Math.min(window.innerHeight * 0.4, 400) : 768);

    sendMessage({
      content: prompt,
      sandboxId: sandboxId || undefined,
      environment: "linux",
      resolution: [width, height],
    });
  };

  const handleSandboxCreated = (newSandboxId: string, newVncUrl: string) => {
    setSandboxId(newSandboxId);
    setVncUrl(newVncUrl);
    setTimeRemaining(SANDBOX_TIMEOUT_MS / 1000);
    toast.success("Sandbox instance created");
  };

  const handleClearChat = () => {
    clearMessages();
    toast.success("Chat cleared");
  };

  const ThemeToggle = () => (
    <Button
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
      variant="outline"
      size="icon"
      suppressHydrationWarning
    >
      {theme === "dark" ? (
        <SunIcon className="h-5 w-5" suppressHydrationWarning />
      ) : (
        <MoonIcon className="h-5 w-5" suppressHydrationWarning />
      )}
    </Button>
  );

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
      toast.error("Instance time expired");
      setTimeRemaining(SANDBOX_TIMEOUT_MS / 1000);
    }
  }, [timeRemaining, sandboxId, stopGeneration, clearMessages, isTabVisible]);

  useEffect(() => {
    onSandboxCreated((newSandboxId: string, newVncUrl: string) => {
      handleSandboxCreated(newSandboxId, newVncUrl);
    });
  }, [onSandboxCreated]);

  return (
  return (
    <div className="min-h-screen bg-background text-foreground p-4 md:p-6 overflow-hidden flex flex-col gap-4 font-sans selection:bg-cyan-500/30">
      {/* Top Bar: Command Deck */}
      <header className="flex items-center justify-between glass-panel p-4 rounded-2xl z-20">
        <div className="flex items-center gap-4">
          <Link href="/" className="group flex items-center gap-3">
            <Logo width={32} height={32} className="transition-transform group-hover:scale-110 group-hover:rotate-12" />
            <div className="flex flex-col">
              <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-purple-400">
                OpenCompX
              </h1>
              <span className="text-[10px] uppercase tracking-widest text-cyan-500/70 font-mono">
                Autonomous Desktop Agent
              </span>
            </div>
          </Link>
        </div>

        <div className="flex items-center gap-3">
          <RepoBanner />
          <ThemeToggle />
          {/* Mobile Menu Toggle */}
          <div className="md:hidden">
            <Button onClick={() => setMobileMenuOpen(!mobileMenuOpen)} variant="ghost" size="icon">
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </Button>
          </div>
        </div>
      </header>

      {/* Main Holo-Deck (Bento Grid) */}
      <main className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 relative z-10 min-h-0">

        {/* Agent Vision (VNC) - Spans 8 cols */}
        <section className="col-span-1 lg:col-span-8 flex flex-col gap-4 min-h-[400px]">
          <div className="glass-panel w-full flex-1 rounded-2xl relative overflow-hidden flex flex-col border-cyan-500/20 shadow-[0_0_30px_rgba(0,212,255,0.05)]">
            {/* Header */}
            <div className="absolute top-0 left-0 right-0 h-10 bg-black/40 backdrop-blur-md border-b border-white/5 flex items-center justify-between px-4 z-10">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                <span className="text-xs font-mono text-cyan-300 tracking-wider">LIVE_FEED // VNC_SECURE</span>
              </div>
              <div className="flex items-center gap-2">
                {sandboxId && (
                  <div className="flex items-center gap-2 px-2 py-1 bg-cyan-900/20 rounded border border-cyan-500/20">
                    <Timer className="w-3 h-3 text-cyan-400" />
                    <span className="text-xs font-mono text-cyan-400">
                      {Math.floor(timeRemaining / 60)}:{(timeRemaining % 60).toString().padStart(2, "0")}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Viewport */}
            <div ref={iFrameWrapperRef} className="flex-1 w-full h-full relative group">
              {isLoading || (chatLoading && !sandboxId) ? (
                <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/80">
                  <Loader variant="square" className="text-cyan-400 w-12 h-12" />
                  <div className="mt-4 font-mono text-cyan-500 animate-pulse">
                    INITIALIZING_NEURAL_LINK...
                  </div>
                </div>
              ) : sandboxId && vncUrl ? (
                <iframe
                  ref={iframeRef}
                  src={vncUrl}
                  className="w-full h-full object-cover"
                  allow="clipboard-read; clipboard-write"
                />
              ) : (
                <div className="absolute inset-0 flex flex-col items-center justify-center bg-[url('/grid-pattern.svg')] bg-center opacity-80">
                  <div className="w-24 h-24 rounded-full bg-cyan-500/10 flex items-center justify-center mb-4 animate-pulse-slow ring-1 ring-cyan-500/30">
                    <Power className="w-10 h-10 text-cyan-400" />
                  </div>
                  <h2 className="text-2xl font-light text-white mb-2">System Standby</h2>
                  <p className="text-zinc-500 max-w-sm text-center">
                    Initiate a task via the command terminal to wake the agent.
                  </p>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Command Terminal (Chat) - Spans 4 cols */}
        <section className="col-span-1 lg:col-span-4 h-full flex flex-col min-h-[500px]">
          <div className="glass-panel w-full flex-1 rounded-2xl flex flex-col overflow-hidden border-purple-500/20 relative">

            {/* Terminal Header */}
            <div className="h-12 border-b border-white/5 bg-white/5 flex items-center px-4 justify-between shrink-0">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-purple-400 uppercase tracking-widest">Command Terminal</span>
              </div>
              {sandboxId && (
                <Button onClick={stopSandbox} variant="destructive" size="xs" className="h-7 text-[10px] uppercase tracking-wide">
                  <Power className="w-3 h-3 mr-1" /> Terminate
                </Button>
              )}
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto relative scrollbar-thin scrollbar-thumb-purple-900/50 scrollbar-track-transparent">
              <ChatList messages={messages} className="p-4" />
              {messages.length === 0 && (
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none p-6">
                  <ExamplePrompts onPromptClick={handleExampleClick} className="w-full pointer-events-auto" />
                </div>
              )}
            </div>

            {/* Input Area */}
            <div className="p-4 bg-black/20 border-t border-white/5 shrink-0">
              <ChatInput
                input={input}
                setInput={setInput}
                onSubmit={onSubmit}
                isLoading={chatLoading}
                onStop={stopGeneration}
                className="w-full"
              />
            </div>

          </div>
        </section>

      </main>
    </div>
  );
}
