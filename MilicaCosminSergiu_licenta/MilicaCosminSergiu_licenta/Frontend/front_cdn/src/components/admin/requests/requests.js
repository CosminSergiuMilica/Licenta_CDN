import React, { useEffect, useState, useRef } from 'react';
import './requests.css';
import { useParams, useNavigate } from 'react-router-dom';

function AdminRequests() {
  const [messages, setMessages] = useState([]);
  const ws = useRef(null);
  const reconnectInterval = useRef(null);
  const navigate = useNavigate(); 
  const storedIP = sessionStorage.getItem('ec2Ip');
  useEffect(() => {
      const userRole = localStorage.getItem('userRole');
      if (userRole !== 'admin') {
        navigate('/'); 
      }
  }, [navigate]);

  useEffect(() => {
    const connectWebSocket = () => {
      ws.current = new WebSocket(`ws://${storedIP}:8221/sqs-messages`);

      ws.current.onopen = () => {
        console.log('Connected to WebSocket');
        if (reconnectInterval.current) {
          clearInterval(reconnectInterval.current);
          reconnectInterval.current = null;
        }
      };

      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setMessages(prevMessages => [...prevMessages, ...data]);
        // setTotalRequests(prevMessages => prevMessages.length + data.length);
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket Error:', error);
      };

      ws.current.onclose = (event) => {
        console.log('WebSocket connection closed', event);
        if (!event.wasClean) {
          console.log('Attempting to reconnect in 5 seconds...');
          if (!reconnectInterval.current) {
            reconnectInterval.current = setInterval(() => {
              connectWebSocket();
            }, 5000);
          }
        }
      };
    };

    connectWebSocket();

    return () => {
      if (ws.current) {
        ws.current.close();
      }
      if (reconnectInterval.current) {
        clearInterval(reconnectInterval.current);
      }
    };
  }, []);

const isMethodRed = (resource) => {
    const methods = ['POST', 'DELETE', 'PATCH', 'PUT'];
    return methods.some(method => resource.includes(method));
  };

  return (
    <div className="App">
      <h1>CDN Traffic Monitor</h1>
      <table>
        <thead>
          <tr>
            <th>Client Location</th>
            <th>Edge Server</th>
            <th>Domain</th>
            <th>Resource</th>
            <th>State</th>
            <th>Time</th>
          </tr>
        </thead>
        <tbody>
          {messages.map((message) => (
            <tr
              key={message.message_id}
              className={`${message.state === 'Miss' ? 'miss' : 'hit'} ${isMethodRed(message.state) ? 'method-red' : ''}`}
            >
              <td>{message.client_ip}</td>
              <td>{message.edge_server}</td>
              <td>{message.domain}</td>
              <td>{message.resource}</td>
              <td>{message.state}</td>
              <td>{new Date(message.time).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default AdminRequests;