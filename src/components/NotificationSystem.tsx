import React, { useState, useEffect } from 'react';

interface Notification {
  id: number;
  message: string;
}

const NotificationSystem = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  useEffect(() => {
    // Simulate fetching notifications from an API
    const fetchNotifications = () => {
      setTimeout(() => {
        setNotifications([
          { id: 1, message: 'New teammate added!' },
          { id: 2, message: 'Subscription updated successfully.' },
          { id: 3, message: 'Your analysis results are ready.' },
        ]);
      }, 1000);
    };

    fetchNotifications();
  }, []);

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h2>Notifications</h2>
      <ul style={{ listStyleType: 'none', padding: 0 }}>
        {notifications.map((notification) => (
          <li
            key={notification.id}
            style={{
              background: '#f9f9f9',
              margin: '10px 0',
              padding: '10px',
              borderRadius: '5px',
              boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
            }}
          >
            {notification.message}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default NotificationSystem;