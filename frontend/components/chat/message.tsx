"use client";

import React, { useState } from "react";
import {
  ChatMessage as ChatMessageType,
  ActionChatMessage,
  AssistantChatMessage,
} from "@/types/chat";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { cva, VariantProps } from "class-variance-authority";
import {
  Terminal,
  AlertCircle,
  CheckCircle2,
  Clock,
  User,
  Bot,
  ChevronDown,
  ChevronUp,
  Cpu,
  MousePointer2,
  Keyboard,
  AppWindow,
  Copy,
  Check,
} from "lucide-react";
import { useChat } from "@/lib/chat-context";
import { Badge } from "../ui/badge";
import { Markdown as MemoizedReactMarkdown } from "@/components/markdown";
import { Button } from "@/components/ui/button";
import { Typewriter } from "../ui/typewriter";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";

const messageVariants = cva("w-full transition-all duration-300 ease-in-out", {
  variants: {
    role: {
      user: "bg-primary/10 border-primary/20",
      assistant: "bg-card border-border/50 shadow-sm",
      system: "bg-muted/30 border-dashed border-muted-foreground/30",
    },
  },
  defaultVariants: {
    role: "system",
  },
});

interface ChatMessageProps extends VariantProps<typeof messageVariants> {
  message: ChatMessageType;
  className?: string;
}

// Helper to make python code user-friendly
const parseAction = (code: string) => {
  if (!code) return { title: "Executing Action", icon: Cpu };

  if (code.includes("write") || code.includes("type")) {
    const match = code.match(/write\(['"](.+?)['"]\)/);
    return {
      title: match ? `Typing "${match[1]}"` : "Typing text...",
      icon: Keyboard
    };
  }
  if (code.includes("click")) {
    const match = code.match(/click\((\d+),\s*(\d+)/);
    return {
      title: match ? `Clicking at (${match[1]}, ${match[2]})` : "Clicking mouse...",
      icon: MousePointer2
    };
  }
  if (code.includes("launch")) {
    const match = code.match(/launch\(['"](.+?)['"]\)/);
    return {
      title: match ? `Launching ${match[1]}` : "Launching application...",
      icon: AppWindow
    };
  }
  if (code.includes("scroll")) return { title: "Scrolling page...", icon: MousePointer2 };
  if (code.includes("wait")) return { title: "Waiting...", icon: Clock };

  return { title: "Executing System Command", icon: Terminal };
};

function ActionMessageDisplay({
  message,
  className,
}: {
  message: ActionChatMessage;
  className?: string;
}) {
  const { action, status } = message;
  const [isOpen, setIsOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  // Extract code string safely
  const codeString = typeof action === 'string'
    ? action
    : (action as any)?.code || JSON.stringify(action, null, 2);

  const { title, icon: Icon } = parseAction(codeString);

  const handleCopy = () => {
    navigator.clipboard.writeText(codeString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const statusColors = {
    completed: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20",
    failed: "text-destructive bg-destructive/10 border-destructive/20",
    pending: "text-amber-500 bg-amber-500/10 border-amber-500/20",
  };

  return (
    <div className={cn("flex justify-start w-full max-w-full my-4 pl-4", className)}>
      <Card
        className={cn(
          "w-full overflow-hidden border transition-all duration-300 backdrop-blur-md",
          status === "completed" ? "bg-cyan-950/20 border-cyan-500/30" : "bg-zinc-950/40 border-white/10",
          status === "pending" && "border-amber-500/30 ring-1 ring-amber-500/10"
        )}
      >
        <div className="flex items-center justify-between p-2 pl-3">
          <div className="flex items-center gap-3">
            <div className={cn("p-1.5 rounded-md", statusColors[status || "pending"])}>
              <Icon className="h-4 w-4" />
            </div>

            <div className="flex flex-col">
              <span className="text-xs font-bold text-cyan-100 uppercase tracking-wide">{title}</span>
              <span className="text-[10px] text-cyan-500/70 font-mono truncate max-w-[200px]">
                {codeString.slice(0, 50)}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {status === "pending" && (
              <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-500 text-[10px] font-medium border border-amber-500/20">
                <Clock className="w-2.5 h-2.5 animate-spin" />
                <span>PROCESSING</span>
              </div>
            )}

            <Collapsible open={isOpen} onOpenChange={setIsOpen}>
              <CollapsibleTrigger asChild>
                <Button variant="ghost" size="sm" className="h-6 w-6 p-0 hover:bg-cyan-500/20 hover:text-cyan-300">
                  {isOpen ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                </Button>
              </CollapsibleTrigger>
            </Collapsible>
          </div>
        </div>

        <Collapsible open={isOpen} className="border-t border-white/5">
          <CollapsibleContent>
            <div className="p-3 bg-black/50 font-mono text-[10px] text-cyan-300/80 overflow-x-auto relative group">
              <Button
                size="icon"
                variant="ghost"
                className="absolute right-1 top-1 h-5 w-5 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-white/10"
                onClick={handleCopy}
              >
                {copied ? <Check className="h-3 w-3 text-green-500" /> : <Copy className="h-3 w-3" />}
              </Button>
              <pre className="whitespace-pre-wrap">{codeString}</pre>
            </div>
          </CollapsibleContent>
        </Collapsible>
      </Card>
    </div>
  );
}

function ThinkingProcess({ content }: { content: string }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="w-full mb-2">
      <Collapsible open={isOpen} onOpenChange={setIsOpen} className="w-full">
        <div className="flex items-center gap-2">
          <CollapsibleTrigger className="group flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 hover:bg-white/10 transition-all border border-white/5 hover:border-cyan-500/30">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
            </span>
            <span className="text-[10px] font-mono font-medium text-cyan-200/70 group-hover:text-cyan-100 uppercase tracking-widest">
              Thinking Process
            </span>
            {isOpen ? (
              <ChevronUp className="h-3 w-3 text-cyan-500/50" />
            ) : (
              <ChevronDown className="h-3 w-3 text-cyan-500/50" />
            )}
          </CollapsibleTrigger>
        </div>

        <CollapsibleContent>
          <div className="mt-3 ml-2 pl-4 border-l border-cyan-500/20">
            <div className="prose prose-sm prose-invert max-w-none break-words font-mono text-xs text-cyan-100/80">
              <Typewriter content={content} speed={1}>
                {(text: string) => <MemoizedReactMarkdown>{text}</MemoizedReactMarkdown>}
              </Typewriter>
            </div>
          </div>
        </CollapsibleContent>
      </Collapsible>
    </div>
  );
}

export function ChatMessage({ message, className }: ChatMessageProps) {
  const role = message.role;
  const isUser = role === "user";
  const isAssistant = role === "assistant";
  const isAction = role === "action";
  const isSystem = role === "system";
  const isError = "isError" in message && message.isError;

  if (isSystem) {
    return (
      <div className="w-full flex justify-center py-6">
        <Badge
          variant={isError ? "error" : "outline"}
          className="px-4 py-1 text-[10px] font-mono tracking-widest text-cyan-500/60 bg-black/40 border-cyan-500/10 uppercase"
        >
          {message.content}
        </Badge>
      </div>
    );
  }

  if (isAction) {
    return (
      <ActionMessageDisplay
        message={message as ActionChatMessage}
        className={className}
      />
    );
  }

  // If assistant, use ThinkingProcess style
  // If user, use standard Command style
  if (isAssistant) {
    return (
      <div className={cn("flex w-full mb-4 justify-start", className)}>
        <div className="flex flex-col max-w-[90%] items-start">
          <ThinkingProcess content={message.content} />
        </div>
      </div>
    );
  }

  const roleLabel = "COMMAND // USER";

  return (
    <div
      className={cn(
        "flex w-full mb-6 justify-end",
        className
      )}
    >
      <div className="flex flex-col max-w-[90%] items-end">

        <div className="flex items-center gap-2 mb-1 opacity-70">
          <span className="text-[10px] font-bold font-mono tracking-widest text-purple-500/50 uppercase">
            {roleLabel}
          </span>
          <User className="h-3 w-3 text-purple-400" />
        </div>

        <div className="rounded-2xl px-5 py-4 shadow-lg text-sm leading-relaxed backdrop-blur-md border bg-gradient-to-br from-purple-900/40 to-blue-900/40 border-purple-500/30 text-purple-100 rounded-tr-none shadow-[0_0_15px_rgba(168,85,247,0.1)]">
          <div className="whitespace-pre-wrap font-sans">{message.content}</div>
        </div>
      </div>
    </div>
  );
}
