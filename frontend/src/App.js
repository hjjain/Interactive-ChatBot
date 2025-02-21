import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import { motion } from "framer-motion";

const ChatApp = () => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [currentImage, setCurrentImage] = useState(null);
    const chatContainerRef = useRef(null);
    const fileInputRef = useRef(null);

    useEffect(() => {
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
    }, [messages]);

    const handleFileUpload = async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        // Only handle images for this version
        if (!file.type.startsWith('image/')) {
            alert('Please upload an image file.');
            return;
        }

        setCurrentImage(file);
        
        // Create a message showing the uploaded image
        const imageUrl = URL.createObjectURL(file);
        const userMessage = { 
            role: "user", 
            content: "Uploaded an image",
            image: imageUrl,
            fileName: file.name
        };
        setMessages(prev => [...prev, userMessage]);

        // Clear the file input
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }

        // Add system message prompting for instructions
        const systemPrompt = { 
            role: "assistant", 
            content: "I've received your image. What would you like me to do with it? I can:\n- Analyze its contents\n- Extract any text\n- Answer questions about it\n- Describe specific aspects"
        };
        setMessages(prev => [...prev, systemPrompt]);
    };

    const sendMessage = async () => {
        if (!input.trim()) return;

        const userMessage = { role: "user", content: input };
        setMessages((prev) => [...prev, userMessage]);
        setInput("");
        setLoading(true);

        try {
            const formData = new FormData();
            formData.append('message', input);
            
            // If there's a current image context, include it
            if (currentImage) {
                formData.append('image', currentImage);
            }

            // Add conversation history
            formData.append('conversation_history', JSON.stringify(messages));

            const response = await axios.post("http://localhost:8000/chat", formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });

            const botMessage = { role: "assistant", content: response.data.reply };
            setMessages((prev) => [...prev, botMessage]);
        } catch (error) {
            console.error("Error fetching response:", error);
            setMessages((prev) => [
                ...prev,
                { role: "assistant", content: "Oops! Something went wrong. Please try again." },
            ]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex items-center justify-center h-screen bg-gray-900">
            <motion.div 
                initial={{ opacity: 0, y: 20 }} 
                animate={{ opacity: 1, y: 0 }}
                className="w-full max-w-2xl h-[80vh] bg-gray-800 rounded-2xl shadow-xl p-6 flex flex-col relative"
            >
                <h2 className="text-white text-2xl font-bold text-center mb-4">AI Chatbot</h2>
                <div ref={chatContainerRef} className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-hide pb-20">
                    {messages.map((msg, index) => (
                        <motion.div 
                            key={index} 
                            initial={{ opacity: 0, x: msg.role === "user" ? 50 : -50 }}
                            animate={{ opacity: 1, x: 0 }}
                            className={`p-3 rounded-lg w-fit max-w-[75%] ${msg.role === "user" ? "bg-blue-500 text-white self-end ml-auto" : "bg-gray-700 text-gray-200"}`}
                        >
                            {msg.image && (
                                <div className="mb-2">
                                    <img 
                                        src={msg.image} 
                                        alt={msg.fileName}
                                        className="max-w-full rounded-lg"
                                        style={{ maxHeight: '200px' }}
                                    />
                                    <div className="text-sm opacity-75 mt-1">
                                        {msg.fileName}
                                    </div>
                                </div>
                            )}
                            {msg.content}
                        </motion.div>
                    ))}
                    {loading && (
                        <motion.div 
                            initial={{ opacity: 0 }} 
                            animate={{ opacity: 1 }}
                            className="p-3 rounded-lg bg-gray-700 text-gray-200"
                        >
                            Processing...
                        </motion.div>
                    )}
                </div>
                <div className="relative w-full p-4 bg-gray-900 rounded-b-2xl flex items-center mt-2">
                    <input
                        type="text"
                        className="flex-1 p-3 bg-gray-700 text-white rounded-lg focus:outline-none"
                        placeholder={currentImage ? "What would you like to know about the image?" : "Type a message..."}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                    />
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*"
                        onChange={handleFileUpload}
                        className="hidden"
                    />
                    <button 
                        onClick={() => {
                            setCurrentImage(null);
                            fileInputRef.current?.click();
                        }}
                        className="ml-3 bg-gray-600 hover:bg-gray-700 text-white p-3 rounded-lg"
                        disabled={loading}
                    >
                        📷
                    </button>
                    <button 
                        onClick={sendMessage} 
                        className="ml-3 bg-blue-600 hover:bg-blue-700 text-white p-3 rounded-lg"
                        disabled={loading}
                    >
                        {loading ? "Sending..." : "Send"}
                    </button>
                </div>
            </motion.div>
        </div>
    );
};

export default ChatApp;