"use client";

import React, { useState } from "react";
import {
  ChatMessage as ChatMessageType,
  ActionChatMessage,
} from "@/types/chat";
import { cn } from "@/lib/utils";
import {
  Terminal,
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
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { Badge } from "../ui/badge";
import { Markdown as MemoizedReactMarkdown } from "@/components/markdown";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";

// Helper to parse pyautogui actions into human-readable text
const parseAction = (code: string) => {
  if (!code) return { title: "Executing Action", icon: Cpu };

  if (code.includes("write") || code.includes("type")) {
    const match = code.match(/write\(['"](.+?)['"]\)/);
    return {
      title: match ? `Typing "${match[1].slice(0, 30)}${match[1].length > 30 ? '...' : ''}"` : "Typing text...",
      icon: Keyboard
    };
  }
  if (code.includes("click")) {
    return { title: "Clicking element", icon: MousePointer2 };
  }
  if (code.includes("launch")) {
    const match = code.match(/launch\(['"](.+?)['"]\)/);
    return {
      title: match ? `Opening ${match[1]}` : "Opening application...",
      icon: AppWindow
    };
  }
  if (code.includes("scroll")) return { title: "Scrolling...", icon: MousePointer2 };
  if (code.includes("wait")) return { title: "Waiting...", icon: Clock };

  return { title: "Running command", icon: Terminal };
};

interface ActionMessageProps {
  message: ActionChatMessage;
  className?: string;
}

function ActionMessage({ message, className }: ActionMessageProps) {
  const { action, status } = message;
  const [isOpen, setIsOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const codeString = typeof action === 'string'
    ? action
    : (action as any)?.code || JSON.stringify(action, null, 2);

  const { title, icon: Icon } = parseAction(codeString);

  const handleCopy = () => {
    navigator.clipboard.writeText(codeString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isPending = status === "pending";
  const isCompleted = status === "completed";
  const isFailed = status === "failed";

  return (
    <div className={cn("w-full", className)}>
      <div className={cn(
        "bg-white border rounded-xl overflow-hidden transition-all",
        isPending && "border-amber-200 bg-amber-50/30",
        isCompleted && "border-emerald-200 bg-emerald-50/30",
        isFailed && "border-red-200 bg-red-50/30",
        !isPending && !isCompleted && !isFailed && "border-slate-200"
      )}>
        {/* Action Header */}
        <div className="flex items-center justify-between px-3 py-2.5">
          <div className="flex items-center gap-3">
            <div className={cn(
              "w-8 h-8 rounded-lg flex items-center justify-center",
              isPending && "bg-amber-100 text-amber-600",
              isCompleted && "bg-emerald-100 text-emerald-600",
              isFailed && "bg-red-100 text-red-600",
              !isPending && !isCompleted && !isFailed && "bg-slate-100 text-slate-600"
            )}>
              <Icon className="w-4 h-4" />
            </div>
            
            <div className="flex flex-col">
              <span className="text-sm font-medium text-slate-900">{title}</span>
              {isPending && (
                <span className="text-xs text-amber-600 flex items-center gap-1">
                  <Clock className="w-3 h-3 animate-spin" />
                  Processing...
                </span>
              )}
              {isCompleted && (
                <span className="text-xs text-emerald-600 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" />
                  Completed
                </span>
              )}
              {isFailed && (
                <span className="text-xs text-red-600 flex items-center gap-1">
                  <XCircle className="w-3 h-3" />
                  Failed
                </span>
              )}
            </div>
          </div>

          <Collapsible open={isOpen} onOpenChange={setIsOpen}>
            <CollapsibleTrigger asChild>
              <Button 
                variant="ghost" 
                size="sm" 
                className="h-7 w-7 p-0 text-slate-400 hover:text-slate-600 hover:bg-slate-100"
              >
                {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </Button>
            </CollapsibleTrigger>
          </Collapsible>
        </div>

        {/* Code Expandable */}
        <Collapsible open={isOpen}>
          <CollapsibleContent>
            <div className="px-3 pb-3">
              <div className="relative bg-slate-900 rounded-lg p-3 group">
                <Button
                  size="icon"
                  variant="ghost"
                  className="absolute right-2 top-2 h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity text-slate-400 hover:text-white hover:bg-slate-700"
                  onClick={handleCopy}
                >
                  {copied ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                </Button>
                <pre className="text-xs text-slate-300 font-mono overflow-x-auto whitespace-pre-wrap">
                  {codeString}
                </pre>
              </div>
            </div>
          </CollapsibleContent>
        </Collapsible>
      </div>
    </div>
  );
}

interface ChatMessageProps {
  message: ChatMessageType;
  className?: string;
}

export function ChatMessage({ message, className }: ChatMessageProps) {
  const role = message.role;
  const isUser = role === "user";
  const isAssistant = role === "assistant";
  const isAction = role === "action";
  const isSystem = role === "system";
  const isError = "isError" in message && message.isError;

  // System messages
  if (isSystem) {
    return (
      <div className={cn("flex justify-center py-3", className)}>
        <Badge
          variant={isError ? "error" : "muted"}
          className={cn(
            "px-3 py-1 text-xs font-medium",
            isError ? "bg-red-100 text-red-700 border-red-200" : "bg-slate-100 text-slate-600 border-slate-200"
          )}
        >
          {message.content}
        </Badge>
      </div>
    );
  }

  // Action messages
  if (isAction) {
    return <ActionMessage message={message as ActionChatMessage} className={className} />;
  }

  // User messages
  if (isUser) {
    return (
      <div className={cn("flex justify-end", className)}>
        <div className="flex items-start gap-2 max-w-[85%]">
          <div className="bg-blue-600 text-white px-4 py-2.5 rounded-2xl rounded-br-md shadow-sm">
            <p className="text-sm">{message.content}</p>
          </div>
          <div className="flex-shrink-0 w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center">
            <User className="w-4 h-4 text-blue-600" />
          </div>
        </div>
      </div>
    );
  }

  // Assistant messages
  if (isAssistant) {
    return (
      <div className={cn("flex justify-start", className)}>
        <div className="flex items-start gap-2 max-w-[85%]">
          <div className="flex-shrink-0 w-7 h-7 rounded-full bg-slate-100 flex items-center justify-center">
            <Bot className="w-4 h-4 text-slate-600" />
          </div>
          <div className="bg-white border border-slate-200 px-4 py-2.5 rounded-2xl rounded-bl-md shadow-sm">
            <div className="text-sm text-slate-700 prose prose-sm prose-slate max-w-none">
              <MemoizedReactMarkdown>{message.content}</MemoizedReactMarkdown>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return null;
}
