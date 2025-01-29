import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './profile.css';
function UserDataComponent() {
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate(); 
  const storedIP = sessionStorage.getItem('ec2Ip');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem('token');
        const user_id = localStorage.getItem('userId');
        const response = await axios.get(`http://${storedIP}/api/cdn/user/${user_id}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        setUserData(response.data);
        setLoading(false);
      } catch (error) {
        if (error.response && error.response.status === 401) {
          
          navigate('/logout');
        } else {
          setError(error.message);
          setLoading(false);
        }
      }
    };

    fetchData();
  }, []); 

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!userData) {
    return <div>No user data available</div>;
  }

  return (
     <div className="hacker-profile">
        <h2>Profile</h2>
      <div className="profile-info">
        <p><span>Username:</span>{userData.username}</p>
        <p><span>Last Name:</span>{userData.last_name}</p>
        <p><span>First Name:</span>{userData.first_name}</p>
        <p><span>Phone:</span>{userData.phone}</p>
        <p><span>Email:</span>{userData.email}</p>
        <p><span>Country:</span>{userData.country}</p>
      </div>
      <div className="ascii-art">
        {/* Insert your ASCII art here */}
      </div>
    </div>
  );
}

export default UserDataComponent;
