import React, { useState , useEffect } from 'react';
import axios from 'axios';
import { Navigate } from 'react-router-dom';
import './signup.css';

function Signup() {
     const [formData, setFormData] = useState({
        username: '',
        password: '',
        first_name: '',
        last_name: '',
        phone: '',
        email: '',
        country: ''
    });
    const [redirectToHome, setRedirectToHome] = useState(false);
    const [message, setMessage] = useState('');
    const storedIP = sessionStorage.getItem('ec2Ip');
    
    useEffect(() => {
        const token = localStorage.getItem('token');

        if (token) {
           
            setRedirectToHome(true);
        }
    }, []);

    const handleChange = (e) => {
        const { id, value } = e.target;
        setFormData((previousFormData) => ({ ...previousFormData, [id]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if(!formData.username || !formData.password || !formData.email){
            setMessage('Ati omis date importante pentru a va crea un cont(username, password, email)!!!')
            return;
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(formData.email)) {
            setMessage("Invalid email format.");
            return;
        }

        if (formData.phone.length !== 10) {
        setMessage("Numarul de telefon trebuie sa aibe 10 cifre!");
        return;
        }

        try {
            const response = await axios.post(`http://${storedIP}/api/cdn/signup`, formData);

            if (response.status === 201) {
                console.log('Inregistrare utilizator reusita:', response.data);
                const token = response.data.Authorization;

                const tokenWithoutBearer = token.replace('Bearer ', '');
                localStorage.setItem('token', tokenWithoutBearer);
                localStorage.setItem('userRole', response.data.user_role);
                localStorage.setItem('userId',response.data.id_user );
                
                setRedirectToHome(true);
            } else if (response.status === 400) {
                console.log('Inregistrarea utilizatorului a esuat:', response.data);
                setMessage(response.data.message || 'Authentication failed');
            }
            else {
                console.log('Inregistrarea utilizatorului a esuat:', response.data);
                setMessage(response.data.message || 'Authentication failed');
            }

        } catch (error) {
            console.error('Eroare în timpul inregistrarii utilizatorului:', error);
            if (error.response && error.response.data) {
                setMessage( error.response.data.message);
            }
        }
    };
    if (redirectToHome) {
        return <Navigate to="/" replace />;
    }

    return (
        <div className="contr">
            <div className="text">
                <h1 className="main-header">Register</h1>
            </div>
            <form onSubmit={handleSubmit}>
                <div className="message" style={{ color: 'red', fontSize: '1.5rem', margin: '1rem 0' }}>{message}</div>
                <div className="content">
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <label htmlFor="username">username</label>
                        <input type="text" id="username" placeholder="username" onChange={handleChange} />
                    </div>


                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <label htmlFor="password">password</label>
                        <input type="password" id="password" placeholder="password" onChange={handleChange} />
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <label htmlFor="first_name">first name</label>
                        <input type="text" id="first_name" placeholder="first name" onChange={handleChange} />
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <label htmlFor="last_name">last name</label>
                        <input type="text" id="last_name" placeholder="last name" onChange={handleChange} />
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <label htmlFor="phone">phone number</label>
                        <input type="tel" id="phone" placeholder="phone number" onChange={handleChange} />
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <label htmlFor="email">email</label>
                        <input type="email" id="email" placeholder="email" onChange={handleChange} />
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <label htmlFor="country">country</label>
                        <input type="text" id="country" placeholder='country' onChange={handleChange} />
                    </div>

                    <div className="btn">
                        <button type="submit">Register</button>
                    </div>
                    
                </div>
                
            </form>
        </div>
    );
}

export default Signup;