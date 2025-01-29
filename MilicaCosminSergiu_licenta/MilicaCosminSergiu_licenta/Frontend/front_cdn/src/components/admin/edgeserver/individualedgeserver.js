import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams, useNavigate } from 'react-router-dom';
import './individualedgeserver.css';

function IndividualEdgeServer() {

  const [Data, setData] = useState(null);
  const [Metrics, setMetrics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { instance_id } = useParams();
  const navigate = useNavigate();
  const [updateData, setUpdateData] = useState({
    region: '',
    lon: '',
    lat: '',
  });

  const [showUpdateForm, setShowUpdateForm] = useState(false);
  const [message, setMessage] = useState('');
  const token = localStorage.getItem('token');
  const storedIP = sessionStorage.getItem('ec2Ip');

  useEffect(() => {
    const userRole = localStorage.getItem('userRole');
    if (userRole !== 'admin') {
      navigate('/'); 
    }
  }, [navigate]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get(`http://${storedIP}/api/cdn/edgeserver_service/${instance_id}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        setData(response.data.edge_server);
        setMetrics(response.data.metrics);
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
  }, [instance_id, navigate]);



  const handleDeleteSite = async () => {
    const confirmDelete = window.confirm("Ești sigur că vrei să ștergi acest server?");
    if (confirmDelete) {
      try {
        const token = localStorage.getItem('token');
        await axios.delete(`http://${storedIP}/api/cdn/edgeserver_service/${instance_id}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        navigate('/admin/edgeservers');
      } catch (error) {
        if (error.response && error.response.status === 401) {
          navigate('/logout');
        } else {
          setError(error.message);
        }
      }
    }
  };

  const handleUpdateFormToggle = () => {
    setShowUpdateForm(!showUpdateForm);
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!Data) {
    return <div>No data available</div>;
  }
  
  const handleChange = (e) => {
    setUpdateData({ ...updateData, [e.target.name]: e.target.value });
  };

const handleSubmit = async (e) => {
  e.preventDefault();
  setMessage('');
  setError('');

  const sensitiveCharsRegex = /[<>&#]/;
  if (sensitiveCharsRegex.test(updateData.region) || sensitiveCharsRegex.test(updateData.lat.toString()) || sensitiveCharsRegex.test(updateData.lon.toString())) {
    setError("Datele nu pot conține caractere sensibile (<, >, & sau #).");
    return;
  }

  try {
    const response = await axios.put(`http://${storedIP}/api/cdn/edgeserver_service/${instance_id}`, updateData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    setMessage(response.data.message);
    setData({ ...Data, ...updateData });  
  } catch (err) {
    if (err.response && err.response.status === 401) {
      navigate('/logout');
    } else {
      setError(err.response ? err.response.data.message : "A apărut o eroare la server.");
    }
  }
};

const UpdateForm = () => (
  <div className="update-form">
    <button onClick={handleUpdateFormToggle}>Close Form</button>
    <form onSubmit={handleSubmit}>
      <label>
        Region:
        <select name="region" value={updateData.region} onChange={handleChange}>
          <option value="us-east-2">Ohio</option>
          <option value="eu-central-1">Frankfurt</option>
          <option value="eu-west-2">London</option>
          <option value="ap-northeast-2">Seoul</option>
          <option value="sa-east-1">Sao Paulo</option>
        </select>
      </label>
      <label>
        Longitudine:
        <input type="number" name="lon" placeholder='Longitudine' value={updateData.lon} onChange={handleChange} step="0.0000001" />
      </label>
      <label>
        Latitudine:
        <input type="number" name="lat" placeholder='Latitudine' value={updateData.lat} onChange={handleChange} step="0.00000001" />
      </label>
      <div className="message" style={{ color: 'red', fontSize: '1.5rem', margin: '1rem 0' }}>{error}</div>
      <div className="message" style={{ color: 'green', fontSize: '1.5rem', margin: '1rem 0' }}>{message}</div>
      <button type="submit">Update EdgeServer</button>
    </form>
  </div>
);
return (
    <div>
      <div className="container-origin">
        <div className="content">
          <div className="header">
            <h1>Detalii EdgeServer</h1>
          </div>
          <div className="details">
            <div className="detail-item">
              <span className="label">Domeniu:</span>
              <span className="value">{Data.instance_id}</span>
            </div>
            <div className="detail-item">
              <span className="label">Regiune:</span>
              <span className="value">{Data.region}</span>
            </div>
            <div className="detail-item">
              <span className="label">Longitudine:</span>
              <span className="value">{Data.lon}</span>
            </div>
            <div className="detail-item">
              <span className="label">Latitudine:</span>
              <span className="value">{Data.lat}</span>
            </div>
            <div className="detail-item">
              <span className="label">Status:</span>
              <span className="value">{Data.status}</span>
            </div>
            {Metrics && Metrics.length > 0 && (
            <div>
              <h3>Instance Details</h3>
              <p><strong>Instance State:</strong> {Metrics[0].InstanceState}</p>
              <p><strong>Instance Name:</strong> {Metrics[0].InstanceName}</p>
              <p><strong>Instance Type:</strong> {Metrics[0].InstanceType}</p>
              <p><strong>Public IP:</strong> {Metrics[0].PublicIP}</p>
              <p><strong>Private IP:</strong> {Metrics[0].PrivateIP}</p>
              </div>
            )}
          </div>
          
          <div className="buttons">
            <button className="button delete-site" onClick={handleDeleteSite}>Delete EdgeServer</button>
            <button className="button update-site" onClick={() => setShowUpdateForm(true)}>Update EdgeServer</button>
          </div>
        </div>
        
        {showUpdateForm && <UpdateForm />}
      </div>
      {Metrics && Metrics.length > 0 && (
        <div className="metrics-container">
          {Metrics.map((metric, index) => (
            <div key={index} className="metric-detail">
              <h3>{metric.Metric}</h3>
              <p><strong>Average:</strong> {metric.Average} {metric.Unit}</p>
              <p><strong>Timestamp:</strong> {metric.Timestamp}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


export default IndividualEdgeServer;
