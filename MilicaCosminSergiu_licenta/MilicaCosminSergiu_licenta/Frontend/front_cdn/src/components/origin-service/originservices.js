import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

import './originservices.css'; 

function OriginServiceComponent() {
  const [originServiceData, setOriginServiceData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate(); 
  const storedIP = sessionStorage.getItem('ec2Ip');
  const handleSquareClick = (domain) => {

    navigate(`/my-site/${domain}`); 
  };

  useEffect(() => {
      const userRole = localStorage.getItem('userRole');
      if (userRole !== 'user') {
        navigate('/'); 
      }
  }, [navigate]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem('token');
        const userId = localStorage.getItem('userId');
        const response = await axios.get(`http://${storedIP}/api/cdn/origin_service?owner=${userId}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        setOriginServiceData(response.data);
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
    return <div className="loading-message">
      <div className="spinner"></div>
      <div className="loading-text">Se încarcă...</div>
    </div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!originServiceData || originServiceData.origins.length === 0) {
    return <div>No data available</div>;
  }

  return (
    <div className="origin-service-container"> 
      <h1 className='h1-site'>My Sites</h1>
      <div className="domain-list">
        {originServiceData.origins.map((origin, index) => (
          <div key={index} className="domain-item">
            <div className="domain-box"> 
              <div onClick={() => handleSquareClick(origin.domain)} className="domain-link"> 
                <h2>{origin.domain}</h2>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default OriginServiceComponent;
