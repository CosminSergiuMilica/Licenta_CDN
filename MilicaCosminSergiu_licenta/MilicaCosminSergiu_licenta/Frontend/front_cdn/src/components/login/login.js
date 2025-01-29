import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Navigate, Link } from 'react-router-dom';

import './login.css'

function Login() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [message, setMessage] = useState('');
    const [redirectToHome, setRedirectToHome] = useState(false);
    const storedIP = sessionStorage.getItem('ec2Ip');
    useEffect(() => {
        const token = localStorage.getItem('token');

        if (token) {
            setRedirectToHome(true);
        }
    }, []);

    const handleLogin = async (e) => {
        e.preventDefault();

        try {
            const response = await axios.post(`http://${storedIP}/api/cdn/login`, {
                username: username,
                password: password,
            });

            if (response.status === 200) {
                const token = response.data.Authorization;

                const tokenWithoutBearer = token.replace('Bearer ', '');

                localStorage.setItem('userRole', response.data.user_role);
                localStorage.setItem('userId', response.data.user_id);
                localStorage.setItem('token', tokenWithoutBearer);

                setMessage('Autentificare cu succes');
                setRedirectToHome(true);
            } else {
                const errorData = response.data;
                setMessage(errorData.message || 'Authentication failed');
            }
        } catch (error) {
            console.error('Error during login:', error.response.data);
            setMessage(error.response.data.detail || 'Error during login');
        }
    };


    if (redirectToHome) {
        return <Navigate to="/" replace />;
    }

    return (
        <div className="cont">
            <div className="text">
                <h1 className="main-header">Login to your account</h1>
            </div>

            <form onSubmit={handleLogin}>
                <div className="content">
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <label>
                            Username
                        </label>
                        <input
                            type="text"
                            placeholder="Username"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                        />
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <label>
                            Password
                        </label>
                        <input
                            type="password"
                            placeholder="Password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                    </div>
                    
                    <div className="btn">
                        <button type="submit">Submit</button>
                    </div>
                    <div style={{ textAlign: 'center', gap: '4px' }}>
                        <Link to="/signup" className="links" style={{ fontSize: '16px' }}>Don't have an account?</Link>
                    </div>
                    <div className="message">{message}</div>
                </div>
            </form>
        </div>
    );
};

export default Login;