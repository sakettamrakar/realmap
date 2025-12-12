import { useState, useRef, useEffect } from "react";
import { aiClient } from "../../api/aiApi";

interface ChatProject {
    id: number;
    name: string | null;
    location: string | null;
    score: number;
}

interface ChatResponse {
    query: string;
    answer: string;
    projects: ChatProject[];
    success: boolean;
}

interface Message {
    type: "user" | "assistant";
    content: string;
    projects?: ChatProject[];
    timestamp: Date;
}

interface Props {
    onSelectProject?: (projectId: number) => void;
}

export const AIChatAssistant = ({ onSelectProject }: Props) => {
    const [isOpen, setIsOpen] = useState(false);
    const [query, setQuery] = useState("");
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    // Scroll to bottom when new messages arrive
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    // Focus input when chat opens
    useEffect(() => {
        if (isOpen) {
            setTimeout(() => inputRef.current?.focus(), 100);
        }
    }, [isOpen]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim() || isLoading) return;

        const userMessage: Message = {
            type: "user",
            content: query,
            timestamp: new Date(),
        };
        setMessages(prev => [...prev, userMessage]);
        setQuery("");
        setIsLoading(true);
        setError(null);

        try {
            const { data } = await aiClient.post<ChatResponse>("/api/v1/chat/search", {
                query: query.trim(),
                limit: 5,
            });

            const assistantMessage: Message = {
                type: "assistant",
                content: data.answer,
                projects: data.projects,
                timestamp: new Date(),
            };
            setMessages(prev => [...prev, assistantMessage]);
        } catch (err) {
            setError("Unable to process your request. Please try again.");
            console.error("Chat search error:", err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleProjectClick = (projectId: number) => {
        onSelectProject?.(projectId);
        setIsOpen(false);
    };

    const exampleQueries = [
        "3BHK apartments under 80 lakhs",
        "Projects with swimming pool in Raipur",
        "Ready to move flats with gym",
        "Premium projects with high scores",
    ];

    return (
        <>
            {/* Floating Chat Button */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="fixed bottom-6 right-6 w-14 h-14 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-full shadow-lg hover:shadow-xl transition-all duration-300 flex items-center justify-center z-50 group"
                aria-label="AI Chat Assistant"
            >
                {isOpen ? (
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                ) : (
                    <svg className="w-6 h-6 text-white group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                )}
                {/* Pulse effect when closed */}
                {!isOpen && (
                    <span className="absolute -top-1 -right-1 w-4 h-4 bg-green-400 rounded-full animate-pulse" />
                )}
            </button>

            {/* Chat Panel */}
            {isOpen && (
                <div className="fixed bottom-24 right-6 w-96 max-h-[600px] bg-white rounded-2xl shadow-2xl border border-gray-200 flex flex-col z-50 overflow-hidden animate-slideUp">
                    {/* Header */}
                    <div className="bg-gradient-to-r from-indigo-600 to-purple-600 px-4 py-3 flex items-center gap-3">
                        <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                            <span className="text-xl">🤖</span>
                        </div>
                        <div className="flex-1">
                            <h3 className="text-white font-semibold">AI Assistant</h3>
                            <p className="text-white/70 text-xs">Ask me about properties</p>
                        </div>
                        <button
                            onClick={() => setIsOpen(false)}
                            className="text-white/70 hover:text-white transition-colors"
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>

                    {/* Messages Area */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-[300px] max-h-[400px] bg-gray-50">
                        {messages.length === 0 ? (
                            <div className="text-center py-8">
                                <div className="text-4xl mb-3">💬</div>
                                <p className="text-gray-600 font-medium mb-2">How can I help you today?</p>
                                <p className="text-gray-400 text-sm mb-4">Try asking:</p>
                                <div className="space-y-2">
                                    {exampleQueries.map((q, i) => (
                                        <button
                                            key={i}
                                            onClick={() => setQuery(q)}
                                            className="block w-full text-left px-3 py-2 bg-white rounded-lg text-sm text-indigo-600 hover:bg-indigo-50 transition-colors border border-indigo-100"
                                        >
                                            "{q}"
                                        </button>
                                    ))}
                                </div>
                            </div>
                        ) : (
                            messages.map((msg, i) => (
                                <div key={i} className={`flex ${msg.type === "user" ? "justify-end" : "justify-start"}`}>
                                    <div className={`max-w-[85%] ${msg.type === "user"
                                        ? "bg-indigo-600 text-white rounded-2xl rounded-br-md"
                                        : "bg-white text-gray-800 rounded-2xl rounded-bl-md shadow-sm border border-gray-100"
                                        } px-4 py-3`}>
                                        <p className="text-sm">{msg.content}</p>

                                        {/* Project Results */}
                                        {msg.projects && msg.projects.length > 0 && (
                                            <div className="mt-3 pt-3 border-t border-gray-200/50 space-y-2">
                                                <p className="text-xs font-medium text-gray-500 mb-2">
                                                    Found {msg.projects.length} matching projects:
                                                </p>
                                                {msg.projects.map((project) => (
                                                    <button
                                                        key={project.id}
                                                        onClick={() => handleProjectClick(project.id)}
                                                        className="w-full text-left px-3 py-2 bg-indigo-50 hover:bg-indigo-100 rounded-lg transition-colors group"
                                                    >
                                                        <div className="flex justify-between items-start">
                                                            <div className="flex-1 min-w-0">
                                                                <p className="text-sm font-medium text-indigo-900 truncate group-hover:text-indigo-700">
                                                                    {project.name || "Unknown Project"}
                                                                </p>
                                                                <p className="text-xs text-gray-500 truncate">
                                                                    {project.location || "Location not specified"}
                                                                </p>
                                                            </div>
                                                            <span className="ml-2 px-2 py-0.5 text-xs font-bold bg-indigo-600 text-white rounded-full">
                                                                {project.score.toFixed(0)}
                                                            </span>
                                                        </div>
                                                    </button>
                                                ))}
                                            </div>
                                        )}

                                        <p className="text-[10px] mt-2 opacity-50">
                                            {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                        </p>
                                    </div>
                                </div>
                            ))
                        )}

                        {/* Loading Indicator */}
                        {isLoading && (
                            <div className="flex justify-start">
                                <div className="bg-white rounded-2xl rounded-bl-md px-4 py-3 shadow-sm border border-gray-100">
                                    <div className="flex gap-1">
                                        <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                                        <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                                        <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Error */}
                        {error && (
                            <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm text-red-600">
                                {error}
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input Area */}
                    <form onSubmit={handleSubmit} className="p-3 bg-white border-t border-gray-100">
                        <div className="flex gap-2">
                            <input
                                ref={inputRef}
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="Ask about properties..."
                                className="flex-1 px-4 py-2 bg-gray-100 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all"
                                disabled={isLoading}
                            />
                            <button
                                type="submit"
                                disabled={isLoading || !query.trim()}
                                className="w-10 h-10 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-300 rounded-full flex items-center justify-center transition-colors"
                            >
                                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                                </svg>
                            </button>
                        </div>
                    </form>
                </div>
            )}

            {/* CSS Animation */}
            <style>{`
                @keyframes slideUp {
                    from {
                        opacity: 0;
                        transform: translateY(20px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }
                .animate-slideUp {
                    animation: slideUp 0.3s ease-out;
                }
            `}</style>
        </>
    );
};
