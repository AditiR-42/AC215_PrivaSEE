'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import ChatInput from '@/components/chat/ChatInput';
import ChatHistory from '@/components/chat/ChatHistory';
import ChatHistorySidebar from '@/components/chat/ChatHistorySidebar';
import ChatMessage from '@/components/chat/ChatMessage';
import DataService from "../../services/DataService";
import { uuid } from "../../services/Common";
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { ThreeDots } from 'react-loader-spinner'; // Add the loader component
import styles from "./styles.module.css";

export default function ChatPage() {
    const searchParams = useSearchParams(); // Use useSearchParams hook
    const chat_id = searchParams.get('id'); // Access `id` safely
    const model = searchParams.get('model') || 'llm'; // Access `model` safely
    const router = useRouter();

    // Component States
    const [chatId, setChatId] = useState(chat_id);
    const [hasActiveChat, setHasActiveChat] = useState(false);
    const [chat, setChat] = useState(null);
    const [refreshKey, setRefreshKey] = useState(0);
    const [isTyping, setIsTyping] = useState(false);
    const [selectedModel, setSelectedModel] = useState(model);
    const [isLoading, setIsLoading] = useState(false); // Add loading state

    const fetchChat = async (id) => {
        try {
            setIsLoading(true); // Start loading
            setChat(null);
            const response = await DataService.GetChat(model, id);
            setChat(response.data);
        } catch (error) {
            console.error('Error fetching chat:', error);
            setChat(null);
        } finally {
            setIsLoading(false); // Stop loading
        }
    };

    // Lifecycle hooks
    useEffect(() => {
        if (chat_id) {
            fetchChat(chat_id);
            setHasActiveChat(true);
        } else {
            setChat(null);
            setHasActiveChat(false);
        }
    }, [chat_id]);

    useEffect(() => {
        setSelectedModel(model);
    }, [model]);

    const tempChatMessage = (message) => {
        const tempMessage = {
            message_id: uuid(),
            role: 'user',
            content: message.content, // Use `content` instead of `text`
            image: message.image || null,
        };
        const updatedChat = chat
            ? { ...chat, messages: [...chat.messages, tempMessage] }
            : { messages: [tempMessage] };
        return updatedChat;
    };

    // Handlers
    const newChat = (message) => {
        const startChat = async (message) => {
            try {
                setIsTyping(true);
                setIsLoading(true); // Start loading
                setChat(tempChatMessage(message)); // Temporarily show user input
    
                console.log('Sending message to backend:', message.content);
    
                // Fetch recommendation from the backend
                const recommendation = await DataService.GetRecommendation(message.content);
                console.log('Backend Response:', recommendation);
    
                // Display the recommendation in an alert
                alert(`Recommendation: ${recommendation.recommendation.Description || "No description provided"}`);
    
                toast.success("Recommendation received!");
    
                setIsTyping(false);
                setChat((prevChat) => ({
                    ...prevChat,
                    messages: [
                        ...(prevChat?.messages || []),
                        { role: 'assistant', content: recommendation.recommendation.Description },
                    ],
                }));
            } catch (error) {
                console.error('Error during chat:', error);
                alert('Something went wrong. Please try again.'); // Show error in alert
                toast.error('Something went wrong. Please try again.');
                setIsTyping(false);
            } finally {
                setIsLoading(false); // Stop loading
            }
        };
    
        startChat(message);
    };

    const appendChat = (message) => {
        const continueChat = async (id, message) => {
            try {
                setIsTyping(true);
                setIsLoading(true); // Start loading
                setChat(tempChatMessage(message));

                const response = await DataService.ContinueChatWithLLM(model, id, message);
                console.log('Response:', response.data);

                setIsTyping(false);
                setChat(response.data);
                forceRefresh();
            } catch (error) {
                console.error('Error appending chat:', error);
                setIsTyping(false);
                toast.error('Failed to continue the chat. Please try again.');
                setChat((prevChat) => ({
                    ...prevChat,
                    messages: [
                        ...(prevChat?.messages || []),
                        { role: 'assistant', content: 'Failed to continue the chat. Please try again.' },
                    ],
                }));
            } finally {
                setIsLoading(false); // Stop loading
            }
        };

        continueChat(chatId, message);
    };

    const forceRefresh = () => setRefreshKey((prevKey) => prevKey + 1);

    const handleModelChange = (newValue) => {
        setSelectedModel(newValue);
        const path = `/chat?model=${newValue}${chat_id ? `&id=${chat_id}` : ''}`;
        router.push(path);
    };

    return (
        <div className={styles.container}>
            {/* Loading overlay */}
            {isLoading && (
                <div className={styles.loadingOverlay}>
                    <ThreeDots color="#007bff" height={80} width={80} />
                </div>
            )}

            {!hasActiveChat && (
                <section className={styles.hero}>
                    <div className={styles.heroContent}>
                        <h1>Get App Recommendations 🌟</h1>
                        <ChatInput
                            onSendMessage={newChat}
                            className={styles.heroChatInputContainer}
                            selectedModel={selectedModel}
                            onModelChange={handleModelChange}
                        />
                    </div>
                </section>
            )}

            {!hasActiveChat && <ChatHistory model={model} />}

            {hasActiveChat && (
                <>
                    <div className={styles.chatHeader}></div>
                    <div className={styles.chatInterface}>
                        <ChatHistorySidebar chat_id={chat_id} model={model} />
                        <div className={styles.mainContent}>
                            <ChatMessage chat={chat} key={refreshKey} isTyping={isTyping} model={model} />
                            <ChatInput
                                onSendMessage={appendChat}
                                chat={chat}
                                selectedModel={selectedModel}
                                onModelChange={handleModelChange}
                                disableModelSelect={true}
                            />
                        </div>
                    </div>
                </>
            )}

            {/* Toast Container */}
            <ToastContainer position="top-right" autoClose={3000} />
        </div>
    );
}