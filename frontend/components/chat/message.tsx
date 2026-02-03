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
    : action?.code || JSON.stringify(action, null, 2);

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
    <div className={cn("flex justify-start w-full max-w-2xl my-4", className)}>
      <Card
        className={cn(
          "w-full overflow-hidden border transition-all hover:shadow-md",
          status === "completed" ? "bg-card/50" : "bg-card",
          status === "pending" && "border-amber-500/30 ring-1 ring-amber-500/10"
        )}
      >
        <div className="flex items-center justify-between p-3">
          <div className="flex items-center gap-3">
            <div className={cn("p-2 rounded-lg", statusColors[status || "pending"])}>
              <Icon className="h-5 w-5" />
            </div>

            <div className="flex flex-col">
              <span className="text-sm font-medium text-foreground">{title}</span>
              <span className="text-xs text-muted-foreground font-mono truncate max-w-[200px] opacity-70">
                {codeString.slice(0, 40)}{codeString.length > 40 && "..."}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {status === "pending" && (
              <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 text-amber-500 text-xs font-medium">
                <Clock className="w-3 h-3 animate-spin" />
                <span>Running</span>
              </div>
            )}

            <Collapsible open={isOpen} onOpenChange={setIsOpen}>
              <CollapsibleTrigger asChild>
                <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                  {isOpen ? (
                    <ChevronUp className="h-4 w-4" />
                  ) : (
                    <ChevronDown className="h-4 w-4" />
                  )}
                </Button>
              </CollapsibleTrigger>
            </Collapsible>
          </div>
        </div>

        <Collapsible open={isOpen} className="border-t border-border/50">
          <CollapsibleContent>
            <div className="p-3 bg-muted/50 font-mono text-xs overflow-x-auto relative group">
              <Button
                size="icon"
                variant="ghost"
                className="absolute right-2 top-2 h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={handleCopy}
              >
                {copied ? <Check className="h-3 w-3 text-green-500" /> : <Copy className="h-3 w-3" />}
              </Button>
              <pre className="text-foreground/80">{codeString}</pre>
            </div>
          </CollapsibleContent>
        </Collapsible>
      </Card>
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
      <div className="w-full flex justify-center py-4">
        <Badge
          variant={isError ? "destructive" : "secondary"}
          className="px-4 py-1.5 text-xs font-medium bg-muted/50 border border-border/50 backdrop-blur-sm"
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

  const roleLabel = isUser ? "You" : "Surf Agent";

  return (
    <div
      className={cn(
        "flex w-full mb-6",
        isUser ? "justify-end" : "justify-start",
        className
      )}
    >
      <div className={cn(
        "flex flex-col max-w-[85%]",
        isUser ? "items-end" : "items-start"
      )}>

        {!isUser && (
          <div className="flex items-center gap-2 mb-2 ml-1">
            <div className="bg-primary/10 p-1 rounded-sm">
              <Bot className="h-3.5 w-3.5 text-primary" />
            </div>
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              {roleLabel}
            </span>
          </div>
        )}

        <div
          className={cn(
            "rounded-2xl px-5 py-3.5 shadow-sm text-sm leading-relaxed",
            isUser
              ? "bg-primary text-primary-foreground rounded-tr-sm"
              : "bg-card border border-border/60 rounded-tl-sm"
          )}
        >
          {isUser ? (
            <div className="whitespace-pre-wrap">{message.content}</div>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none break-words">
              <MemoizedReactMarkdown>
                {message.content}
              </MemoizedReactMarkdown>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
