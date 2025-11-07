import React, { useState } from 'react';

interface Message {
  sender: string;
  text: string;
}

const TeammateChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');

  const handleSendMessage = () => {
    if (input.trim()) {
      setMessages([...messages, { sender: 'You', text: input }]);
      setInput('');
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h2>Teammate Chat</h2>
      <div
        style={{
          border: '1px solid #ccc',
          borderRadius: '10px',
          padding: '10px',
          height: '300px',
          overflowY: 'scroll',
          marginBottom: '10px',
        }}
      >
        {messages.map((message, index) => (
          <div key={index} style={{ marginBottom: '5px' }}>
            <strong>{message.sender}:</strong> {message.text}
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', gap: '10px' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          style={{ flex: 1, padding: '10px', borderRadius: '5px', border: '1px solid #ccc' }}
        />
        <button
          onClick={handleSendMessage}
          style={{ padding: '10px 20px', borderRadius: '5px', backgroundColor: '#007BFF', color: 'white', border: 'none' }}
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default TeammateChat;