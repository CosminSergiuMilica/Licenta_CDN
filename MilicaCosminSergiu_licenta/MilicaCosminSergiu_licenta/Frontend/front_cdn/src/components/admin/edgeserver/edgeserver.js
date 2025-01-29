import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import './blockip.css'
function EdgeServers() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const storedIP = sessionStorage.getItem('ec2Ip');

  const handleRowClick = (instance_id) => {
    navigate(`/admin/edgeservers/${instance_id}`);
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(`http://${storedIP}/api/cdn/edgeserver_service`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        setData(response.data);
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
  }, [navigate, storedIP]);

  if (loading) {
    return (
      <div className="loading-message">
        <div className="spinner"></div>
        <div className="loading-text">Se încarcă...</div>
      </div>
    );
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!data || data.length === 0) {
    return <div>No data available</div>;
  }

  const getStatusImage = (status) => {
    switch (status) {
      case 'SLOW':
        return '/down.png';
      case 'OFF':
        return '/off.png';
      case 'CRASH':
        return '/crash.png';
      case 'ON':
        return '/on.png';
      default:
        return null;
    }
  };

  return (
    <div className="origin-service-container">
      <h1 className="h1-site">EdgeServers</h1>
      <table className="server-table">
        <thead>
          <tr>
            <th>Instance ID</th>
            <th>Region</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {data.map((d, index) => (
            <tr key={index} onClick={() => handleRowClick(d.instance_id)} className="server-row">
              <td>{d.instance_id}</td>
              <td>{d.region}</td>
              <td>
                <img src={getStatusImage(d.status)} alt={d.status} className="status-image" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default EdgeServers;
